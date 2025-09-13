from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status, Request
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.models.audio import (
    AudioFile, AudioFileCreate, AudioFileResponse, 
    LanguageResponse, AudioUploadResponse, ErrorResponse
)
from app.services.audio_service import audio_service
from app.utils.helpers import (
    save_uploaded_file, validate_audio_file, 
    generate_file_url, get_file_size, normalize_language_code
)
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/audio", tags=["Audio"])

# Rate limiter for audio endpoints
limiter = Limiter(key_func=get_remote_address)

@router.get("/languages", response_model=List[LanguageResponse])
@limiter.limit("30/minute")
async def get_available_languages(request: Request):
    """
    Get list of available languages with file counts
    """
    try:
        languages = await audio_service.get_available_languages()
        return languages
    except Exception as e:
        logger.error(f"Error getting available languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available languages"
        )

@router.get("/{language}", response_model=AudioFileResponse)
@limiter.limit("60/minute")
async def get_audio_by_language(language: str, request: Request):
    """
    Get audio file URL for specific language
    
    - **language**: Language code (en, ar, english, arabic)
    """
    try:
        # Normalize language code
        normalized_lang = normalize_language_code(language)
        
        # Get audio file
        audio_file = await audio_service.get_audio_by_language(normalized_lang)
        
        if not audio_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No audio file found for language: {language}"
            )
        
        # Convert to response model
        return AudioFileResponse(
            id=str(audio_file.id),
            language=audio_file.language,
            filename=audio_file.filename,
            url=audio_file.url,
            file_size=audio_file.file_size,
            duration=audio_file.duration,
            format=audio_file.format,
            created_at=audio_file.created_at,
            updated_at=audio_file.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio for language {language}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audio file"
        )

@router.post("/upload", response_model=AudioUploadResponse)
@limiter.limit("10/minute")
async def upload_audio_file(
    request: Request,
    file: UploadFile = File(...),
    language: str = "en"
):
    """
    Upload a new audio file
    
    - **file**: Audio file to upload (mp3, wav, m4a)
    - **language**: Language code (en, ar, english, arabic)
    """
    try:
        # Validate file
        is_valid, error_message = validate_audio_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Normalize language code
        normalized_lang = normalize_language_code(language)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{normalized_lang}_{uuid.uuid4().hex}.{file_extension}"
        
        # Save file
        file_path = await save_uploaded_file(file, unique_filename)
        
        # Get file size
        file_size = get_file_size(file_path)
        
        # Generate URL
        file_url = generate_file_url(unique_filename)
        
        # Create audio file record
        audio_data = AudioFileCreate(
            language=normalized_lang,
            filename=unique_filename,
            url=file_url,
            file_size=file_size,
            format=file_extension
        )
        
        # Save to database
        audio_file = await audio_service.create_audio_file(audio_data)
        
        # Convert to response model
        audio_response = AudioFileResponse(
            id=str(audio_file.id),
            language=audio_file.language,
            filename=audio_file.filename,
            url=audio_file.url,
            file_size=audio_file.file_size,
            duration=audio_file.duration,
            format=audio_file.format,
            created_at=audio_file.created_at,
            updated_at=audio_file.updated_at
        )
        
        return AudioUploadResponse(
            message="Audio file uploaded successfully",
            audio_file=audio_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload audio file"
        )

@router.get("/files/{filename}")
async def serve_audio_file(filename: str):
    """
    Serve audio files for playback
    
    - **filename**: Name of the audio file to serve
    """
    try:
        file_path = os.path.join(settings.AUDIO_FILES_PATH, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )
        
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve audio file"
        )

@router.get("/", response_model=List[AudioFileResponse])
async def get_all_audio_files():
    """
    Get all audio files (admin endpoint)
    """
    try:
        audio_files = await audio_service.get_all_audio_files()
        
        return [
            AudioFileResponse(
                id=str(audio_file.id),
                language=audio_file.language,
                filename=audio_file.filename,
                url=audio_file.url,
                file_size=audio_file.file_size,
                duration=audio_file.duration,
                format=audio_file.format,
                created_at=audio_file.created_at,
                updated_at=audio_file.updated_at
            )
            for audio_file in audio_files
        ]
        
    except Exception as e:
        logger.error(f"Error getting all audio files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audio files"
        )

@router.delete("/{audio_id}")
async def delete_audio_file(audio_id: str):
    """
    Delete an audio file (admin endpoint)
    
    - **audio_id**: ID of the audio file to delete
    """
    try:
        # Get audio file first to get filename
        audio_file = await audio_service.get_audio_by_id(audio_id)
        
        if not audio_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )
        
        # Delete from database
        deleted = await audio_service.delete_audio_file(audio_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found"
            )
        
        # Delete physical file
        file_path = os.path.join(settings.AUDIO_FILES_PATH, audio_file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {"message": "Audio file deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting audio file {audio_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete audio file"
        )
