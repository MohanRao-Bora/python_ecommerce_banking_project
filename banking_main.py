import random
from db import get_connection
from datetime import datetime
import re
import sys
from beneficiary import *

# ---------------- Validation Functions ----------------
def is_valid_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)

def is_valid_phone(phone):
    return re.match(r"^\d{10}$", phone)

def is_valid_dob(dob):
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        today = datetime.today().date()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        if age < 18:
            print("Customer must be at least 18 years old to open an account.")
            return False
        return True
    except ValueError:
        return False

# ---------------- Create Customer & Account ----------------
def create_customer_and_account():
    """Handles the creation of a new customer and one or more bank accounts."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("\n--- Create New Customer & Account ---")

        # --- Gather User Input with Validation ---
        name = input("Enter name: ").strip()
        while True:
            email = input("Enter Email: ").strip()
            if is_valid_email(email): break
            print("Invalid email format.")
        while True:
            phone = input("Enter 10-digit Phone Number: ").strip()
            if is_valid_phone(phone): break
            print("Invalid phone number.")
        address = input("Enter Address: ").strip()
        while True:
            dob = input("Enter Date of Birth (YYYY-MM-DD): ").strip()
            if is_valid_dob(dob): break
            print("Invalid DOB or format. Use YYYY-MM-DD.")
        while True:
            password = input("Create a Password: ").strip()
            confirm_password = input("Confirm Password: ").strip()
            if password and password == confirm_password: break
            print("Passwords do not match or are empty. Try again.")

        # --- Create Customer Record ---
        cursor.execute('''
            INSERT INTO Customer (name, email, phone, address, dob, password)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING customer_id;
            ''', (name, email, phone, address, dob, password))
        customer_id = cursor.fetchone()[0]

        # --- Create Bank Account(s) ---
        while True:
            ifsc_code = input("Enter IFSC Code: ").strip().upper()
            cursor.execute("SELECT branch FROM ifsc_branches WHERE UPPER(ifsc_code) = %s", (ifsc_code,))
            row = cursor.fetchone()
            if row:
                branch_name = row[0]; break
            print("Invalid IFSC Code. Please try again.")

        print("\nWhich accounts to open? Options: Savings, Current")
        chosen_types_str = input("Enter choices separated by a comma (e.g., Savings, Current): ")
        chosen_types = [acc.strip().capitalize() for acc in chosen_types_str.split(",")]
        valid_types = {"Savings", "Current"}
        
        created_accounts = False
        for account_type in chosen_types:
            if account_type in valid_types:
                initial_balance = float(input(f"Enter Initial Balance for {account_type} account: "))
                
                # --- CORRECTED: Restored your original date-based logic ---
                today_prefix = datetime.today().strftime('%Y%m%d')
                
                # This query now works by temporarily treating the BIGINT as TEXT for the search
                cursor.execute(
                    "SELECT COUNT(*) FROM Account WHERE CAST(account_id AS TEXT) LIKE %s;", 
                    (today_prefix + '%',)
                )
                
                count_today = cursor.fetchone()[0] + 1
                
                # Create the final ID and convert it to a number (BIGINT)
                new_account_id = int(f"{today_prefix}{count_today:02d}")
                # --- End of correction ---

                cursor.execute('''
                    INSERT INTO Account (account_id, customer_id, account_type, balance, branch_name)
                    VALUES (%s, %s, %s, %s, %s);
                    ''', (new_account_id, customer_id, account_type, initial_balance, branch_name))
                print(f"-> {account_type} Account Created! Account ID: {new_account_id}")
                created_accounts = True

        if created_accounts:
            conn.commit()
            print(f"\nCustomer & Account(s) Created Successfully! Your Customer ID is: {customer_id}")
        else:
            print("\nNo valid account types were selected. Process cancelled.")
            conn.rollback()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

# ---------------- Update Customer ----------------
def update_customer():
    """Updates the details for a given customer ID after validating the input."""
    customer_id_str = input("Enter Customer ID to update: ").strip()

    
    if not customer_id_str.isdigit():
        print("\nError: Invalid input. Please enter a valid, numeric Customer ID.")
        return
    
    
    customer_id = int(customer_id_str)
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Customer WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()

        if not customer:
            print("Customer not found!")
            return

        print("\nLeave a field blank to keep the existing value.")
        
        # Original customer data: index 1=name, 2=email, 3=phone, 4=address, 5=dob
        name = input(f"Enter new name ({customer[1]}): ").strip() or customer[1]
        email = input(f"Enter new email ({customer[2]}): ").strip() or customer[2]
        phone = input(f"Enter new phone ({customer[3]}): ").strip() or customer[3]
        address = input(f"Enter new address ({customer[4]}): ").strip() or customer[4]
        dob = input(f"Enter new date of birth ({customer[5]}): ").strip() or customer[5]

        cursor.execute("""
            UPDATE Customer
            SET name=%s, email=%s, phone=%s, address=%s, dob=%s
            WHERE customer_id=%s
        """, (name, email, phone, address, dob, customer_id))

        conn.commit()
        print("\nCustomer details updated successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

# ---------------- Deposit Money Feature ----------------
def deposit_money(customer_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT account_id, account_type, balance FROM account WHERE customer_id = %s", (customer_id,))
        accounts = cursor.fetchall()

        if not accounts:
            print("No accounts found.")
            return

        print("\nYour Accounts:")
        for idx, (acc_id, acc_type, balance) in enumerate(accounts, start=1):
            print(f"{idx}. {acc_id} - {acc_type} (Balance: ₹{balance:.2f})")

        choice = int(input("Select account number to deposit into: "))
        if choice < 1 or choice > len(accounts):
            print("Invalid choice.")
            return

        account_id = accounts[choice - 1][0]
        amount = float(input("Enter amount to deposit: "))
        if amount <= 0:
            print("Amount must be positive.")
            return

        # Update account balance
        cursor.execute(
            "UPDATE account SET balance = balance + %s WHERE account_id = %s",
            (amount, account_id)
        )

        # Generate a random 16-digit reference number
        reference_no = str(random.randint(10**15, 10**16 - 1))

        # Insert into transactions table
        cursor.execute("""
            INSERT INTO transactions (account_id, transaction_type, amount, description, reference_no)
            VALUES (%s, 'Credit', %s, %s, %s)
        """, (account_id, amount, 'Deposit via Customer', reference_no))

        conn.commit()
        print(f"₹{amount:.2f} deposited successfully into account {account_id}. Reference No: {reference_no}")

    except Exception as e:
        print("Error while depositing:", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
def show_customer_details(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.customer_id, c.name, c.email, c.phone, c.address, c.dob,
                   a.account_id, a.account_type, a.balance, a.branch_name, a.status
            FROM Customer c
            JOIN Account a ON c.customer_id = a.customer_id
            WHERE c.customer_id = %s
        """, (customer_id,))
        rows = cursor.fetchall()

        if rows:
            print("\n====== Customer Details ======")
            for row in rows:
                print(f"Customer ID : {row[0]}")
                print(f"Name        : {row[1]}")
                print(f"Email       : {row[2]}")
                print(f"Phone       : {row[3]}")
                print(f"Address     : {row[4]}")
                print(f"DOB         : {row[5]}")
                print(f"Account ID  : {row[6]}")
                print(f"Type        : {row[7]}")
                print(f"Balance     : ₹{row[8]:.2f}")
                print(f"Branch      : {row[9]}")
                print(f"Status      : {row[10]}")
                print("-" * 40)
        else:
            print("No details found for this customer.")

    except Exception as e:
        print("Error while fetching customer details:", e)
    finally:
        cursor.close()
        conn.close()



