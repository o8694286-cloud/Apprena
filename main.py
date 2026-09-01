import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

security = HTTPBasic()

# Remplacez vos identifiants ici si besoin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "NouveauMotDePasse"

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

# Route sécurisée pour la page admin
@app.get("/admin")
def get_admin_page(username: str = Depends(authenticate_admin)):
    return FileResponse("static/admin.html")

# Conservez le reste de vos routes et le montage statique
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
