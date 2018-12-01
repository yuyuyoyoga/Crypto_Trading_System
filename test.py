
from flask import Flask 
from flask import request
from flask import render_template
import mysql.connector as mc
from mysql.connector.conversion import MySQLConverter
from mysql.connector.cursor import MySQLCursor


app = Flask(__name__)
user_id = None
@app.route('/')
def trading_main():
    return render_template('login.html')

@app.route('/signup.html')
def signup_main():    
    return render_template('signup.html')

@app.route('/transaction.html')
def transaction_main():    
    item = get_currencies()
    return render_template('transaction.html',item = item)


   
def get_connection():
    return mc.connect(
    user='root',
    password='liuyu123',
    host = 'localhost',
    database='trading',
    auth_plugin='mysql_native_password',
    charset = 'utf8mb4',
    collation = 'utf8mb4_unicode_ci',
    use_unicode = True
    )



@app.route('/login',methods = ['POST'])
def login_process():
    username = request.form['username']
    password = request.form['password']

    connection = get_connection()
    cursor = connection.cursor()

    sql = """select count(*) from user_info
                where username = %s and password = %s
            """
    data = (username,password)

    cursor.execute(sql,data)
    check = cursor.fetchone()[0]
    cursor.close()
    connection.close()
    response = "Username or Password is incorrect!"
    user_info = get_user_info()
    global user_id
    user_id = user_info[username]

    portfolio = get_portfolio()
    unrealizedGL = get_UnrealziedGL()


    return render_template('portfolio.html',portfolio = portfolio,GL = unrealizedGL) if check == 1 else response

@app.route('/signup',methods = ['POST'])
def signup_process():
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    connection = get_connection()
    cursor = MySQLCursor(connection)
    insert = """ insert into user_info(username, password,email)
            values (%s,%s,%s) 
            """
    data = (username,password,email)
    cursor.execute(insert,data)
    connection.commit()
    cursor.close()
    connection.close()
    
    response = "Sign up successful"
    return response

def get_portfolio():
    connection = get_connection()
    cursor = connection.cursor()
    
    sql_portfolio = """select sum(quantity * avg_cost) from portfolio
                    where user_id = %s 
                    """

    cursor.execute(sql_portfolio,(user_id,))
    cv=cursor.fetchone()[0]
    if cv == None:
        pass
    else:
        cv = round(cv,2)    
    cursor.close()
    connection.close()
    return cv

def get_UnrealziedGL():
    connection = get_connection()
    cursor = connection.cursor()

    sql_gl = """select sum(currency.last_price - portfolio.avg_cost)
                from portfolio
                join currency
                on portfolio.currency_id = currency.currency_id
                where user_id = %s
            """
    cursor.execute(sql_gl,(user_id,))
    gl = cursor.fetchone()[0]

    if gl == None:
        pass
    else:
        gl = round(gl,2)    
    cursor.close()
    connection.close()
    return gl

def get_user_info():
    connection = get_connection()
    result = connection.cmd_query("select username,user_id from user_info")
    (users, eof) = connection.get_rows()
    converter = MySQLConverter(connection.charset, True)
    user_info = []
    for user in users:
        user_info.append(converter.row_to_python(user,result["columns"]))
    user_info = dict(user_info)

    connection.close()
    return user_info


@app.route('/process',methods = ['POST'])
def process_order():
    
    ## Get data from website
    quantity = float(request.form['qty'])
    currency = int(request.form['itemOrder'])
    type_id = int(request.form['Type'])
    amount = None
    gl = None
    response = ""
    
    ## Set up connection
    connection = get_connection()
    cursor = connection.cursor(buffered=True)

    ## Set up sql
    sql_price = """ select last_price from currency where currency_id = %s
                    """
    sql_avgcost = """select avg_cost from portfolio where user_id = %s
                    """
    sql_check = """select count(*) from portfolio where user_id = %s and currency_id = %s
                 """
    sql_insert = """ insert into portfolio (user_id,currency_id,quantity,avg_cost)
                    values (%s,%s,%s,%s)
                  """  
    sql_process = """insert into general_ledger(user_id,currency_id,type_id,trade_price,quantity,amount,gl)
               values(%s,%s,%s,%s,%s,%s,%s)    """  

    sql_new_avg = """ select sum(amount)/sum(quantity) from general_ledger
                    where user_id = %s and currency_id = %s
                    """
    sql_update = """ update portfolio set quantity = quantity + %s,avg_cost = %s
                    where user_id = %s and currency_id = %s
                  """                
    sql_bp = """ select balance from user_info where user_id = %s
                """              
    sql_inventory = """ select quantity from portfolio where user_id = %s and currency_id = %s
                     """            
    sql_balance = """ update user_info set balance = balance - %s where user_id = %s
                    """
    ## Get current price of cryptocurrency
    
    cursor.execute(sql_price,(currency,))
    trade_price = cursor.fetchone()[0]


   

    ##Get user's buying power
    cursor.execute(sql_bp,(user_id,))
    buying_power = cursor.fetchone()[0]


    data_amount = (user_id,currency)



    data_check = (user_id,currency)
    cursor.execute(sql_check,data_check)
    currency_check = cursor.fetchone()[0]   

    data_new_avg = (user_id,currency)
    
    

    ## Buy
    if type_id == 1:
        amount = quantity*trade_price
        data_process = (user_id,currency,type_id,trade_price,quantity,amount,gl)
        data_balance= (amount,user_id)
        data_insert = (user_id, currency,quantity,trade_price)   
        #check if buying power is suffcient or not
        if buying_power >= amount:
        #check if user has this currency or not
            if currency_check == 0:
                #process transaction
                cursor.execute(sql_process,data_process)
                

                #update portfolio
                
                cursor.execute(sql_balance,data_balance)

                cursor.execute(sql_insert,data_insert)
                response = "Purchase completed!"
            
            else:
                #process transaction
                cursor.execute(sql_process,data_process)

                #Calculate new avg cost
                cursor.execute(sql_new_avg,data_new_avg)
                new_avg_cost = cursor.fetchone()[0]
                #update
                cursor.execute(sql_balance,data_balance) 
                
                data_update = (quantity,new_avg_cost,user_id,currency)
                cursor.execute(sql_update,data_update)
                response = "Purchase completed!"
        
        # insufficent amount
        else:
            
            #error message
            response = "Insufficient fund!"
    
    #if sell, calculate total amount, gain and loss
    elif type_id == 2:
        #get user's avg_cost
        cursor.execute(sql_avgcost,(user_id,))
        avg_cost = cursor.fetchone()[0]
        
        amount = -1*quantity*trade_price
        gl = (trade_price-avg_cost)*quantity
        quantity=-1*quantity
        
        #Get inventory amount 
        cursor.execute(sql_inventory,data_amount)
        inventory_amount = float(cursor.fetchone()[0])
        #Check if user has sufficient inventory
        if inventory_amount >= quantity:
            
            #process transaction
            data_process = (user_id,currency,type_id,trade_price,quantity,amount,gl)
            cursor.execute(sql_process,data_process)
            
            #calculate new avg cost
            cursor.execute(sql_new_avg,data_new_avg)
            new_avg_cost = cursor.fetchone()[0]
            
            #update 
            data_balance = (amount,user_id)
            cursor.execute(sql_balance,data_balance)
            data_update = (quantity,new_avg_cost,user_id,currency)
            cursor.execute(sql_update,data_update)
            
            response = "Sale Completed!"
        else:
            
            #error message
            response = "Insufficient Inventory!"   

    
    connection.commit()

    cursor.close()
    return response

def get_currencies():
    connection = get_connection()
    result = connection.cmd_query("select * from currency")
    (currencies, eof) = connection.get_rows()
    converter = MySQLConverter(connection.charset, True)
    connection.close()
    values = []
    for currency in currencies:
        values.append(converter.row_to_python(currency,result["columns"])[0:2])
    return values