
import mysql.connector
from mysql.connector.cursor import MySQLCursor
import pprint
import cbpro
import time

def market_price():
    public_client = cbpro.PublicClient()
    btc_price = public_client.get_product_24hr_stats('BTC-USD')['last']
    eth_price = public_client.get_product_24hr_stats('ETH-USD')['last']
    ltc_price = public_client.get_product_24hr_stats('LTC-USD')['last']
    
    cursor = MySQLCursor(db)

    sql_r = """INSERT INTO trading.historical_rate(historical_rate,currency_id) 
             VALUES (%s,%s) 
        """
    sql_p = """update trading.currency set last_price = %s where currency_id = %s  """  
    
    sql_ugl = """ update portfolio set un
                """
    data = [(btc_price,1),
            (eth_price,2),
            (ltc_price,3)]
    
    cursor.executemany(sql_p,data)
    
    cursor.executemany(sql_r,data)

    
    db.commit()

    cursor.close()



db=mysql.connector.connect(user='root',
password='liuyu123',
host = 'localhost',
database='trading',
auth_plugin='mysql_native_password',
use_pure = True)




start_time = time.time()
p = 0
while p <= 10:
    market_price()
    time.sleep(10.0 - ((time.time() - start_time) % 10.0))
    p = p+1
    


db.close() 
