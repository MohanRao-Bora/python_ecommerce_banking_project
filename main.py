# --- Imports ---
from create_tables import create_all_tables
from customer import *
from products import *
from cart import *
from orders import *
from address import *
from invoice import display_invoice_for_order
from reviews import check_if_customer_purchased_product, add_review, get_reviews_for_product
from shipments import *
from db import get_connection
from cancellation import cancel_order, return_order



def banner():
    
    print("\n" + "=" * 35)
    print("      Welcome to Your-Mart ")
    print("=" * 35)

def signup_flow():
    
    print("\n--- Sign Up ---")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    phone = input("Enter your phone (10 digits): ")
    password = input("Set your password: ")
    add_customer(name, email, phone, password)

def login_flow():
    """Handles the customer login process."""
    print("\n--- Login ---")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    customer_id = verify_customer_login(email, password)

    if customer_id:
        print("Login successful!")
        customer_dashboard(customer_id)
    else:
        
        print("Invalid email or password.")

def customer_dashboard(customer_id):
   
    while True:
        print("\n--- Customer Dashboard ---")
        print("0. Enter category name to search products from: ")
        print("1. View Product Categories")
        print("2. View Products by Category")
        print("3. Manage My Profile")
        print("4. My Cart")
        print("5. View My Orders & Invoices")
        print("6. Manage My Addresses")
        print("7. Logout")
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            keyword = input("Enter category name to search products from: ")
            results = search_products_by_category_name(keyword)
            if results:
                print("\nProducts under this category:")
                for p in results:
                    print(f"ID: {p[0]}, Name: {p[1]}, Price: ₹{p[2]:.2f}, Stock: {p[3]}")
                handle_product_list_actions(customer_id)
            else:
                print("No products found for that category.")

        elif choice == "1":
            categories = get_all_categories()
            print("\nCategories:")
            for cid, cname in categories:
                print(f"{cid}. {cname}")

        elif choice == "2":
            categories = get_all_categories()
            print("\nAvailable Categories:")
            for cid, cname in categories:
                print(f"{cid}. {cname}")
            try:
                selected_id = int(input("Enter category ID: ").strip())
                products = get_products_by_category(selected_id)
                if products:
                    print("\nProducts:")
                    for p in products:
                        print(f"ID: {p[0]}, Name: {p[1]}, Price: ₹{p[3]:.2f}, Stock: {p[4]}, Seller: {p[5]}")
                    handle_product_list_actions(customer_id)
                else:
                    print("No products found in this category.")
            except (ValueError, IndexError):
                print("Invalid input.")

        elif choice == "3":
            show_profile_menu(customer_id)
        elif choice == "4":
            manage_cart(customer_id)
        elif choice == "5":
            order_actions_menu(customer_id)
        elif choice == "6":
            address_menu(customer_id)
        elif choice == "7":
            print("Logged out."); break
        else:
            print("Invalid choice. Try again.")

def handle_product_list_actions(customer_id):
    
    try:
        print("\n1. Add to Cart")
        print("2. Place Order Now")
        print("3. View Product Reviews")
        print("n. Do Nothing")
        action = input("Choose an option: ").strip().lower()
        
        if action == "1":
            product_id = int(input("Enter Product ID to add: "))
            quantity = int(input("Enter Quantity: "))
            add_to_cart(customer_id, product_id, quantity)
        elif action == "2":
            product_id = int(input("Enter Product ID to order: "))
            quantity = int(input("Enter Quantity: "))
            place_direct_order(customer_id, product_id, quantity)
        elif action == "3":
            product_id = int(input("Enter Product ID to view reviews: "))
            get_reviews_for_product(product_id)
    except ValueError:
        print("Invalid Input.")

def order_actions_menu(customer_id):
    """Shows orders and a menu for actions like invoice, review, shipment, or cancellation/return."""
    view_orders(customer_id)
    try:
        order_id = int(input("\nEnter an Order ID for more actions (or 0 to go back): ").strip())
        if order_id == 0:
            return
        
        print("\n--- Order Actions ---")
        print("1. View Invoice")
        print("2. Leave a Review")
        print("3. Check Shipment Status")
        print("4. Cancel or Return Order") # <-- Updated Text
        action = input("Choose an option: ").strip()

        if action == '1':
            display_invoice_for_order(order_id)
        elif action == '2':
            leave_review_flow(customer_id, order_id)
        elif action == '3':
                check_and_update_shipment_status(order_id)
        elif action == '4':
            # --- NEW SUB-MENU ---
            print("\nSelect an action:")
            print("1. Cancel this Order (if not yet shipped)")
            print("2. Return this Order (if delivered)")
            sub_choice = input("Choose an option: ").strip()
            if sub_choice == '1':
                confirm = input(f"Are you sure you want to cancel Order #{order_id}? (y/n): ").lower()
                if confirm == 'y':
                    cancel_order(order_id, customer_id)
            elif sub_choice == '2':
                confirm = input(f"Are you sure you want to return Order #{order_id}? (y/n): ").lower()
                if confirm == 'y':
                    return_order(order_id, customer_id)
            else:
                print("Invalid choice.")
            # --- END OF SUB-MENU ---
        else:
            print("Invalid choice.")

    except ValueError:
        print("Invalid input. Please enter a numeric Order ID.")

