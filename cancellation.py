from db import get_connection
from beneficiary import process_refund_transfer
from banking_main import verify_banking_login

def cancel_order(order_id, customer_id):
    """Handles the logic for cancelling an order BEFORE it ships, including refunds."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT o.status, p.amount, p.payment_method
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_id = %s AND o.customer_id = %s
        """, (order_id, customer_id))
        
        order_data = cursor.fetchone()
        if not order_data:
            print("Order not found."); return
        
        status, amount, payment_method = order_data

        # Business Rule: Can only cancel if the order is not yet shipped or delivered.
        if status.lower() in ['shipped', 'out for delivery', 'delivered', 'returned']:
            print(f"Cannot cancel order: Current status is '{status}'."); return
        if status.lower() == 'cancelled':
            print("This order has already been cancelled."); return

        # If it was a paid order, process the refund.
        if payment_method == 'Online Payment':
            print("\nThis was a paid order. To process your refund, please authenticate.")
            try:
                banking_id = int(input("Enter your Banking Customer ID: ").strip())
                banking_password = input("Enter your Banking Password: ").strip()
            except ValueError:
                print("Invalid Banking ID format. Cancellation aborted."); return

            verified_id = verify_banking_login(banking_id, banking_password)
            if not verified_id:
                print("Banking authentication failed. Cancellation aborted."); return
            
            print("Processing refund...")
            refund_ok = process_refund_transfer(verified_id, amount, order_id)
            if not refund_ok:
                print("Refund failed. Cancellation aborted."); return
        
        # --- Update stock and statuses ---
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items_to_restock = cursor.fetchall()
        for product_id, quantity in items_to_restock:
            cursor.execute("UPDATE products SET stock = stock + %s WHERE product_id = %s", (quantity, product_id))
        
        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE order_id = %s", (order_id,))
        cursor.execute("UPDATE payments SET payment_status = 'Refunded' WHERE order_id = %s", (order_id,))
        cursor.execute("UPDATE shipments SET status = 'Cancelled' WHERE order_id = %s", (order_id,))

        conn.commit()
        print(f"\nOrder #{order_id} has been successfully cancelled and refunded. Stock has been updated.")

    except Exception as e:
        print(f"An error occurred during cancellation: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


def return_order(order_id, customer_id):
    """Handles the logic for returning an order AFTER it has been delivered."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get order status and payment details
        cursor.execute("""
            SELECT o.status, p.amount, p.payment_method
            FROM orders o
            JOIN payments p ON o.order_id = p.order_id
            WHERE o.order_id = %s AND o.customer_id = %s
        """, (order_id, customer_id))
        
        order_data = cursor.fetchone()
        if not order_data:
            print("Order not found."); return
        
        status, amount, payment_method = order_data

        # Business Rule: Can only return an order that has been successfully delivered.
        # We check this by querying the shipment status, not the order status.
        cursor.execute("SELECT status FROM shipments WHERE order_id = %s", (order_id,))
        shipment_status_result = cursor.fetchone()
        shipment_status = shipment_status_result[0] if shipment_status_result else ""

        if shipment_status.lower() != 'delivered':
            print(f"Cannot return order: Order must be 'Delivered' first. Current shipment status is '{shipment_status}'."); return
        if status.lower() == 'returned':
            print("This order has already been returned."); return

        # All returns require a refund.
        if payment_method == 'Online Payment':
            print("\nTo process your refund, please authenticate with your banking details.")
            try:
                banking_id = int(input("Enter your Banking Customer ID: ").strip())
                banking_password = input("Enter your Banking Password: ").strip()
            except ValueError:
                print("Invalid Banking ID format. Return aborted."); return

            verified_id = verify_banking_login(banking_id, banking_password)
            if not verified_id:
                print("Banking authentication failed. Return aborted."); return
            
            print("Processing refund...")
            refund_ok = process_refund_transfer(verified_id, amount, order_id)
            if not refund_ok:
                print("Refund failed. Return aborted."); return
        
        # --- Update stock and statuses ---
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items_to_restock = cursor.fetchall()
        for product_id, quantity in items_to_restock:
            # Business decision: for this project, we will restock returned items.
            cursor.execute("UPDATE products SET stock = stock + %s WHERE product_id = %s", (quantity, product_id))
        
        cursor.execute("UPDATE orders SET status = 'Returned' WHERE order_id = %s", (order_id,))
        cursor.execute("UPDATE payments SET payment_status = 'Refunded' WHERE order_id = %s", (order_id,))
        cursor.execute("UPDATE shipments SET status = 'Returned' WHERE order_id = %s", (order_id,))

        conn.commit()
        print(f"\nOrder #{order_id} has been successfully returned and refunded. Stock has been updated.")

    except Exception as e:
        print(f"An error occurred during return: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()