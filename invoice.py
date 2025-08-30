from datetime import datetime
from dateutil.relativedelta import relativedelta
from db import get_connection

def create_invoice(cursor, order_id, payment_id, amount):
   
    try:
        # Step 1: Find the longest warranty period for all items in the order
        cursor.execute("""
            SELECT MAX(p.warranty_months)
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        longest_warranty_months = cursor.fetchone()[0]
        if longest_warranty_months is None:
            longest_warranty_months = 0

        # --- FIX: Calculate both start and end dates ---
        warranty_start_date = datetime.now()
        warranty_end_date = warranty_start_date + relativedelta(months=longest_warranty_months)

        # Step 3: Insert the new invoice record with both dates
        cursor.execute("""
            INSERT INTO invoice (order_id, payment_id, amount, warranty_start_date, warranty_end_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, payment_id, amount, warranty_start_date, warranty_end_date))
        
        print("Invoice created successfully.")
        
    except Exception as e:
        print(f"Error creating invoice: {e}")
        raise e


def display_invoice_for_order(order_id):
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # FIX: Update query to fetch the new columns
        cursor.execute("""
            SELECT i.invoice_id, i.warranty_start_date, i.warranty_end_date, o.order_date, c.name, c.email, p.amount, p.payment_method
            FROM invoice i
            JOIN orders o ON i.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN payments p ON i.payment_id = p.payment_id
            WHERE i.order_id = %s
        """, (order_id,))
        
        invoice_data = cursor.fetchone()
        if not invoice_data:
            print("No invoice found for this order.")
            return

        invoice_id, start_date, end_date, order_date, cust_name, email, amount, payment_method = invoice_data

        print("\n" + "="*55)
        print("                     INVOICE                     ")
        print("="*55)
        print(f" Invoice ID: {invoice_id:<15} Order ID: {order_id}")
        print(f" Order Date: {order_date.strftime('%Y-%m-%d %H:%M')}")
        # FIX: Display both warranty dates
        print(f" Warranty Start Date: {start_date.strftime('%Y-%m-%d')}")
        print(f" Warranty End Date:   {end_date.strftime('%Y-%m-%d')}")
        print("-"*55)
        print(" Billed To:")
        print(f"  {cust_name}")
        print(f"  {email}")
        print("-"*55)

        # ... (The rest of the function to display items remains the same) ...
        cursor.execute("""
            SELECT p.name, oi.quantity, oi.price, (oi.quantity * oi.price) as item_total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """, (order_id,))
        
        order_items = cursor.fetchall()
        print(" Product                 Qty     Price       Total")
        print("-"*55)
        for item in order_items:
            name, qty, price, item_total = item
            print(f" {name:<23} {qty:<7} {price:<11.2f} {item_total:<10.2f}")
        
        print("-"*55)
        print(f" Payment Method: {payment_method}")
        print(f" TOTAL AMOUNT:                           ₹{amount:<10.2f}")
        print("="*55)

    except Exception as e:
        print(f"Error displaying invoice: {e}")
    finally:
        if conn:
            conn.close()