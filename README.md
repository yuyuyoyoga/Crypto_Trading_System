# Web_System

## Instruction: 
1) Create a new schema in MySQL database
2) Use the sql file to generate the table in database
3) Open the app.py and go to line 300
4) Change the connection paramater to your own user and password
```python
  def get_connection():
      return mc.connect(
      user='YOUR_USER_NAME',
      password='YOUR_PASSWORD',
      host = 'YOUR_HOST',
      database='YOUR_DATABASE_NAME',
      auth_plugin='mysql_native_password'
      )
```
5) In the terminal type command: FLASK_APP=app.py flask run
6) Copy the url:http://127.0.0.1:5000/ and open it with a browser 

## Description:

This is a cryptocurrency trading system that will allow a user to buy and sell cryptocurrencies and tract trrading pfofitability and loss

#Technologies to use:
- Python 3
- Flask
- Bootstrap 4 / HTML / CSS
- Database: MySQL
- JavaScript

#Required aspects
- Order management screen allowing the user to buy and sell cryptocurrencies: Bitcoin, ethereum and litecoin are sufficient
- Tracking and view real-time profit and loss including realized, Unrealized PL and volume-weighted average price
- View a history of trades made


