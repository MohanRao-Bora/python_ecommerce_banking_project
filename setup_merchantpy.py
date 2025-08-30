from db import get_connection
import random
from datetime import datetime

def setup_merchant_account():
   
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        merchant_name = "Your-Mart Merchant"
        merchant_email = "billing@your-mart.com"
        
        # Check if the merchant already exists to avoid creating duplicates
        cursor.execute("SELECT customer_id FROM Customer WHERE name = %s", (merchant_name,))
        if cursor.fetchone():
            print(f"Merchant '{merchant_name}' already exists in the banking system.")
            # Find and print the existing account ID for reference
            cursor.execute("""
                SELECT a.account_id FROM Account a
                JOIN Customer c ON a.customer_id = c.customer_id
                WHERE c.name = %s LIMIT 1
            """, (merchant_name,))
            existing_account = cursor.fetchone()
            if existing_account:
                print(f"Existing Merchant Account ID is: {existing_account[0]}")
            return

        # 1. Create the merchant as a "Customer" in the banking system
        cursor.execute("""
            INSERT INTO Customer (name, email, phone, address, dob, password)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING customer_id;
        """, (merchant_name, merchant_email, '9999999999', '123 Commerce Way', '2000-01-01', 'merchant_password'))
        
        merchant_customer_id = cursor.fetchone()[0]
        print(f"Merchant customer created with ID: {merchant_customer_id}")

        # 2. Create a "Current" bank account for the merchant to receive payments
        merchant_account_id = int(f"99{datetime.now().strftime('%y%m%d')}{random.randint(100, 999)}")
        
        cursor.execute("""
            INSERT INTO Account (account_id, customer_id, account_type, balance, branch_name, status)
            VALUES (%s, %s, 'Current', 0.00, 'Main Corporate Branch', 'Active');
        """, (merchant_account_id, merchant_customer_id, ))
        
        conn.commit()
        print(f"Merchant bank account created successfully with Account ID: {merchant_account_id}")

    except Exception as e:
        print(f"An error occurred during merchant setup: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_merchant_account()