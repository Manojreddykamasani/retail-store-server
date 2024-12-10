import pymysql
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Function to connect to the database
def connect_db():
    return pymysql.connect(
        host=os.getenv('host'),  # Aiven MySQL host
        user=os.getenv('user'),  # Aiven MySQL user
        password=os.getenv('AIVEN_PASSWORD'),  # Aiven MySQL password
        database=os.getenv('database'),  # Aiven MySQL database name
        port=15536,  # MySQL port
        cursorclass=pymysql.cursors.DictCursor
    )

# Function to truncate the table
def truncate_table():
    conn = None
    cursor = None

    try:
        # Connect to the database
        conn = connect_db()
        cursor = conn.cursor()

        # Truncate the table
        truncate_query = "TRUNCATE TABLE products;"
        cursor.execute(truncate_query)

        conn.commit()
        print("Table truncated successfully.")
    except Exception as e:
        print("Error truncating table:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Call the function to truncate the table
truncate_table()

