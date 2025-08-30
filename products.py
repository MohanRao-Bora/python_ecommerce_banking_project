from db import get_connection

def get_all_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_id")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return categories

def get_products_by_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.product_id, p.name, p.description, p.price, p.stock, s.name AS seller_name
        FROM products p
        JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.category_id = %s
        ORDER BY p.product_id
    ''', (category_id,))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products


def search_products_by_category_name(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT p.product_id, p.name, p.price, p.stock
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE LOWER(c.category_name) LIKE %s
        """, (f"%{keyword.lower()}%",))

        return cursor.fetchall()
    except Exception as e:
        print("Error searching products by category:", e)
        return []
    finally:
        cursor.close()
        conn.close()




