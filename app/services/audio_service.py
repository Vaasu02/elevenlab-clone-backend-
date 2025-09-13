from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.database import get_database
from app.models.audio import AudioFile, AudioFileCreate, AudioFileUpdate, LanguageResponse
import logging

logger = logging.getLogger(__name__)

class AudioService:
    """Service class for audio file operations"""
    
    def __init__(self):
        self.collection_name = "audio_files"
    
    async def get_collection(self):
        """Get the audio files collection"""
        database = await get_database()
        return database[self.collection_name]
    
    async def create_audio_file(self, audio_data: AudioFileCreate) -> AudioFile:
        """Create a new audio file record"""
        try:
            collection = await self.get_collection()
            
            # Create audio file document
            audio_doc = {
                "language": audio_data.language,
                "filename": audio_data.filename,
                "url": audio_data.url,
                "file_size": audio_data.file_size,
                "duration": audio_data.duration,
                "format": audio_data.format,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert document
            result = await collection.insert_one(audio_doc)
            
            # Fetch and return the created document
            created_doc = await collection.find_one({"_id": result.inserted_id})
            return AudioFile(**created_doc)
            
        except Exception as e:
            logger.error(f"Error creating audio file: {e}")
            raise e
    
    async def get_audio_by_language(self, language: str) -> Optional[AudioFile]:
        """Get audio file by language"""
        try:
            collection = await self.get_collection()
            
            # Normalize language code
            lang_code = language.lower()
            if lang_code in ['english', 'en']:
                lang_code = 'en'
            elif lang_code in ['arabic', 'ar']:
                lang_code = 'ar'
            
            # Find audio file by language
            audio_doc = await collection.find_one({"language": lang_code})
            
            if audio_doc:
                return AudioFile(**audio_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio by language {language}: {e}")
            raise e
    
    async def get_all_audio_files(self) -> List[AudioFile]:
        """Get all audio files"""
        try:
            collection = await self.get_collection()
            audio_docs = await collection.find().to_list(length=None)
            
            return [AudioFile(**doc) for doc in audio_docs]
            
        except Exception as e:
            logger.error(f"Error getting all audio files: {e}")
            raise e
    
    async def get_available_languages(self) -> List[LanguageResponse]:
        """Get list of available languages with file counts"""
        try:
            collection = await self.get_collection()
            
            # Aggregate to get language counts
            pipeline = [
                {
                    "$group": {
                        "_id": "$language",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            results = await collection.aggregate(pipeline).to_list(length=None)
            
            # Map language codes to full names
            language_names = {
                'en': 'English',
                'ar': 'Arabic'
            }
            
            languages = []
            for result in results:
                lang_code = result['_id']
                lang_name = language_names.get(lang_code, lang_code.title())
                
                languages.append(LanguageResponse(
                    language=lang_code,
                    language_name=lang_name,
                    count=result['count']
                ))
            
            return languages
            
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            raise e
    
    async def update_audio_file(self, audio_id: str, update_data: AudioFileUpdate) -> Optional[AudioFile]:
        """Update an audio file"""
        try:
            collection = await self.get_collection()
            
            # Prepare update document
            update_doc = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_doc["updated_at"] = datetime.utcnow()
            
            # Update document
            result = await collection.update_one(
                {"_id": ObjectId(audio_id)},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                # Fetch and return updated document
                updated_doc = await collection.find_one({"_id": ObjectId(audio_id)})
                return AudioFile(**updated_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating audio file {audio_id}: {e}")
            raise e
    
    async def delete_audio_file(self, audio_id: str) -> bool:
        """Delete an audio file"""
        try:
            collection = await self.get_collection()
            
            result = await collection.delete_one({"_id": ObjectId(audio_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting audio file {audio_id}: {e}")
            raise e
    
    async def get_audio_by_id(self, audio_id: str) -> Optional[AudioFile]:
        """Get audio file by ID"""
        try:
            collection = await self.get_collection()
            
            audio_doc = await collection.find_one({"_id": ObjectId(audio_id)})
            
            if audio_doc:
                return AudioFile(**audio_doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio file by ID {audio_id}: {e}")
            raise e

# Create service instance
audio_service = AudioService()
