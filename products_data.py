import pandas as pd
from db import get_connection

def import_products():
    df = pd.read_excel(r"C:\Users\91966\OneDrive\Desktop\sales_project\data\products_data.xlsx")
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO products (product_id, name, description, price, stock, category_id, seller_id, warranty_months)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING
            ''', (
                int(row['product_id']),
                row['name'],
                row['description'],
                float(row['price']),
                int(row['stock']),
                int(row['category_id']),
                int(row['seller_id']),
                int(row['warranty_months'])
            ))
        except Exception as e:
            print("Skipping product due to error:", e)
    conn.commit()
    cursor.close()
    conn.close()
    
import_products()
print("Imported Data Successfully")