# ---------------- Transaction History Feature ----------------
def view_transaction_history(customer_id):
    # First show customer details
    show_customer_details(customer_id)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get all accounts for this customer
        cursor.execute("SELECT account_id, account_type FROM account WHERE customer_id = %s", (customer_id,))
        accounts = cursor.fetchall()

        if not accounts:
            print("No accounts found.")
            return

        print("\nYour Accounts:")
        for idx, (acc_id, acc_type) in enumerate(accounts, start=1):
            print(f"{idx}. {acc_id} - {acc_type}")

        choice = int(input("Select account to view transactions: "))
        if choice < 1 or choice > len(accounts):
            print("Invalid choice.")
            return

        account_id = accounts[choice - 1][0]

        # Ask user which history they want
        print("\n1. Last 10 Transactions")
        print("2. Statement between Dates")
        option = int(input("Choose option: "))

        if option == 1:
            cursor.execute("""
                SELECT transaction_id, transaction_type, amount, transaction_date, description, reference_no
                FROM transactions
                WHERE account_id = %s
                ORDER BY transaction_date DESC
                LIMIT 10
            """, (account_id,))
        elif option == 2:
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            cursor.execute("""
                SELECT transaction_id, transaction_type, amount, transaction_date, description, reference_no
                FROM transactions
                WHERE account_id = %s
                  AND transaction_date::date BETWEEN %s AND %s
                ORDER BY transaction_date DESC
            """, (account_id, start_date, end_date))
        else:
            print("Invalid option.")
            return

        rows = cursor.fetchall()

        if not rows:
            print("No transactions found for this selection.")
            return

        print("\n====== Transaction History ======")
        for idx, tx in enumerate(rows, start=1):
            print(f"{idx}. {tx[1]} | ₹{tx[2]:.2f} | {tx[3]} | {tx[4]} | Ref: {tx[5]}")

    except Exception as e:
        print("Error while fetching history:", e)
    finally:
        cursor.close()
        conn.close()


