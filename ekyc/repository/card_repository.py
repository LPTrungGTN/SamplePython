# repository/card_repository.py
import mysql.connector
from mysql.connector import Error

def insert_card_record(connection,profile_id, card_type, front_image_url):
    try:
        cursor = connection.cursor()
        insert_query = """
            INSERT INTO cards (profile_id, card_type, front_image_url)
            VALUES (%s, %s, %s);
        """
        record_tuple = (profile_id, card_type, front_image_url)
        cursor.execute(insert_query, record_tuple)
        connection.commit()
        print('\033[36m' + 'Record inserted successfully into cards table' + '\033[0m')
    except Error as e:
        print('\033[91m' + 'Error while inserting record into cards table: ' + '\033[92m', e)
    finally:
        if (connection.is_connected()):
            cursor.close()
