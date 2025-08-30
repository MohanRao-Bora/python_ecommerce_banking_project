import random
from datetime import datetime, timedelta
from db import get_connection
from cart import get_cart_id
from banking_main import verify_banking_login
from beneficiary import get_merchant_account_id, process_payment_transfer
from invoice import create_invoice
from shipments import check_and_update_shipment_status

def _handle_payment_process(total_amount):
    """
    An internal helper function to handle the entire payment flow.
    It returns payment details on success, or None on failure.
    """
    print("\nChoose Payment Method:")
    print("1. Cash on Delivery")
    print("2. Pay Now")
    payment_choice = input("Enter your choice (1/2): ").strip()

    if payment_choice == "1":
        return "Cash on Delivery", "Pending", "Confirmed"
    
    elif payment_choice == "2":
        print("\n--- Banking Authentication ---")
        try:
            banking_cust_id = int(input("Enter your Banking Customer ID: ").strip())
            banking_password = input("Enter your Banking Password: ").strip()
        except ValueError:
            print("Invalid Customer ID format. Order cancelled.")
            return None

        verified_id = verify_banking_login(banking_cust_id, banking_password)
        if not verified_id:
            print("Authentication Failed. Order cancelled.")
            return None

        merchant_account_id = get_merchant_account_id()
        if not merchant_account_id:
            print("Merchant account not found. Cannot process payment. Order cancelled.")
            return None

        print("Processing payment...")
        payment_successful = process_payment_transfer(verified_id, merchant_account_id, total_amount)
        
        if not payment_successful:
            print("Payment Failed (e.g., insufficient funds). Order cancelled.")
            return None
        
        print("Payment Successful!")
        return "Online Payment", "Paid", "Confirmed"
    
    else:
        print("Invalid payment choice. Order canceled.")
        return None


def choose_shipping_address(cursor, customer_id):
    """Displays available shipping addresses and handles user selection or creation of a new one."""
    cursor.execute("SELECT address_id, street, city, state, pincode FROM addresses WHERE customer_id = %s AND type = 'Shipping'", (customer_id,))
    addresses = cursor.fetchall()
    
    if not addresses:
        print("\nNo shipping addresses found. You must add one to continue.")
    else:
        print("\nAvailable Shipping Addresses:")
        for addr in addresses:
            print(f"{addr[0]}. {addr[1]}, {addr[2]}, {addr[3]} - {addr[4]}")
    
    print("0. Add New Address")
    selected_address_id_str = input("Enter shipping address ID (or 0 to add new): ").strip()

    if selected_address_id_str == "0":
        print("\nEnter new shipping address details:")
        street = input("Enter Street: ").strip()
        city = input("Enter City: ").strip()
        state = input("Enter State: ").strip()
        pincode = input("Enter Pincode: ").strip()
        cursor.execute("INSERT INTO addresses (customer_id, type, street, city, state, pincode) VALUES (%s, 'Shipping', %s, %s, %s, %s) RETURNING address_id",
                       (customer_id, street, city, state, pincode))
        new_address_id = cursor.fetchone()[0]
        print("New address added successfully.")
        return new_address_id
    else:
        try:
            selected_id = int(selected_address_id_str)
            if selected_id not in [a[0] for a in addresses]:
                return None
            return selected_id
        except ValueError:
            return None


