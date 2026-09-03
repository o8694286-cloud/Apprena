import os
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import shutil

app = FastAPI(title="Apprena - Fournitures Scolaires")

security = HTTPBasic()

# Vos identifiants admin
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

def get_db():
    if not DATABASE_URL:
        raise Exception("La variable DATABASE_URL n'est pas configurée dans Render.")
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
    return conn

def init_db():
    if DATABASE_URL:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price NUMERIC NOT NULL,
                stock INTEGER DEFAULT 0,
                image_url TEXT
            )
        """)
        conn.commit()
        conn.close()

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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    conn.close()
    return products

@app.post("/api/products")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    image: UploadFile = File(...)
):
    image_filename = f"uploads/{image.filename}"
    with open(image_filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, price, stock, image_url) VALUES (%s, %s, %s, %s)",
        (name, price, stock, f"/{image_filename}")
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Produit ajouté avec succès !"}

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Produit supprimé avec succès !"}
