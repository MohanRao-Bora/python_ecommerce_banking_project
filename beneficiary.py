import random
from datetime import datetime
from db import get_connection



def add_beneficiary(customer_id):
    """Allows a logged-in user to add a new beneficiary to their account."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        while True:
            acc_no1 = input("Enter Beneficiary Account Number: ").strip()
            acc_no2 = input("Re-enter Beneficiary Account Number: ").strip()
            if acc_no1 == acc_no2 and acc_no1.isdigit():
                beneficiary_account_number = acc_no1
                break
            print("Account numbers do not match or are invalid. Please try again.")

        cursor.execute("SELECT customer_id FROM Account WHERE account_id = %s", (int(beneficiary_account_number),))
        acc_row = cursor.fetchone()
        if not acc_row:
            print("Beneficiary account does not exist in our bank system.")
            return

        if acc_row[0] == customer_id:
            print("You cannot add yourself as a beneficiary.")
            return

        ifsc_code = input("Enter IFSC Code: ").strip().upper()
        cursor.execute("SELECT bank_name FROM IFSC_Branches WHERE UPPER(ifsc_code) = %s", (ifsc_code,))
        ifsc_row = cursor.fetchone()
        if not ifsc_row:
            print("Invalid IFSC Code.")
            return
        
        beneficiary_name = input("Enter Beneficiary Name / Nickname: ").strip()

        cursor.execute("SELECT 1 FROM Beneficiary WHERE customer_id = %s AND beneficiary_account_number = %s",
                       (customer_id, beneficiary_account_number))
        if cursor.fetchone():
            print("This beneficiary is already added.")
            return

        cursor.execute("""
            INSERT INTO Beneficiary (customer_id, beneficiary_name, beneficiary_account_number, bank_name, IFSC_code)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, beneficiary_name, beneficiary_account_number, ifsc_row[0], ifsc_code))

        conn.commit()
        print(f"Beneficiary '{beneficiary_name}' added successfully.")

    except Exception as e:
        print(f"Error while adding beneficiary: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


def view_beneficiaries(customer_id):

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT beneficiary_id, beneficiary_name, beneficiary_account_number, bank_name, IFSC_code
            FROM Beneficiary WHERE customer_id = %s ORDER BY beneficiary_id;
        """, (customer_id,))
        rows = cursor.fetchall()
        
        if not rows:
            print("\nNo beneficiaries found.")
            return

        print("\n--- Your Beneficiaries ---")
        for r in rows:
            print(f"ID: {r[0]} | Name: {r[1]} | Account: {r[2]} | Bank: {r[3]} | IFSC: {r[4]}")
            
    except Exception as e:
        print(f"Error while fetching beneficiaries: {e}")
    finally:
        if conn: conn.close()


def transfer_funds(customer_id):
    """Handles the interactive process for a user to transfer funds to a beneficiary."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # --- MODIFIED LOGIC: Use the smart account selection helper ---
        sender_account_id, sender_balance = _select_account_for_debit(cursor, customer_id)
        
        if sender_account_id is None:
            return # Abort the transfer
        # --- End of modification ---

        # (The rest of the logic for selecting a beneficiary and amount is correct)
        view_beneficiaries(customer_id)
        beneficiary_id = int(input("Enter Beneficiary ID to transfer to: ").strip())
        cursor.execute("SELECT beneficiary_account_number, beneficiary_name FROM Beneficiary WHERE beneficiary_id = %s AND customer_id = %s", (beneficiary_id, customer_id))
        ben_row = cursor.fetchone()
        if not ben_row:
            print("Invalid beneficiary selected."); return
        
        destination_account_id = int(ben_row[0])
        beneficiary_name = ben_row[1]
        
        amount = float(input("Enter amount to transfer: ").strip())
        if amount <= 0 or amount > sender_balance:
            print(f"Invalid amount or insufficient balance (Balance: ₹{sender_balance:.2f})."); return
        
        ref_no = str(random.randint(10**15, 10**16 - 1))
        
        # Perform transaction
        cursor.execute("UPDATE Account SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cursor.execute("UPDATE Account SET balance = balance + %s WHERE account_id = %s", (amount, destination_account_id))
        
        # Log transactions
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Debit', %s, %s, %s)",
                       (sender_account_id, amount, f"Transfer to {beneficiary_name}", ref_no))
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Credit', %s, %s, %s)",
                       (destination_account_id, amount, f"Received from customer {customer_id}", ref_no))
        
        cursor.execute("INSERT INTO Fund_Transfer (from_account_id, to_account_id, amount, mode, status) VALUES (%s, %s, %s, 'NEFT', 'Success')",
                       (sender_account_id, destination_account_id, amount))

        conn.commit()
        print(f"\nSuccessfully transferred ₹{amount:.2f} to {beneficiary_name}.")

    except (ValueError, TypeError):
        print("Invalid input. Please try again.")
        if conn: conn.rollback()
    except Exception as e:
        print(f"Error during transfer: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


def beneficiary_menu(customer_id):
    
    while True:
        print("\n====== Beneficiary Management ======")
        print("1. Add Beneficiary")
        print("2. View Beneficiaries")
        print("3. Transfer Funds")
        print("4. Back to Main Menu")
        choice = input("Choose an option: ").strip()
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




def get_merchant_account_id(merchant_name="Your-Mart Merchant"):
    """Finds the primary bank account ID for the named merchant."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id FROM Customer WHERE name = %s", (merchant_name,))
        merchant_customer = cursor.fetchone()
        if not merchant_customer:
            return None
        
        merchant_customer_id = merchant_customer[0]
        cursor.execute("SELECT account_id FROM Account WHERE customer_id = %s AND account_type = 'Current' LIMIT 1", (merchant_customer_id,))
        merchant_account = cursor.fetchone()
        
        return merchant_account[0] if merchant_account else None
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def process_payment_transfer(sender_customer_id, merchant_account_id, amount):
    """
    Processes a non-interactive fund transfer for a payment using smart account selection.
    Returns True for success, False for failure.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # --- MODIFIED LOGIC: Use the smart account selection helper ---
        sender_account_id, sender_balance = _select_account_for_debit(cursor, sender_customer_id)
        
        if sender_account_id is None:
            return False # Selection failed or was cancelled
        
        if sender_balance < amount:
            print(f"Error: Insufficient funds. Your balance is ₹{sender_balance:.2f}, but the payment is ₹{amount:.2f}.")
            return False
        # --- End of modification ---
        
        payment_ref_no = str(random.randint(10**15, 10**16 - 1))

        # Perform Transaction
        cursor.execute("UPDATE Account SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cursor.execute("UPDATE Account SET balance = balance + %s WHERE account_id = %s", (amount, merchant_account_id))

        # Log transactions
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Debit', %s, %s, %s)",
                       (sender_account_id, amount, f"Payment to merchant account {merchant_account_id}", payment_ref_no))
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Credit', %s, %s, %s)",
                       (merchant_account_id, amount, f"Payment received from customer {sender_customer_id}", payment_ref_no))
        
        # Log in Fund_Transfer table
        cursor.execute("INSERT INTO Fund_Transfer (from_account_id, to_account_id, amount, mode, status) VALUES (%s, %s, %s, 'IMPS', 'Success')",
                       (sender_account_id, merchant_account_id, amount))

        conn.commit()
        return True

    except Exception as e:
        print(f"Payment processing error: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
            
def process_refund_transfer(customer_banking_id, amount, order_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        merchant_account_id = get_merchant_account_id()
        if not merchant_account_id:
            print("Error: Merchant account not found for refund."); return False

        # Find customer's account (we'll refund to their first account)
        cursor.execute("SELECT account_id FROM Account WHERE customer_id = %s LIMIT 1", (customer_banking_id,))
        customer_account = cursor.fetchone()
        if not customer_account:
            print("Error: Customer bank account not found for refund."); return False
        customer_account_id = customer_account[0]
        
        # Check if merchant has enough funds for the refund
        cursor.execute("SELECT balance FROM Account WHERE account_id = %s", (merchant_account_id,))
        merchant_balance = cursor.fetchone()[0]
        if merchant_balance < amount:
            print("Error: Merchant has insufficient funds to process refund."); return False

        # --- Perform Refund Transaction ---
        ref_no = str(random.randint(10**15, 10**16 - 1))
        
        # 1. Debit from merchant
        cursor.execute("UPDATE Account SET balance = balance - %s WHERE account_id = %s", (amount, merchant_account_id))
        # 2. Credit to customer
        cursor.execute("UPDATE Account SET balance = balance + %s WHERE account_id = %s", (amount, customer_account_id))

        # 3. Log transactions
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Debit', %s, %s, %s)",
                       (merchant_account_id, amount, f"Refund for Order #{order_id}", ref_no))
        cursor.execute("INSERT INTO Transactions (account_id, transaction_type, amount, description, reference_no) VALUES (%s, 'Credit', %s, %s, %s)",
                       (customer_account_id, amount, f"Refund received for Order #{order_id}", ref_no))
        
        conn.commit()
        print("Refund processed successfully.")
        return True

    except Exception as e:
        print(f"Refund processing error: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
        
def _select_account_for_debit(cursor, customer_id):
    """
    Fetches a customer's accounts and handles the selection process.
    - If 1 account, auto-selects it.
    - If >1 account, prompts the user to choose.
    - If 0 accounts, returns None.
    Returns a tuple: (account_id, balance) or None if failed.
    """
    cursor.execute("SELECT account_id, account_type, balance FROM Account WHERE customer_id = %s", (customer_id,))
    accounts = cursor.fetchall()

    if not accounts:
        print("Error: No bank accounts found for this customer.")
        return None, None
    
    if len(accounts) == 1:
        account = accounts[0]
        print(f"Using your only account ({account[1]}) for this transaction.")
        return account[0], account[2] # Returns account_id, balance
    else:
        print("\nYou have multiple accounts. Please choose one to pay from:")
        for idx, (acc_id, acc_type, balance) in enumerate(accounts, start=1):
            print(f"{idx}. {acc_type} (Account: {acc_id}, Balance: ₹{balance:.2f})")
        
        try:
            choice = int(input("Choose an account number: ").strip())
            if 1 <= choice <= len(accounts):
                selected_account = accounts[choice - 1]
                return selected_account[0], selected_account[2] # Returns account_id, balance
            else:
                print("Invalid choice.")
                return None, None
        except ValueError:
            print("Invalid input. Please enter a number.")
            return None, None