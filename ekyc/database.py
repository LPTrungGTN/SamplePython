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
            create_cards_table(connection)
            print('\033[36m' + 'Connect database success' + '\033[0m')
            return connection
    except Error as e:
        print('\033[91m'+'Error while connecting to MySQL: ' + '\033[92m', e)
        return None

def create_cards_table(connection):
    try:
        cursor = connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS cards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                profile_id INT NOT NULL,
                card_type VARCHAR(255) NOT NULL,
                front_image_url VARCHAR(255),
                back_image_url VARCHAR(255),
                upload_datetime DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """
        cursor.execute(create_table_query)
        connection.commit()
        print('\033[36m' + 'Table [cards] created successfully' + '\033[0m')
    except Error as e:
        print('\033[91m' + 'Failed to create table [cards]: ' + '\033[92m', e)
    finally:
        if (connection.is_connected()):
            cursor.close()
