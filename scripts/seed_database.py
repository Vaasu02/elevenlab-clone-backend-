"""
Script to seed the database with sample audio files
Run this script to add sample audio files for testing
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.database import connect_to_mongo, close_mongo_connection
from app.services.audio_service import audio_service
from app.models.audio import AudioFileCreate
from app.config import settings

async def seed_database():
    """Seed the database with sample audio files"""
    try:
        # Connect to database
        await connect_to_mongo()
        print("Connected to MongoDB")
        
        # Create audio_files directory if it doesn't exist
        os.makedirs(settings.AUDIO_FILES_PATH, exist_ok=True)
        
        # Sample audio files data with deployed backend URLs
        sample_files = [
            {
                "language": "en",
                "filename": "sample_english.mp3",
                "url": "https://elevenlab-clone-backend.vercel.app/api/audio/files/sample_english.mp3",
                "file_size": 1024000,  # 1MB
                "duration": 30.5,
                "format": "mp3"
            },
            {
                "language": "ar",
                "filename": "sample_arabic.mp3",
                "url": "https://elevenlab-clone-backend.vercel.app/api/audio/files/sample_arabic.mp3",
                "file_size": 1200000,  # 1.2MB
                "duration": 35.2,
                "format": "mp3"
            }
        ]
        
        # Create sample audio files
        for file_data in sample_files:
            try:
                # Check if file already exists
                existing_file = await audio_service.get_audio_by_language(file_data["language"])
                if existing_file:
                    print(f"Audio file for language {file_data['language']} already exists, skipping...")
                    continue
                
                # Create audio file record
                audio_data = AudioFileCreate(**file_data)
                audio_file = await audio_service.create_audio_file(audio_data)
                
                print(f"Created audio file: {audio_file.filename} for language {audio_file.language}")
                
            except Exception as e:
                print(f"Error creating audio file for {file_data['language']}: {e}")
        
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        # Close database connection
        await close_mongo_connection()
        print("Disconnected from MongoDB")

if __name__ == "__main__":
    asyncio.run(seed_database())
