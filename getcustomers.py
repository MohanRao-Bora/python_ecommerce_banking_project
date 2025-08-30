from db import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Create Customer table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Customer (
            customer_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(15),
            address TEXT,
            dob DATE,
            password Text NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Create Account table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Account (
            account_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES Customer(customer_id) ON DELETE CASCADE,
            customer_name VARCHAR(100),
            account_type VARCHAR(20) CHECK (account_type IN ('Savings', 'Current')),
            balance NUMERIC(15,2) DEFAULT 0,
            branch_name VARCHAR(100),
            status VARCHAR(20) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        cursor.execute("ALTER SEQUENCE customer_customer_id_seq RESTART WITH 30001;")

        # Create Transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Transactions (
            transaction_id SERIAL PRIMARY KEY,
            account_id INT REFERENCES Account(account_id) ON DELETE CASCADE,
            transaction_type VARCHAR(10) CHECK (transaction_type IN ('Credit', 'Debit')),
            amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            reference_no VARCHAR(100)
        );
        ''')

        # Create Beneficiary table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Beneficiary (
            beneficiary_id SERIAL PRIMARY KEY,
            customer_id INT REFERENCES Customer(customer_id) ON DELETE CASCADE,
            beneficiary_name VARCHAR(100) NOT NULL,
            beneficiary_account_number VARCHAR(30) NOT NULL,
            bank_name VARCHAR(100),
            IFSC_code VARCHAR(20)
        );
        ''')
                # Create IFSC_Branches table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS IFSC_Branches (
            ifsc_code VARCHAR(20) PRIMARY KEY,
            bank_name VARCHAR(100) NOT NULL,
            branch VARCHAR(100) NOT NULL,
            address TEXT,
            city VARCHAR(100),
            district VARCHAR(100),
            state VARCHAR(100)
        );
        ''')


        # Create Fund Transfer table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Fund_Transfer (
            transfer_id SERIAL PRIMARY KEY,
            from_account_id INT REFERENCES Account(account_id) ON DELETE CASCADE,
            to_account_id INT REFERENCES Account(account_id) ON DELETE CASCADE,
            amount NUMERIC(15,2) NOT NULL CHECK (amount > 0),
            transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mode VARCHAR(20) CHECK (mode IN ('NEFT', 'IMPS', 'RTGS')),
            status VARCHAR(20) DEFAULT 'Success'
        );
        ''')

        conn.commit()

    except Exception as e:
        print("Error creating tables:", e)

    finally:
        cursor.close()
        conn.close()

# Call the function
create_tables()
