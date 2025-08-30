from db import get_connection
import re


def validate_customer_inputs(name, email, phone):
    if not all(part.isalpha() for part in name.split()):
        raise ValueError("Enter a valid name (alphabets and spaces only).")

    if not (phone.isdigit() and len(phone) == 10):
        raise ValueError("Enter a valid 10-digit phone number.")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, email):
        raise ValueError("Enter a valid email address (e.g., user@example.com).")

# In customer.py

def add_customer(name, email, phone, password):
    """Creates a new customer and an associated cart, storing a plain-text password."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        validate_customer_inputs(name, email, phone)
        
        # Insert customer with plain-text password and get the new customer_id
        cursor.execute('''
            INSERT INTO customers (name, email, phone, password)
            VALUES (%s, %s, %s, %s)
            RETURNING customer_id
        ''', (name, email, phone, password))
        customer_id = cursor.fetchone()[0]

        # Create a cart for this new customer
        cursor.execute('INSERT INTO carts (customer_id) VALUES (%s)', (customer_id,))
        
        conn.commit()
        print("\nCustomer and cart created successfully.")
        
    except Exception as e:
        print(f"Error adding customer: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

def verify_password(customer_id, input_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM customers WHERE customer_id = %s", (customer_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row and row[0] == input_password

def verify_customer_login(email, input_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, password FROM customers WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row and row[1] == input_password else None

def update_customer(customer_id, new_name, new_email, new_phone):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, email, phone FROM customers WHERE customer_id = %s", (customer_id,))
        result = cursor.fetchone()
        if not result:
            print("Customer not found.")
            return

        current_name, current_email, current_phone = result

        updated_name = new_name.strip() if new_name.strip() else current_name
        updated_email = new_email.strip() if new_email.strip() else current_email
        updated_phone = new_phone.strip() if new_phone.strip() else current_phone

        cursor.execute("""
            UPDATE customers
            SET name = %s, email = %s, phone = %s
            WHERE customer_id = %s
        """, (updated_name, updated_email, updated_phone, customer_id))

        conn.commit()
        print("Customer updated successfully.")

    except Exception as e:
        print("Error updating customer:", e)
    finally:
        cursor.close()
        conn.close()

def delete_customer(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Step 1: Delete cart items
        cursor.execute("DELETE FROM cart_items WHERE customer_id = %s", (customer_id,))

        # Step 2: Delete cart
        cursor.execute("DELETE FROM carts WHERE customer_id = %s", (customer_id,))

        # Step 3: Delete customer
        cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))

        conn.commit()
        print("Customer deleted successfully.")
    except Exception as e:
        print("Error deleting customer:", e)
    finally:
        conn.close()


def get_customer_by_id(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return customer

def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY customer_id")
    customers = cursor.fetchall()
    conn.close()
    return customers
    
def send_old_password(email):
    """Send the old password to the user's email if found."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, password FROM customers WHERE email = %s", (email,))
    result = cur.fetchone()
    conn.close()

    if result:
        customer_id, old_password = result
        send_email(email, "Your Old Password", f"Your old password is: {old_password}")
        return customer_id, old_password
    else:
        print("Email not found.")
        return None, None


def reset_password(customer_id, old_password, new_password):
    """Reset the password ensuring it's not the same as the old one."""
    if new_password == old_password:
        print("New password cannot be the same as the old password.")
        return False

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE customers SET password = %s WHERE customer_id = %s", (new_password, customer_id))
    conn.commit()
    conn.close()
    print("Password updated successfully.")
    return True

