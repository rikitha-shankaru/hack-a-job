from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import profile, jobs, tailor, email, autofill
from app.database import engine, Base
import os

app = FastAPI(
    title="Hack-A-Job API", 
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Compression middleware (reduces response size by 70-90%)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for PDFs and resumes
uploads_dir = "uploads/pdfs"
resumes_dir = "uploads/resumes"
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(resumes_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(tailor.router, prefix="/api/tailor", tags=["tailor"])
app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(autofill.router, prefix="/api/autofill", tags=["autofill"])

@app.get("/")
def root():
    return {"message": "Hack-A-Job API", "version": "1.0.0"}

@app.on_event("startup")
async def startup():
    # Create tables
    Base.metadata.create_all(bind=engine)

