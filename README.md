# Python E-Commerce & Banking CLI Application

A project simulating a full e-commerce workflow (`main.py`) and a standalone banking system (`banking_main.py`), which are integrated to handle real-time payments and refunds.

---

## Key Features ✨

#### Sales Module (`main.py`)
* **Full E-Commerce Workflow:** Complete user journey from registration and login to product browsing, cart management, and a secure checkout.
* **Order Management:** Customers can view their order history, check automated shipment statuses, and view detailed invoices.
* **Customer Interaction:** A full review system allows customers to leave ratings and comments for products they have purchased.
* **Cancellations & Returns:** Logic for customers to cancel or return orders, triggering automated refunds and product restocking.

#### Banking Module (`banking_main.py`)
* **Account Management:** Ability for users to create and manage their own bank accounts (Savings & Current).
* **Core Banking Operations:** Supports key features like depositing money, viewing transaction history, and managing beneficiaries.
* **Fund Transfers:** Allows for secure, interactive fund transfers between customers within the banking system.

#### System Integration
* The sales module securely authenticates with the banking module to process real-time payments and automated refunds without storing sensitive banking links in the sales database.

## Technologies Used 🛠️

* **Language:** Python
* **Database:** PostgreSQL
* **Libraries:**
    * `psycopg2` (for database connection)
    * `pandas` (for initial data import)
    * `python-dateutil` (for warranty date calculations)

## How to Set Up and Run

1.  **Database Setup:**
    * Ensure PostgreSQL is running.
    * Create a database (e.g., `sales_project`).
    * Update the connection details in the `db.py` file.
    * Run the table creation scripts: `python create_tables.py` and `python create_banking_tables.py`.

2.  **Install Dependencies:**
    * Navigate to the project folder in your terminal.
    * Run the command: `pip install -r requirements.txt`

3.  **Run the Applications:**
    This project contains two separate command-line applications.

    * **To run the E-Commerce Store (for customers):**
        ```bash
        python main.py
        ```

    * **To run the Banking System (for bank customers):**
        ```bash
        python banking_main.py
        ```
