from db import get_connection
from getcustomers import Customer, Account, Transactions
from datetime import datetime
import sys

# Import your login function
from customer import login_customer  

def get_accounts(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT account_id, account_type, balance FROM Account WHERE customer_id = %s", (customer_id,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def deduct_balance(account_id, amount):
    conn = get_connection()
    cursor = conn.cursor()

    # Check balance
    cursor.execute("SELECT balance FROM Account WHERE account_id = %s", (account_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False, "Account not found"
    balance = result[0]

    if balance < amount:
        conn.close()
        return False, "Insufficient funds"

    # Deduct and insert transaction
    new_balance = balance - amount
    cursor.execute("UPDATE Account SET balance = %s WHERE account_id = %s", (new_balance, account_id))

    cursor.execute(
        "INSERT INTO Transactions (account_id, transaction_type, amount, transaction_date) VALUES (%s, %s, %s, %s)",
        (account_id, "debit", amount, datetime.now())
    )

    conn.commit()
    conn.close()
    return True, "Payment successful"

def process_bank_payment(customer_id, password, order_total):
    # Login verification
    if not login_customer(customer_id, password):
        return False

    accounts = get_accounts(customer_id)
    if not accounts:
        print("No accounts found for this customer.")
        return False

    print("\nAvailable Bank Accounts:")
    for idx, acc in enumerate(accounts, start=1):
        print(f"{idx}. Account ID: {acc[0]} | Type: {acc[1]} | Balance: {acc[2]}")

    choice = int(input("Choose account number: "))
    if choice < 1 or choice > len(accounts):
        print("Invalid choice")
        return False

    account_id = accounts[choice - 1][0]
    success, msg = deduct_balance(account_id, order_total)
    print(msg)
    return success
