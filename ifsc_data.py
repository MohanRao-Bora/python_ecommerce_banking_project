
import pandas as pd
from db import get_connection
from psycopg2.extras import execute_values

# Read Excel file
excel_path = r"C:\Users\91966\OneDrive\Desktop\dummy_ifsc_codes (1).xlsx"
df = pd.read_excel(excel_path)

# Connect to DB
conn = get_connection()
cursor = conn.cursor()

# Target table name
table_name = "ifsc_branches"

# Generate the INSERT query dynamically
columns = ','.join(df.columns)
insert_query = f"INSERT INTO {table_name} ({columns}) VALUES %s"

# Insert data
try:
    execute_values(cursor, insert_query, df.values.tolist())
    conn.commit()
    print(" Data imported successfully.")
except Exception as e:
    print(" Error importing data:", e)
    conn.rollback()
finally:
    cursor.close()
    conn.close()
