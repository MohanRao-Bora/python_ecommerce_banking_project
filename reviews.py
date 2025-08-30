from db import get_connection

def check_if_customer_purchased_product(customer_id, product_id):
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.customer_id = %s AND oi.product_id = %s
            LIMIT 1;
        """, (customer_id, product_id))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking purchase history: {e}")
        return False
    finally:
        if conn:
            conn.close()

def add_review(customer_id, product_id, rating, comment):
   
    if not (1 <= rating <= 5):
        print("Invalid rating. Please enter a number between 1 and 5.")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reviews (customer_id, product_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, product_id, rating, comment))
        conn.commit()
        print("\nThank you! Your review has been submitted successfully.")
    except Exception as e:
        print(f"Error submitting review: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_reviews_for_product(product_id):
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Query to get average rating and count
        cursor.execute("SELECT AVG(rating), COUNT(rating) FROM reviews WHERE product_id = %s", (product_id,))
        stats = cursor.fetchone()
        avg_rating, review_count = (stats[0], stats[1]) if stats and stats[0] is not None else (0, 0)

        # Query to get individual reviews with customer names
        cursor.execute("""
            SELECT r.rating, r.comment, c.name FROM reviews r
            JOIN customers c ON r.customer_id = c.customer_id
            WHERE r.product_id = %s ORDER BY r.review_date DESC;
        """, (product_id,))
        reviews = cursor.fetchall()
        
        print("\n--- Product Reviews ---")
        if review_count > 0:
            print(f"Average Rating: {avg_rating:.1f}/5.0 (from {review_count} reviews)")
            print("-" * 35)
            for rating, comment, name in reviews:
                print(f" Rating: {'★' * round(rating)}{'☆' * (5-round(rating))}")
                print(f" Reviewer: {name}")
                print(f' "{comment}"')
                print("-" * 35)
        else:
            print("This product has no reviews yet.")
            
    except Exception as e:
        print(f"Error fetching reviews: {e}")
    finally:
        if conn:
            conn.close()