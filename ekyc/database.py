from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import os

load_dotenv()

def create_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            database=os.getenv("MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
        )
        if connection.is_connected():
            print('\033[36m' + 'Connect database success' + '\033[0m')
            return connection
    except Error as e:
        print('\033[91m'+'Error while connecting to MySQL: ' + '\033[92m', e)
        return None
