import secrets
import os
from fastapi import FastAPI, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

security = HTTPBasic()

# Vos identifiants de connexion
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "vos_mot_de_passe_secret"

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

# Route sécurisée demandant un mot de passe
@app.get("/admin")
def get_admin_page(username: str = Depends(authenticate_admin)):
    return FileResponse("static/admin.html")

# Route d'ajout de produit pour le formulaire admin
@app.post("/api/products")
async def add_product(
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image: UploadFile = File(...)
):
    # Logique de traitement / sauvegarde
    return {"message": "Produit ajouté avec succès"}

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
