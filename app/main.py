import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import create_db_and_tables
from app import models  # noqa: F401
from app.routers import auth, prompts

app = FastAPI(title="Promptarium API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://promptarium.netlify.app",
]

print("DEBUG ORIGINS:", repr(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(prompts.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def read_root():
    return {"message": "Promptarium API is running"}