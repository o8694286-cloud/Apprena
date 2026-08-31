import sqlite3
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os
import shutil

app = FastAPI(title="Apprena - Fournitures Scolaires")

# Création des dossiers nécessaires
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    # Option nolock=1 pour éviter le blocage SQLite sur la mémoire /sdcard Android
    conn = sqlite3.connect("file:boutique.db?nolock=1", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            image_url TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.get("/admin", response_class=HTMLResponse)
async def read_admin():
    return FileResponse("static/admin.html")

# Route d'obtention des produits
@app.get("/api/products")
async def get_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

# Route d'ajout d'un produit
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
        "INSERT INTO products (name, price, stock, image_url) VALUES (?, ?, ?, ?)",
        (name, price, stock, f"/{image_filename}")
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Produit ajouté avec succès !"}

# Route de suppression d'un produit
@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Produit supprimé avec succès !"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
