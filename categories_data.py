import pandas as pd
from db import get_connection

def import_categories():
    df = pd.read_excel(r"C:\Users\91966\OneDrive\Desktop\sales_project\data\categories_data.xlsx")
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("INSERT INTO categories (category_id, category_name) VALUES (%s, %s) ON CONFLICT (category_id) DO NOTHING",
                           (int(row['category_id']), row['category_name']))
        except Exception as e:
            print("Skipping category due to error:", e)
    conn.commit()
    cursor.close()
    conn.close()
import_categories()
print("Imported Data Successfully")