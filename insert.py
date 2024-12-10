import pymysql
import os
import csv
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

# Function to insert records from CSV into the database
def insert_from_csv(csv_file_path):
    conn = None
    cursor = None

    try:
        # Connect to the database
        conn = connect_db()
        cursor = conn.cursor()

        # Open the CSV file and insert records
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                insert_query = """
                INSERT INTO products (brand_name, id, image_link, mrp, product_name, rack, section, speciality, tax, vendor_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, row)

        conn.commit()
        print("Records inserted successfully.")
    except Exception as e:
        print("Error inserting records:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Specify your CSV file path and call the function
csv_file_path = "products.csv"
insert_from_csv(csv_file_path)
