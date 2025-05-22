import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

def run_sql(query):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        return columns, rows
    except Exception as e:
        return None, str(e)
