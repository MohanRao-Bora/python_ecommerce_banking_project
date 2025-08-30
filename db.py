import psycopg2

DB_NAME = "sales_project"
DB_USER = "postgres"
DB_PASSWORD = "Mohan@2580"
DB_HOST = "localhost"
DB_PORT = "5432"  

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )


