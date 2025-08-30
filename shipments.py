from datetime import datetime
from db import get_connection

def check_and_update_shipment_status(order_id):
    """
    Checks shipment status. If an order is >24 hours old and still 'Processing',
    it updates the status to 'Delivered' in the database.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the order date and the current shipment status
        cursor.execute("""
            SELECT o.order_date, s.status
            FROM orders o
            LEFT JOIN shipments s ON o.order_id = s.order_id
            WHERE o.order_id = %s
        """, (order_id,))
        
        result = cursor.fetchone()
        if not result:
            print("Could not find shipment details for this order."); return
        
        order_date, current_status = result
        # Can't proceed if there's no order date
        if not order_date:
             print("Order date not found, cannot calculate status."); return
             
        hours_passed = (datetime.now() - order_date).total_seconds() / 3600.0

        # If it's over 24 hours and still processing, update it to Delivered.
        if hours_passed >= 24 and current_status == 'Processing':
            print("\nOrder is over 24 hours old. Updating status to Delivered...")
            
            update_time = datetime.now()
            # Set both shipment_date and delivery_date upon delivery
            cursor.execute("""
                UPDATE shipments
                SET status='Delivered', shipment_date=%s, delivery_date=%s
                WHERE order_id=%s
            """, (update_time, update_time, order_id))
            
            # Also update the main order status to keep it in sync
            cursor.execute("UPDATE orders SET status='Delivered' WHERE order_id=%s", (order_id,))
            conn.commit()
            print("Status updated successfully.")

        # Now, display the most current information from the database
        cursor.execute("SELECT * FROM shipments WHERE order_id = %s", (order_id,))
        shipment = cursor.fetchone()
        
        print("\n--- Shipment Status ---")
        if shipment:
            _, _, ship_date, del_date, courier, track_no, status = shipment
            print(f" Status: {status}")
            print(f" Tracking Number: {track_no}")
            print(f" Courier: {courier}")
            print(f" Shipped On: {ship_date.strftime('%Y-%m-%d') if ship_date else 'Pending'}")
            print(f" Delivered On: {del_date.strftime('%Y-%m-%d') if del_date else 'Pending'}")
        else:
            print("Shipment record not found.")

    except Exception as e:
        print(f"Error fetching shipment status: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()