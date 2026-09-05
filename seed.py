import os
import sqlite3
import urllib.parse

DATABASE_URL = os.environ.get("DATABASE_URL")

try:
    import pg8000.native
    HAS_PG8000 = True
except ImportError:
    HAS_PG8000 = False

def get_db_connection():
    if DATABASE_URL and HAS_PG8000:
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = pg8000.native.Connection(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432,
            database=url.path[1:]
        )
        return conn, "postgres"
    else:
        conn = sqlite3.connect("boutique.db")
        return conn, "sqlite"

def seed_100_products():
    conn, db_type = get_db_connection()
    default_img = "https://placehold.co/600x400/eeb025/ffffff?text=Image+Produit"
    
    if db_type == "postgres":
        conn.run("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price NUMERIC NOT NULL,
                stock INTEGER DEFAULT 0,
                image_url TEXT
            );
        """)
        conn.run("TRUNCATE TABLE products RESTART IDENTITY;")
        for i in range(1, 101):
            conn.run(
                "INSERT INTO products (name, price, stock, image_url) VALUES (:n, :p, :s, :i)",
                n=f"Produit N°{i} - Fourniture Scolaire",
                p=1000 * (i % 10 + 1),
                s=50,
                i=default_img
            )
        conn.close()
    else:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                image_url TEXT
            );
        """)
        cursor.execute("DELETE FROM products;")
        for i in range(1, 101):
            cursor.execute(
                "INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)",
                (f"Produit N°{i} - Fourniture Scolaire", 1000 * (i % 10 + 1), 50, default_img)
            )
        conn.commit()
        conn.close()
        
    print("100 produits modèles ont été insérés avec succès !")

if __name__ == "__main__":
    seed_100_products()
