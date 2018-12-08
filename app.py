from flask import Flask 
from flask import request
from flask import render_template
import mysql.connector as mc
from mysql.connector.conversion import MySQLConverter
from mysql.connector.cursor import MySQLCursor
import cbpro
import time

app = Flask(__name__)


##Golbal Variable 
user_id = None

##Flask Setting

#main page
@app.route('/')
def trading_main():
    return render_template('login.html')

#signup page
@app.route('/sign')
def signup_main():    
    return render_template('signup.html')

#Go to transacion page
@app.route('/transaction')
def transaction_main():
    market_price()    
    item = get_currencies()
    account = get_account()
    return render_template('transaction.html',item = item,accounts=account)

#Go to account page
@app.route('/account')
def account():
    market_price()
    accounts = get_account()
    history = get_history()
    portfolio = get_portfolio()
    unrealizedGL = get_UnrealziedGL()
    bp = round(get_buying_power(),2)
    gl = get_gl()
    rgl = round(get_realgl(),2)
    maxgl = get_maxgl()*4
    startgl = get_maxgl()*-2
    values = []
    labels = []
    for i,v in gl:
        if i == None:
            values.append(0)
            labels.append(v)
        else:
            values.append(round(i,2))
            labels.append(v)
    return render_template('account.html',accounts = accounts,portfolio = portfolio,
                            GL = unrealizedGL,rgl= rgl,bp = bp,values = values,labels=labels,
                            maxgl = maxgl, startgl = startgl,history = history)

#GO to overview page
@app.route('/overview')
def overview():
    market_price()
    portfolio = get_portfolio()
    unrealizedGL = get_UnrealziedGL()
    values = get_value()
    price = get_price()
    euqity = []
    symbol = []
    for i,v in values:
        symbol.append(i)
        euqity.append(round(v,2))    
    colors = ["#FDB45C","#5060FF", "#9EA8A8"]
    return render_template('overview.html',portfolio = portfolio,GL = unrealizedGL, price = price,set = zip(euqity,symbol,colors))

#Login process
@app.route('/login',methods = ['POST'])
def login_process():
    
    market_price()
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

    if check == 0:
        response = "Username or Password is incorrect!"
        return render_template('s_result.html',response = response)

    else:
        user_info = get_user_info()
        
        global user_id
        user_id = user_info[username]

        portfolio = get_portfolio()
        unrealizedGL = get_UnrealziedGL()
        price = get_price()
        values = get_value()
        euqity = []
        symbol = []
        for i,v in values:
            symbol.append(i)
            euqity.append(round(v,2))
        colors = ["#FDB45C","#5060FF", "#9EA8A8"]

        return render_template('overview.html',portfolio = portfolio,GL = unrealizedGL,price = price,set = zip(euqity,symbol,colors))


# Signup process
@app.route('/signup',methods = ['POST'])
def signup_process():
    market_price()
    email = request.form['email']
    username = request.form['username']
    password = request.form['password']

    connection = get_connection()
    cursor = connection.cursor(buffered=True)
    insert = """ insert into user_info(username, password,email,balance)
            values (%s,%s,%s,100000) 
            """
    data = (username,password,email)
    cursor.execute(insert,data)
    connection.commit()
    cursor.close()
    connection.close()
    
    response = "Sign up successfully"
    return render_template('signup_result.html',response = response)


# Transaction [rocess
@app.route('/process',methods = ['POST'])
def process_order():
    market_price()
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
    sql_avgcost = """select avg_cost from portfolio where user_id = %s and currency_id = %s
                    """
    sql_check = """select count(*) from portfolio where user_id = %s and currency_id = %s
                 """
    sql_insert = """ insert into portfolio (user_id,currency_id,quantity,avg_cost)
                    values (%s,%s,%s,%s)
                  """  
    sql_process = """insert into general_ledger(user_id,currency_id,type_id,trade_price,quantity,amount,gl)
               values(%s,%s,%s,%s,%s,%s,%s)    """  

    sql_new_avg = """ select IFNULL(sum(amount)/sum(quantity),0) from general_ledger
                    where user_id = %s and currency_id = %s
                    """
    sql_update = """ update portfolio set quantity = quantity + %s,avg_cost = %s
                    where user_id = %s and currency_id = %s
                  """                
    sql_bp = """ select IFNULL(balance,0) from user_info where user_id = %s
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
        
        
        #Get inventory amount 
        cursor.execute(sql_inventory,data_amount)
        inventory_amount = float(cursor.fetchone()[0])
        #Check if user has sufficient inventory
        if inventory_amount >= quantity:
            
            #get user's avg_cost
            cursor.execute(sql_avgcost,(user_id,currency))
            avg_cost = cursor.fetchone()[0]
                
            #Calculate transaction amount
            amount = -1*quantity*trade_price
            gl = (trade_price-avg_cost)*quantity
            quantity=-1*quantity
            
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
    return render_template('t_result.html',response = response)


###################################################### Function  ######################################################

# Database Connection    
def get_connection():
    return mc.connect(
    user='root',
    password='liuyu123',
    host = 'localhost',
    database='trading',
    auth_plugin='mysql_native_password'
    )


# Get Currect Portofilo value of user

def get_portfolio():
    connection = get_connection()
    cursor = connection.cursor()
    
    sql_portfolio = """select IFNULL(sum(quantity * avg_cost),0) from portfolio
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

