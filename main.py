import os
import secrets
import sqlite3
import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import shutil

try:
    import pg8000.native
    HAS_PG8000 = True
except ImportError:
    HAS_PG8000 = False

app = FastAPI(title="Apprena - Fournitures Scolaires")

security = HTTPBasic()
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "vos_mot_de_passe_secret"

DATABASE_URL = os.environ.get("DATABASE_URL")

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def init_and_seed_db():
    try:
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
            count = conn.run("SELECT COUNT(*) FROM products;")[0][0]
            if count == 0:
                for i in range(1, 101):
                    conn.run(
                        "INSERT INTO products (name, price, stock, image_url) VALUES (:n, :p, :s, :i)",
                        n=f"Produit N°{i} - Fourniture Scolaire",
                        p=1000 * (i % 10 + 1),
                        s=50,
                        i=default_img
                    )
                print("100 produits automatiques insérés sur Postgres !")
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
            cursor.execute("SELECT COUNT(*) FROM products;")
            if cursor.fetchone()[0] == 0:
                for i in range(1, 101):
                    cursor.execute(
                        "INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)",
                        (f"Produit N°{i} - Fourniture Scolaire", 1000 * (i % 10 + 1), 50, default_img)
                    )
                conn.commit()
                print("100 produits automatiques insérés sur SQLite !")
            conn.close()
    except Exception as e:
        print(f"Erreur d'initialisation DB: {e}")

@app.on_event("startup")
def startup():
    init_and_seed_db()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/products")
async def get_products():
    try:
        conn, db_type = get_db_connection()
        if db_type == "postgres":
            rows = conn.run("SELECT id, name, price, stock, image_url FROM products ORDER BY id ASC")
            products = [{"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3], "image_url": r[4]} for r in rows]
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id ASC")
            rows = cursor.fetchall()
            products = [dict(row) for row in rows]
            conn.close()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
