import os
from flask import Flask, request, jsonify
import pymysql.cursors
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Database configuration
def connect_db():
    return pymysql.connect(
        host=os.getenv('host'),  # Your Aiven MySQL host
        user=os.getenv('user'),                                         # Your Aiven MySQL user
        password=os.getenv('AIVEN_PASSWORD'),                     # Your Aiven MySQL password
        database=os.getenv('database'),                                    # Your Aiven MySQL database name
        port=15536,                                              # Port for MySQL on Aiven
        cursorclass=pymysql.cursors.DictCursor
    )

# Get all products
@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        return jsonify(products)  # Return all products in JSON format
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Search product by name using JSON in body
@app.route('/api/products/search', methods=['POST'])
def search_product():
    try:
        data = request.get_json()  # Get JSON from the request body
        
        # Check if 'product_name' is provided in the request data
        if 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400

        product_name = data['product_name']  # Extract product name
        
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products WHERE product_name LIKE %s", (f'%{product_name}%',))
        products = cursor.fetchall()
        
        if products:
            return jsonify(products)  # Return the list of products found
        else:
            return jsonify({'message': 'No products found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Add a new product
@app.route('/api/products', methods=['POST'])
def add_product():
    try:
        data = request.get_json()  # Get JSON data from request body
        
        # Insert the new product into the database
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(""" 
            INSERT INTO products (product_name, section, brand_name, vendor_name, tax, image_link, rack)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data['product_name'], data['section'], data['brand_name'], data['vendor_name'],
              data['tax'], data['image_link'], data['rack']))
        connection.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Update a product by name using JSON in body
@app.route('/api/products/update', methods=['PUT'])
def update_product():
    try:
        data = request.get_json()  # Get JSON data from request body

        # Check if 'product_name' is provided in the request data
        if 'product_name' not in data:
            return jsonify({'error': 'Product name is required'}), 400
        
        product_name = data['product_name']  # Extract product name
        
        # Prepare the SQL SET clause based on the provided attributes
        update_fields = []
        update_values = []

        # Check which attributes are provided and prepare update fields dynamically
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

        # If no fields to update, return an error
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        # Add the product name at the end of the values
        update_values.append(product_name)

        # Build the SQL query
        update_query = f"""
            UPDATE products
            SET {', '.join(update_fields)}
            WHERE product_name = %s
        """

        # Execute the update query
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

# Run the Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use dynamic port provided by Render
    app.run(host="0.0.0.0", port=port)
