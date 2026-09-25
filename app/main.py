import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import create_db_and_tables
from app.routers import auth, prompts

UPLOAD_DIR = "app/static/uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    create_db_and_tables()
    yield


app = FastAPI(
    title="Promptarium API",
    description="Backend API powering the Promptarium AI Prompt Vault",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://promptarium.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file route for profile images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(prompts.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "healthy", "service": "Promptarium API"}