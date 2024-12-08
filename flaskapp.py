import os
from flask import Flask, request, jsonify
import pymysql.cursors
from dotenv import load_dotenv
from fuzzywuzzy import process
from difflib import SequenceMatcher
from flask_mail import Mail, Message
load_dotenv()

app = Flask(__name__)

# Database configuration
def connect_db():
    return pymysql.connect(
        host=os.getenv('host'),  # Aiven MySQL host
        user=os.getenv('user'),  # Aiven MySQL user
        password=os.getenv('AIVEN_PASSWORD'),  # Aiven MySQL password
        database=os.getenv('database'),  # Aiven MySQL database name
        port=15536,  # MySQL port
        cursorclass=pymysql.cursors.DictCursor
    )
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587  # SMTP port for Gmail (with TLS)
app.config['MAIL_USE_TLS'] = True  # Enable TLS
app.config['MAIL_USE_SSL'] = False  # Disable SSL (use TLS instead)
app.config['MAIL_USERNAME'] = 'sender_mail@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'app specific password'  # Use the 16-character app password here
app.config['MAIL_DEFAULT_SENDER'] = 'sender_mail@gmail.com'  # Default sender (same as username)

mail = Mail(app)

@app.route('/notify_out_of_stock', methods=['POST'])
def notify_out_of_stock():
    # Receive item name from the API call
    item_name = request.json.get('item_name')
    
    if not item_name:
        return jsonify({'error': 'Item name is required'}), 400

    recipient_email = "mail_to_be_notified@example.com"  # Fixed recipient email address

    # Create the email content
    subject = f"{item_name} is Out of Stock"
    body = f"Dear Admin,\n\nWe regret to inform you that the item '{item_name}' is currently out of stock.\n\nPlease take necessary action."

    # Create the email message
    msg = Message(subject, recipients=[recipient_email], body=body)

    try:
        # Send the email
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully to the fixed recipient.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get all products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/products/search', methods=['POST'])
def search_product():
    connection = None
    try:
        data = request.get_json()  # Get JSON from the request body

        # Check if 'query' is provided in the request data
        if 'query' not in data:
            return jsonify({'error': 'Search query is required'}), 400

        query = data['query'].strip().lower()  # Convert query to lowercase and trim spaces
        connection = connect_db()
        cursor = connection.cursor()

        # Step 1: Exact match
        cursor.execute("SELECT * FROM products WHERE LOWER(product_name) = %s", (query,))
        exact_matches = cursor.fetchall()

        if exact_matches:
            return jsonify(exact_matches)  # Return exact matches if found

        # Step 2: Fuzzy match logic
        cursor.execute("SELECT * FROM products")
        all_products = cursor.fetchall()

        def fuzzy_match(query, product_name):
            """Returns a similarity score between 0 and 1."""
            return SequenceMatcher(None, query, product_name).ratio()

        partial_matches = []
        for product in all_products:
            product_name = product['product_name'].lower()
            similarity = fuzzy_match(query, product_name)

            # Include if similarity is above 40% threshold
            if similarity >= 0.4:
                partial_matches.append({"product": product, "similarity": similarity})

        # Step 3: Sort results by similarity score
        partial_matches.sort(key=lambda x: x['similarity'], reverse=True)

        # Prepare the final response
        response = [match["product"] for match in partial_matches]

        if response:
            return jsonify(response)
        else:
            return jsonify({'message': 'No products found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection:
            connection.close()
# Add a new product
@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(""" 
            INSERT INTO products (product_name, section, brand_name, vendor_name, tax, image_link, rack, mrp, speciality)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['product_name'], data['section'], data['brand_name'], data['vendor_name'],
            data['tax'], data['image_link'], data['rack'], data['mrp'], data['speciality']
        ))
        connection.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Update a product by name
@app.route('/api/products/update', methods=['PUT'])
def update_product():
    try:
        data = request.get_json()
        if 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product_name = data['product_name']
        update_fields = []
        update_values = []

        if 'brand_name' in data:
            update_fields.append("brand_name = %s")
            update_values.append(data['brand_name'])
        if 'vendor_name' in data:
            update_fields.append("vendor_name = %s")
            update_values.append(data['vendor_name'])
        if 'tax' in data:
            update_fields.append("tax = %s")
            update_values.append(data['tax'])
        if 'image_link' in data:
            update_fields.append("image_link = %s")
            update_values.append(data['image_link'])
        if 'rack' in data:
            update_fields.append("rack = %s")
            update_values.append(data['rack'])
        if 'mrp' in data:
            update_fields.append("mrp = %s")
            update_values.append(data['mrp'])
        if 'speciality' in data:
            update_fields.append("speciality = %s")
            update_values.append(data['speciality'])

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        update_values.append(product_name)
        update_query = f"""
            UPDATE products
            SET {', '.join(update_fields)}
            WHERE product_name = %s
        """
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(update_query, tuple(update_values))
        connection.commit()

        if cursor.rowcount > 0:
            return jsonify({'message': 'Product updated successfully'})
        else:
            return jsonify({'message': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
# Delete a product by name using JSON in body
@app.route('/api/products/delete', methods=['POST'])
def delete_product():
    try:
        data = request.get_json()  # Get JSON data from request body
        
        # Check if 'product_name' is provided in the request data
        if 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product_name = data['product_name']  # Extract product name
        
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products WHERE product_name = %s", (product_name,))
        connection.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'message': 'Product deleted successfully'})
        else:
            return jsonify({'message': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