def leave_review_flow(customer_id, order_id):
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT p.product_id, p.name FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id = %s", (order_id,))
        products_in_order = cursor.fetchall()
        if not products_in_order:
            print("Could not find products for this order."); return
        print("\n--- Products in this Order ---")
        for pid, name in products_in_order:
            print(f"ID: {pid}, Name: {name}")
        
        product_id = int(input("Enter the Product ID you want to review: ").strip())
        if product_id not in [p[0] for p in products_in_order]:
            print("This product is not in the selected order."); return
        if not check_if_customer_purchased_product(customer_id, product_id):
            print("Verification failed. You can only review products you have purchased."); return
        
        rating = float(input("Enter your rating (e.g., 4.5): ").strip())
        comment = input("Enter your review comment: ").strip()
        add_review(customer_id, product_id, rating, comment)

    except (ValueError, IndexError):
        print("Invalid product ID or rating format.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn: conn.close()

def manage_cart(customer_id):
    """Handles viewing the cart and actions like updating, removing, or ordering."""
    while True:
        print("\n--- Your Cart ---")
        cart_items = view_cart(customer_id)
        if not cart_items:
            print("Your cart is empty.")
            break
        
        for item in cart_items:
            print(f"ID: {item[0]}, Name: {item[1]}, Qty: {item[2]}, Price: ₹{item[3]:.2f}, Total: ₹{item[4]:.2f}")

        print("\n--- Cart Options ---")
        print("1. Update Quantity")
        print("2. Remove Item")
        print("3. Place Order from Cart")
        print("4. Back to Dashboard")
        choice = input("Choose an option: ").strip()

        try:
            if choice == '1':
                # --- ADDED: The missing logic for updating quantity ---
                product_id = int(input("Enter Product ID to update: "))
                new_qty = int(input("Enter new quantity: "))
                if new_qty > 0:
                    update_cart_quantity(customer_id, product_id, new_qty)
                else:
                    # Automatically remove if quantity is 0 or less
                    remove_from_cart(customer_id, product_id)
                # --- End of added logic ---
            
            elif choice == '2':
                # --- ADDED: The missing logic for removing an item ---
                product_id = int(input("Enter Product ID to remove: "))
                remove_from_cart(customer_id, product_id)
                # --- End of added logic ---
            
            elif choice == '3':
                place_selected_items_order(customer_id)
            
            elif choice == '4':
                break
            
            else:
                print("Invalid choice.")
        
        except ValueError:
            print("Invalid input. Please enter a number.")

def show_profile_menu(customer_id):
    """Handles viewing and managing the customer's profile details."""
    while True:
        print("\n--- Manage My Profile ---")
        print("1. Update Profile")
        print("2. Delete Account")
        print("3. View My Details")
        print("4. Back")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            # --- ADDED: The missing logic for updating the profile ---
            password = input("To make changes, please enter your password: ").strip()
            if verify_password(customer_id, password):
                print("\nEnter new details (leave blank to keep current value).")
                new_name = input(f"Enter new name: ")
                new_email = input(f"Enter new email: ")
                new_phone = input(f"Enter new phone: ")
                update_customer(customer_id, new_name, new_email, new_phone)
            else:
                print("Incorrect password. Update failed.")
            # --- End of added logic ---

        elif choice == "2":
            # --- ADDED: The missing logic for deleting the account ---
            password = input("Enter your password to confirm account deletion: ").strip()
            if verify_password(customer_id, password):
                confirm = input("Are you absolutely sure? This cannot be undone. (y/n): ").lower()
                if confirm == 'y':
                    delete_customer(customer_id)
                    print("Your account has been permanently deleted.")
                    return # Exit the profile menu and the dashboard
            else:
                print("Incorrect password. Deletion failed.")
            # --- End of added logic ---
        
        elif choice == "3":
            customer = get_customer_by_id(customer_id)
            if customer:
                # Assuming password is at index 4 in the tuple
                print(f"ID: {customer[0]}, Name: {customer[1]}, Email: {customer[2]}, Phone: {customer[3]}")
        
        elif choice == "4":
            break
        
        else:
            print("Invalid choice.")

def main():
    
    create_all_tables()
    while True:
        banner()
        print("1. Sign Up")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            signup_flow()
        elif choice == "2":
            login_flow()
        elif choice == "3":
            print("Thank you for visiting Your-Mart!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
