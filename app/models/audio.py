from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
        raise ValueError("Invalid ObjectId")

class AudioFileBase(BaseModel):
    """Base model for audio file data"""
    language: str = Field(..., description="Language code (e.g., 'en', 'ar')")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    format: str = Field(..., description="Audio format (mp3, wav, m4a)")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        """Validate language code"""
        allowed_languages = ['en', 'ar', 'english', 'arabic']
        if v.lower() not in allowed_languages:
            raise ValueError(f"Language must be one of: {allowed_languages}")
        return v.lower()
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate audio format"""
        allowed_formats = ['mp3', 'wav', 'm4a', 'ogg']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Format must be one of: {allowed_formats}")
        return v.lower()

class AudioFileCreate(AudioFileBase):
    """Model for creating audio file"""
    url: str = Field(..., description="URL to access the audio file")

class AudioFileUpdate(BaseModel):
    """Model for updating audio file"""
    language: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    url: Optional[str] = None

class AudioFile(AudioFileBase):
    """Complete audio file model with database fields"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    url: str = Field(..., description="URL to access the audio file")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "language": "en",
                "filename": "sample_english.mp3",
                "file_size": 1024000,
                "duration": 30.5,
                "format": "mp3",
                "url": "http://localhost:8000/audio_files/sample_english.mp3",
                "created_at": "2023-12-09T10:00:00Z",
                "updated_at": "2023-12-09T10:00:00Z"
            }
        }
    }

class AudioFileResponse(BaseModel):
    """Response model for audio file"""
    id: str = Field(..., description="Audio file ID")
    language: str = Field(..., description="Language code")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="URL to access the audio file")
    file_size: int = Field(..., description="File size in bytes")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    format: str = Field(..., description="Audio format")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class LanguageResponse(BaseModel):
    """Response model for available languages"""
    language: str = Field(..., description="Language code")
    language_name: str = Field(..., description="Full language name")
    count: int = Field(..., description="Number of audio files for this language")

class AudioUploadResponse(BaseModel):
    """Response model for audio upload"""
    message: str = Field(..., description="Success message")
    audio_file: AudioFileResponse = Field(..., description="Uploaded audio file details")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
