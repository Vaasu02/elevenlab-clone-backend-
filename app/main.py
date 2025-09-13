from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, create_indexes
from app.routers import audio
from app.middleware.logging import LoggingMiddleware, SecurityLoggingMiddleware
from app.middleware.security import setup_rate_limiting
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ElevenLabs Clone API",
    description="Backend API for ElevenLabs clone with audio file management",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Setup rate limiting
app = setup_rate_limiting(app)

# Add security middleware
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(LoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await connect_to_mongo()
    await create_indexes()
    logger.info("FastAPI application started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()
    logger.info("FastAPI application shutdown")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "ElevenLabs Clone API is running"}

# Debug endpoint to test database connection
@app.get("/debug/db")
async def debug_database():
    """Debug database connection"""
    try:
        from app.database import get_database
        database = await get_database()
        if database is None:
            return {"error": "Database connection is None"}
        
        # Try to get collection
        collection = database["audio_files"]
        count = await collection.count_documents({})
        return {"status": "connected", "collection_count": count}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

# Include routers
app.include_router(audio.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to ElevenLabs Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "audio_languages": "/api/audio/languages",
            "audio_by_language": "/api/audio/{language}",
            "upload_audio": "/api/audio/upload",
            "serve_audio": "/api/audio/files/{filename}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