def place_selected_items_order(customer_id):
    """Creates an order from cart items, including payment, shipment, and invoice records."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT p.product_id, p.name, ci.quantity, p.price, p.stock FROM cart_items ci JOIN products p ON ci.product_id = p.product_id JOIN carts c ON ci.cart_id = c.cart_id WHERE c.customer_id = %s", (customer_id,))
        items = cursor.fetchall()
        if not items:
            print("Your cart is empty."); return

        print("\nCart Items:")
        for item in items:
            print(f"Product ID: {item[0]}, Name: {item[1]}, Qty: {item[2]}, Price: ₹{item[3]:.2f}")

        selected_ids_str = input("Enter Product IDs to order (comma-separated): ").strip()
        selected_ids = [int(pid.strip()) for pid in selected_ids_str.split(",")]
        total = 0
        order_items = []
        for pid in selected_ids:
            match = next((it for it in items if it[0] == pid), None)
            if match:
                product_id, name, qty, price, stock = match
                if qty > stock: print(f"Not enough stock for Product ID {pid}. Skipping."); continue
                total += qty * price
                order_items.append((product_id, qty, price))
        
        if not order_items: print("No valid products selected for order."); return
        
        if not choose_shipping_address(cursor, customer_id):
            print("Address selection failed. Order cancelled."); return

        payment_result = _handle_payment_process(total)
        if not payment_result: return
        payment_method, payment_status, order_status = payment_result

        # --- DATABASE TRANSACTION BLOCK: All actions succeed or none do ---
        # 1. Create the Order
        cursor.execute("INSERT INTO orders (customer_id, status, total_amount) VALUES (%s, %s, %s) RETURNING order_id", (customer_id, order_status, total))
        order_id = cursor.fetchone()[0]

        # 2. Create the initial Shipment record with all details
        tracking_number = f"YM{random.randint(100000000, 999999999)}"
        delivery_date = datetime.now() + timedelta(days=3)
        shipment_date = datetime.now()
        courier_partner = "Your-Mart Express"
        cursor.execute("""
            INSERT INTO shipments (order_id, shipment_date, delivery_date, courier_partner, tracking_number, status)
            VALUES (%s, %s, %s, %s, %s, 'Processing')
        """, (order_id, shipment_date, delivery_date, courier_partner, tracking_number))

        # 3. Create the Payment record
        cursor.execute("INSERT INTO payments (order_id, payment_method, payment_status, amount) VALUES (%s, %s, %s, %s) RETURNING payment_id",
                       (order_id, payment_method, payment_status, total))
        payment_id = cursor.fetchone()[0]

        # 4. Create Order Items, update stock, and clear cart
        cart_id = get_cart_id(customer_id)
        for pid, qty, price in order_items:
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)", (order_id, pid, qty, price))
            cursor.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (qty, pid))
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s AND product_id = %s", (cart_id, pid))
        
        # 5. Create the Invoice
        create_invoice(cursor, order_id, payment_id, total)
        
        conn.commit()
        print(f"\nOrder #{order_id} placed successfully. Total: ₹{total:.2f}")

    except Exception as e:
        print(f"Error placing order: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


def place_direct_order(customer_id, product_id, quantity):
    """Creates a direct order, including payment, shipment, and invoice records."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT price, stock FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product: print("Product not found."); return

        price, stock = product
        if quantity > stock: print("Not enough stock available."); return

        total = price * quantity
        if not choose_shipping_address(cursor, customer_id):
            print("Address selection failed. Order cancelled."); return

        payment_result = _handle_payment_process(total)
        if not payment_result: return
        payment_method, payment_status, order_status = payment_result

        # --- DATABASE TRANSACTION BLOCK ---
        # 1. Create the Order
        cursor.execute("INSERT INTO orders (customer_id, status, total_amount) VALUES (%s, %s, %s) RETURNING order_id", (customer_id, order_status, total))
        order_id = cursor.fetchone()[0]

        # 2. Create the initial Shipment record with all details
        tracking_number = f"YM{random.randint(100000000, 999999999)}"
        delivery_date = datetime.now() + timedelta(days=3)
        shipment_date = datetime.now()
        courier_partner = "Your-Mart Express"
        cursor.execute("""
            INSERT INTO shipments (order_id, shipment_date, delivery_date, courier_partner, tracking_number, status)
            VALUES (%s, %s, %s, %s, %s, 'Processing')
        """, (order_id, shipment_date, delivery_date, courier_partner, tracking_number))
        
        # 3. Create the Payment record
        cursor.execute("INSERT INTO payments (order_id, payment_method, payment_status, amount) VALUES (%s, %s, %s, %s) RETURNING payment_id",
                       (order_id, payment_method, payment_status, total))
        payment_id = cursor.fetchone()[0]
        
        # 4. Create Order Item and update stock
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)", (order_id, product_id, quantity, price))
        cursor.execute("UPDATE products SET stock = stock - %s WHERE product_id = %s", (quantity, product_id))
        
        # 5. Create the Invoice
        create_invoice(cursor, order_id, payment_id, total)

        conn.commit()
        print(f"\nOrder #{order_id} placed successfully. Total: ₹{total:.2f}")

    except Exception as e:
        print(f"Error placing direct order: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


def view_orders(customer_id):
    """Displays the order history for a given customer, including payment and shipment status."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query now joins orders, payments, and shipments for a complete overview
        cursor.execute("""
            SELECT o.order_id, o.order_date, o.status, p.payment_status, s.status AS shipment_status
            FROM orders o
            LEFT JOIN payments p ON o.order_id = p.order_id
            LEFT JOIN shipments s ON o.order_id = s.order_id
            WHERE o.customer_id = %s
            ORDER BY o.order_date DESC
        """, (customer_id,))
        orders = cursor.fetchall()

        if not orders:
            print("\nNo orders found.")
            return

        print("\n--- Your Orders ---")
        for order in orders:
            order_id, date, order_status, payment, shipment = order
            print(f"Order ID: {order_id} | Date: {date.strftime('%Y-%m-%d')} | Payment: {payment or 'N/A'} | Shipment: {shipment or 'N/A'}")
            
            cursor.execute("SELECT p.name, oi.quantity, oi.price FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id = %s", (order_id,))
            items = cursor.fetchall()
            for item in items:
                print(f"  - {item[0]} (Qty: {item[1]} @ ₹{item[2]:.2f})")
            print("-" * 40)

    except Exception as e:
        print(f"Error viewing orders: {e}")
    finally:
        if conn:
            conn.close()