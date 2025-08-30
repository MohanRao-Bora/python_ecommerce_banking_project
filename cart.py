from db import get_connection

def get_cart_id(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT cart_id FROM carts WHERE customer_id = %s", (customer_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()

def add_to_cart(customer_id, product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cart_id = get_cart_id(customer_id)
        if not cart_id:
            print("Cart not found for customer.")
            return

        cursor.execute("""
            INSERT INTO cart_items (cart_id, customer_id, product_id, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (customer_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity
        """, (cart_id, customer_id, product_id, quantity))
        conn.commit()
        print("Product added to cart.")
    except Exception as e:
        print("Error adding to cart:", e)
    finally:
        cursor.close()
        conn.close()


def view_cart(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.product_id, p.name, c.quantity, p.price, (c.quantity * p.price) AS total_price
            FROM cart_items c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = %s
        """, (customer_id,))
        items = cursor.fetchall()
        return items
    except Exception as e:
        print("Error viewing cart:", e)
        return []
    finally:
        cursor.close()
        conn.close()

def update_cart_quantity(customer_id, product_id, new_quantity):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE cart_items
            SET quantity = %s
            WHERE customer_id = %s AND product_id = %s
        """, (new_quantity, customer_id, product_id))
        if cursor.rowcount == 0:
            print("No such product in cart.")
        else:
            conn.commit()
            print("Cart quantity updated.")
    except Exception as e:
        print("Error updating cart:", e)
    finally:
        cursor.close()
        conn.close()

def remove_from_cart(customer_id, product_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM cart_items
            WHERE customer_id = %s AND product_id = %s
        """, (customer_id, product_id))
        if cursor.rowcount == 0:
            print("Product not found in cart.")
        else:
            conn.commit()
            print("Product removed from cart.")
    except Exception as e:
        print("Error removing from cart:", e)
    finally:
        cursor.close()
        conn.close()

def clear_cart(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cart_items WHERE customer_id = %s", (customer_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
