"""
Automated Answer Sheet Evaluation System - Main Application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

import app.models
from app.config import get_settings
from app.routers import auth, exams, submissions, results
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"LLM Base URL: {settings.LLM_BASE_URL}")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="End-to-end automated answer sheet evaluation using OCR and NLP",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    import os
    error_msg = f"Global error: {exc}"
    logger.error(error_msg)
    traceback.print_exc()
    
    # Also log to a dedicated file for easier retrieval
    log_path = os.path.join(os.getcwd(), "backend_errors.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"URL: {request.url}\n")
            f.write(f"Method: {request.method}\n")
            f.write(f"Error: {str(exc)}\n")
            f.write(traceback.format_exc())
    except Exception as e:
        logger.error(f"Failed to write to error log: {e}")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc), "type": type(exc).__name__},
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(exams.router, prefix="/api/exams", tags=["Exams"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
