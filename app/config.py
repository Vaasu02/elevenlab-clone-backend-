import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "elevenlabs_clone")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS Configuration
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # Audio Files Configuration
    AUDIO_FILES_PATH: str = os.getenv("AUDIO_FILES_PATH", "./audio_files")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_AUDIO_FORMATS: list = os.getenv("ALLOWED_AUDIO_FORMATS", "mp3,wav,m4a").split(",")

settings = Settings()