# Get Currect Portofilo value of user
def get_UnrealziedGL():
    connection = get_connection()
    cursor = connection.cursor()

    sql_gl = """select IFNULL(sum(unrealized_gl),0)
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


# Get user's username, user_id 

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



# Get currency list 
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

# Get Currency Pirce
def get_price():
    connection = get_connection()
    result = connection.cmd_query("select * from currency")
    (currencies, eof) = connection.get_rows()
    converter = MySQLConverter(connection.charset, True)
    connection.close()
    values = []
    for currency in currencies:
        values.append(converter.row_to_python(currency,result["columns"])[1:3])
    return values


# Get account info
def get_account():
    connection = get_connection()
    sql_accout = """ select currency.currency_name, IFNULL(portfolio.quantity,0), IFNULL(round(currency.last_price,2),0), IFNULL(round(portfolio.avg_cost,2),0),IFNULL(round(portfolio.unrealized_gl,2),0), IFNULL(round((portfolio.avg_cost * portfolio.quantity),2),0)
                    from portfolio
                    join currency
                    on portfolio.currency_id = currency.currency_id
                    where user_id = %s
                   """ 
    cursor = connection.cursor(buffered=True)
    cursor.execute(sql_accout,(user_id,))
    values = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return values

# Get buying power
def get_buying_power():
    connection = get_connection()
    sql_buying = """ select IFNULL(balance,0) from user_info
                    where user_id = %s
                    """
    cursor = connection.cursor(buffered=True)
    cursor.execute(sql_buying,(user_id,))
    values = cursor.fetchone()[0]

    cursor.close()
    connection.close()
    return values

# get portfolio value
def get_value():
    connection = get_connection()
    sql_rate = """select currency.currency_name, IFNULL((portfolio.avg_cost * portfolio.quantity),0) from portfolio 
                join currency
                on portfolio.currency_id = currency.currency_id
                where user_id = %s 
                """
    cursor = connection.cursor()
    cursor.execute(sql_rate,(user_id,))
    values = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return values

# get historical gain and loss
def get_gl():
    connection = get_connection()
    sql_hgl = """select IFNULL(sum(gl),0), date(trade_date) from general_ledger
            where user_id = %s
            group by date(trade_date)
            """
    cursor = connection.cursor()
    cursor.execute(sql_hgl,(user_id,))
    values = cursor.fetchall()
    cursor.close()
    connection.close()
    return values

# Get total realized gain and loss
def get_realgl():
    connection = get_connection()
    sql_rgl = """select IFNULL(round(sum(gl),2),0) from general_ledger
                where user_id =%s
            """
    cursor = connection.cursor()
    cursor.execute(sql_rgl,(user_id,))
    values = cursor.fetchone()[0]
    
    cursor.close()
    connection.close()
    
    return values   

# Get maximum realized gain and loss group by date
def get_maxgl():
    connection = get_connection()
    sql_mgl = """select IFNULL(max(m.mv),0) from
                    (select abs(sum(gl)) as mv from general_ledger
                    where user_id = %s
                    group by date(trade_date)) as m
                """
    cursor = connection.cursor()
    cursor.execute(sql_mgl,(user_id,))
    values = round(cursor.fetchone()[0],-3)

    cursor.close()
    connection.close()

    return values
# Get Transaction History
def get_history():
    connection = get_connection()
    sql_history = """select currency.currency_name, 
                            transaction_type.transaction_type,
                            general_ledger.trade_price,
                            general_ledger.quantity, 
                            round(general_ledger.amount,2),
                            IFNULL(general_ledger.gl,0),
                            date(general_ledger.trade_date)
                    from general_ledger
                    join currency
                    on general_ledger.currency_id = currency.currency_id
                    join transaction_type
                    on general_ledger.type_id = transaction_type.type_id
                    where user_id = %s
                    order by date(general_ledger.trade_date) desc                    
                    """
    cursor = connection.cursor()
    cursor.execute(sql_history,(user_id,))
    values = cursor.fetchall()

    cursor.close()
    connection.close()

    return values
# Get Market Price and Update Unrealized gain and loss
def market_price():
    connection = get_connection()

    public_client = cbpro.PublicClient()
    btc_price = public_client.get_product_24hr_stats('BTC-USD')['last']
    eth_price = public_client.get_product_24hr_stats('ETH-USD')['last']
    ltc_price = public_client.get_product_24hr_stats('LTC-USD')['last']
    
    cursor = MySQLCursor(connection)

    sql_r = """INSERT INTO trading.historical_rate(historical_rate,currency_id) 
             VALUES (%s,%s) 
        """
    sql_p = """update trading.currency set last_price = %s where currency_id = %s  """  
    
    sql_ugl = """ update portfolio
                    join currency on portfolio.currency_id = currency.currency_id
                    set portfolio.unrealized_gl = (currency.last_price - portfolio.avg_cost )*portfolio.quantity
                """
    data = [(btc_price,1),
            (eth_price,2),
            (ltc_price,3)]
    
    cursor.executemany(sql_p,data)
    cursor.executemany(sql_r,data)
    cursor.execute(sql_ugl)
    
    
    connection.commit()

    cursor.close()
    connection.close()

