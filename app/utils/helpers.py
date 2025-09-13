import os
import aiofiles
from typing import Optional
from fastapi import UploadFile
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def save_uploaded_file(upload_file: UploadFile, filename: str) -> str:
    """Save uploaded file to the audio_files directory"""
    try:
        # Ensure audio_files directory exists
        os.makedirs(settings.AUDIO_FILES_PATH, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(settings.AUDIO_FILES_PATH, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)
        
        logger.info(f"File saved successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving file {filename}: {e}")
        raise e

def validate_audio_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """Validate uploaded audio file"""
    try:
        # Check file size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        
        # Check file extension
        if not file.filename:
            return False, "No filename provided"
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            return False, f"File format not allowed. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
        
        # Check MIME type (basic validation)
        if file.content_type and not file.content_type.startswith('audio/'):
            return False, "File is not an audio file"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return False, f"Validation error: {str(e)}"

def generate_file_url(filename: str) -> str:
    """Generate URL for the uploaded file"""
    # In production, this would be a proper URL
    # For now, we'll use a local URL
    base_url = f"http://localhost:{settings.PORT}"
    return f"{base_url}/audio_files/{filename}"

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0

def normalize_language_code(language: str) -> str:
    """Normalize language code to standard format"""
    language = language.lower().strip()
    
    # Map common variations to standard codes
    language_map = {
        'english': 'en',
        'eng': 'en',
        'arabic': 'ar',
        'ara': 'ar'
    }
    
    return language_map.get(language, language)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
