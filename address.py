from db import get_connection

def add_address(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        addr_type = input("Enter address type (Billing/Shipping): ").capitalize()
        if addr_type not in ("Billing", "Shipping"):
            print("Invalid type. Use Billing or Shipping.")
            return

        street = input("Enter Street: ")
        city = input("Enter City: ")
        state = input("Enter State: ")
        pincode = input("Enter Pincode: ")

        cursor.execute("""
            INSERT INTO addresses (customer_id, type, street, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (customer_id, addr_type, street, city, state, pincode))

        conn.commit()
        print(f"{addr_type} address added successfully.")
    except Exception as e:
        print("Error adding address:", e)
    finally:
        cursor.close()
        conn.close()

def view_addresses(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT address_id, type, street, city, state, pincode
            FROM addresses
            WHERE customer_id = %s
        """, (customer_id,))
        addresses = cursor.fetchall()

        if not addresses:
            print("No addresses found.")
            return

        for addr in addresses:
            print(f"ID: {addr[0]}, Type: {addr[1]}, {addr[2]}, {addr[3]}, {addr[4]}, {addr[5]}")
    except Exception as e:
        print("Error viewing addresses:", e)
    finally:
        cursor.close()
        conn.close()

def delete_address(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT address_id, type, street, city, state, pincode
            FROM addresses
            WHERE customer_id = %s
        """, (customer_id,))
        addresses = cursor.fetchall()

        if not addresses:
            print("No addresses found.")
            return

        for addr in addresses:
            print(f"ID: {addr[0]}, Type: {addr[1]}, {addr[2]}, {addr[3]}, {addr[4]}, {addr[5]}")

        address_id = input("Enter address ID to delete: ").strip()
        if not address_id.isdigit():
            print("Invalid input.")
            return
        address_id = int(address_id)

        # Check if this address is used in any order
        cursor.execute("SELECT 1 FROM orders WHERE shipping_address_id = %s", (address_id,))
        if cursor.fetchone():
            print(" Cannot delete this address. It is linked to an existing order.")
            print(" You can update it instead.")
            return

        cursor.execute("DELETE FROM addresses WHERE address_id = %s AND customer_id = %s", (address_id, customer_id))
        conn.commit()
        print(" Address deleted successfully.")
    except Exception as e:
        print("Error deleting address:", e)
    finally:
        cursor.close()
        conn.close()
        
def update_address(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT address_id, type, street, city, state, pincode
            FROM addresses
            WHERE customer_id = %s
        """, (customer_id,))
        addresses = cursor.fetchall()

        if not addresses:
            print("No addresses found.")
            return

        for addr in addresses:
            print(f"ID: {addr[0]}, Type: {addr[1]}, {addr[2]}, {addr[3]}, {addr[4]}, {addr[5]}")

        address_id = input("Enter address ID to update: ").strip()
        if not address_id.isdigit():
            print("Invalid input.")
            return
        address_id = int(address_id)

        cursor.execute("SELECT 1 FROM addresses WHERE address_id = %s AND customer_id = %s", (address_id, customer_id))
        if not cursor.fetchone():
            print("Address not found.")
            return

        new_street = input("Enter new street: ").strip()
        new_city = input("Enter new city: ").strip()
        new_state = input("Enter new state: ").strip()
        new_pincode = input("Enter new pincode: ").strip()

        cursor.execute("""
            UPDATE addresses
            SET street = %s, city = %s, state = %s, pincode = %s
            WHERE address_id = %s AND customer_id = %s
        """, (new_street, new_city, new_state, new_pincode, address_id, customer_id))
        
        conn.commit()
        print(" Address updated successfully.")
    except Exception as e:
        print("Error updating address:", e)
    finally:
        cursor.close()
        conn.close()


def address_menu(customer_id):
    while True:
        print("\nAddress Menu")
        print("1. Add Address")
        print("2. View Addresses")
        print("3. Delete Address")
        print("4. Update Address")  # <-- Add this
        print("5. Back to Dashboard")

        choice = input("Enter your choice: ")
        if choice == "1":
            add_address(customer_id)
        elif choice == "2":
            view_addresses(customer_id)
        elif choice == "3":
            delete_address(customer_id)
        elif choice == "4":
            update_address(customer_id)  # <-- Add this
        elif choice == "5":
            break
        else:
            print("Invalid choice.")

def get_non_empty_input(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")
