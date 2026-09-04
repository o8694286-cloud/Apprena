import os
import secrets
import sqlite3
import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import shutil

# Import hybride pour la base de données
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

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db_connection():
    if DATABASE_URL and HAS_PG8000:
        # Configuration PostgreSQL distante (Render) via pg8000
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
        # Repli local SQLite sur mobile
        conn = sqlite3.connect("boutique.db")
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

def init_db():
    try:
        conn, db_type = get_db_connection()
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
            conn.commit()
            conn.close()
        print(f"Base de données ({db_type}) initialisée.")
    except Exception as e:
        print(f"Erreur d'initialisation DB: {e}")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(username: str = Depends(authenticate_admin)):
    return FileResponse("static/admin.html")

@app.get("/api/products")
async def get_products():
    try:
        conn, db_type = get_db_connection()
        if db_type == "postgres":
            rows = conn.run("SELECT id, name, price, stock, image_url FROM products ORDER BY id DESC")
            products = [{"id": r[0], "name": r[1], "price": float(r[2]), "stock": r[3], "image_url": r[4]} for r in rows]
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
            rows = cursor.fetchall()
            products = [dict(row) for row in rows]
            conn.close()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    image: UploadFile = File(...)
):
    try:
        file_path = f"uploads/{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        conn, db_type = get_db_connection()
        img_url = f"/{file_path}"
        
        if db_type == "postgres":
            conn.run(
                "INSERT INTO products (name, price, stock, image_url) VALUES (:n, :p, :s, :i)",
                n=name, p=price, s=stock, i=img_url
            )
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)",
                (name, price, stock, img_url)
            )
            conn.commit()
            conn.close()
        return {"status": "success", "message": "Produit ajouté avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    try:
        conn, db_type = get_db_connection()
        if db_type == "postgres":
            conn.run("DELETE FROM products WHERE id = :id", id=product_id)
            conn.close()
        else:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
