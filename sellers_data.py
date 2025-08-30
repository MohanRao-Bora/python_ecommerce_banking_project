import pandas as pd
from db import get_connection

def import_sellers():
    df = pd.read_excel(r"C:\Users\91966\OneDrive\Desktop\sales_project\data\sellers_data.xlsx")
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO sellers (seller_id, name, gstin, phone_number,contact_mail)
                VALUES (%s, %s, %s, %s,%s) ON CONFLICT (seller_id) DO NOTHING
            ''', (int(row['seller_id']), row['name'], row['gstin'], row['phone_number'],row['contact_mail']))
        except Exception as e:
            print("Skipping seller due to error:", e)
    conn.commit()
    cursor.close()
    conn.close()
    
import_sellers()
print("Imported Data Successfully")