# ---------------- Login & Menu ----------------
def customer_login():
    customer_id = input("Enter your Customer ID: ")
    password = input("Enter your password: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, name FROM Customer WHERE customer_id = %s AND password = %s",
        (customer_id, password)
    )
    user = cursor.fetchone()
    
    if user:
        customer_id, customer_name = user
        print(f"Login successful! Welcome {customer_name}")
        customer_menu(customer_id)
    else:
        print("Invalid Customer ID or password.")

    cursor.close()
    conn.close()

def customer_menu(customer_id):
    while True:
        print("\n====== Customer Menu ======")
        print("1. Beneficiary Management")
        print("2. Deposit Money")
        print("3. View Transaction History")
        print("4. Back to Main Menu")
        choice = input("Choose an option: ")

        if choice == "1":
            beneficiary_menu(customer_id)
        elif choice == "2":
            deposit_money(customer_id)
        elif choice == "3":
            view_transaction_history(customer_id)
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

def beneficiary_menu(customer_id):
    while True:
        print("\n====== Beneficiary Management ======")
        print("1. Add Beneficiary")
        print("2. View Beneficiaries")
        print("3. Transfer Funds")
        print("4. Back")
        choice = input("Choose an option: ")

        if choice == "1":
            add_beneficiary(customer_id)
        elif choice == "2":
            view_beneficiaries(customer_id)
        elif choice == "3":
            transfer_funds(customer_id)
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

# ---------------- Main ----------------
def main():
    while True:
        print("\n====== BANKING SYSTEM ======")
        print("1. Create New Account")
        print("2. Update Customer Details")
        print("3. Login")
        print("4. Exit")
        
        choice = input("Choose an option: ")

        if choice == "1":
            create_customer_and_account()
        elif choice == "2":
            update_customer()
        elif choice == "3":
            customer_login()
        elif choice == "4":
            print("Thank you for using the Banking System!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()



# Add this function to your banking_main.py file

def verify_banking_login(customer_id, password):
    """
    Verifies banking credentials without user interaction.
    Returns the customer_id if successful, otherwise None.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_id FROM Customer WHERE customer_id = %s AND password = %s",
            (customer_id, password)
        )
        user = cursor.fetchone()
        if user:
            return user[0]
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        if conn:
            conn.close()
