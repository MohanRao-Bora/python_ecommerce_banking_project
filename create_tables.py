from db import get_connection

def create_all_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15),
            Password TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            seller_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            gstin VARCHAR(20) UNIQUE,
            phone_number TEXT,
            contact_mail TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id SERIAL PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price NUMERIC(10,2) NOT NULL,
            stock INT NOT NULL,
            category_id INT REFERENCES categories(category_id),
            seller_id INT REFERENCES sellers(seller_id),
            warranty_months INT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES customers(customer_id),
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Pending'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(order_id),
            product_id INT REFERENCES products(product_id),
            quantity INT NOT NULL,
            price NUMERIC(10,2) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id SERIAL PRIMARY KEY,
            order_id INT UNIQUE REFERENCES orders(order_id),
            payment_method VARCHAR(50),
            payment_status VARCHAR(50),
            amount NUMERIC(10,2) NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(order_id),
            shipment_date DATE,
            delivery_date DATE,
            courier_partner VARCHAR(100),
            tracking_number VARCHAR(100),
            status VARCHAR(50)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES customers(customer_id),
            product_id INT REFERENCES products(product_id),
            rating INT CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            cart_id SERIAL PRIMARY KEY,
            customer_id INT UNIQUE REFERENCES customers(customer_id),
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_item_id SERIAL PRIMARY KEY,
            cart_id INT REFERENCES carts(cart_id),
            product_id INT REFERENCES products(product_id),
            quantity INT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            address_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES customers(customer_id),
            type VARCHAR(20) CHECK (type IN ('Billing', 'Shipping')),
            street TEXT,
            city VARCHAR(100),
            state VARCHAR(100),
            pincode VARCHAR(10)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice (
            invoice_id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(order_id),
            payment_id INT REFERENCES payments(payment_id),
            amount NUMERIC(10,2) NOT NULL,
            warranty_date TIMESTAMP
        );
    """)
    

    conn.commit()
    cursor.close()
    conn.close()
    print("All tables created successfully.")

if __name__ == "__main__":
    create_all_tables()
