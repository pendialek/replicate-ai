import json
import os
import uuid
import logging
from typing import Dict, List, Optional
import requests
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class FileManager:
    """Base class for file management"""
    
    def __init__(self, storage_path: str):
        """Initialize with storage path"""
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def _generate_filename(self, extension: str) -> str:
        """Generate unique filename using UUID"""
        return f"{uuid.uuid4()}.{extension}"

    def _get_full_path(self, filename: str) -> str:
        """Get full path for a file"""
        return os.path.join(self.storage_path, filename)

class ImageManager(FileManager):
    """Manager for handling image files"""
    
    def __init__(self, storage_path: str):
        """Initialize image manager"""
        super().__init__(storage_path)

    def save_image_from_file(self, source_path: str) -> str:
        """
        Save image from a local file
        
        Args:
            source_path (str): Path to the source image file
            
        Returns:
            str: Filename of saved image
        """
        try:
            filename = self._generate_filename('webp')
            dest_path = self._get_full_path(filename)
            
            # Copy the file using binary mode
            with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
                dst.write(src.read())
            
            # Remove the temporary file
            os.unlink(source_path)
                    
            logger.info(f"Saved image: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving image from file: {str(e)}", exc_info=True)
            raise

    def delete_image(self, filename: str) -> None:
        """Delete image file"""
        try:
            full_path = self._get_full_path(filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Deleted image: {filename}")
            else:
                logger.warning(f"Image not found: {filename}")
                
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}", exc_info=True)
            raise

class MetadataManager(FileManager):
    """Manager for handling metadata files"""
    
    def __init__(self, storage_path: str):
        """Initialize metadata manager"""
        super().__init__(storage_path)

    def save_metadata(self, image_filename: str, metadata: Dict) -> str:
        """
        Save metadata for an image
        
        Args:
            image_filename (str): Filename of the associated image
            metadata (Dict): Metadata to save
            
        Returns:
            str: Filename of saved metadata
        """
        try:
            # Use same UUID as image but with json extension
            filename = f"{os.path.splitext(image_filename)[0]}.json"
            full_path = self._get_full_path(filename)
            
            # Add timestamp to metadata
            metadata['timestamp'] = datetime.utcnow().isoformat()
            metadata['image_filename'] = image_filename
            
            with open(full_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Saved metadata: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}", exc_info=True)
            raise

    def get_metadata(self, filename: str) -> Optional[Dict]:
        """Get metadata for a file"""
        try:
            full_path = self._get_full_path(filename)
            if not os.path.exists(full_path):
                return None
                
            with open(full_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading metadata: {str(e)}", exc_info=True)
            raise

    def delete_metadata(self, filename: str) -> None:
        """Delete metadata file"""
        try:
            full_path = self._get_full_path(filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Deleted metadata: {filename}")
            else:
                logger.warning(f"Metadata not found: {filename}")
                
        except Exception as e:
            logger.error(f"Error deleting metadata: {str(e)}", exc_info=True)
            raise

    def list_images(self, page: int = 1, per_page: int = 12) -> Dict[str, any]:
        """
        List all images with their metadata, paginated
        
        Args:
            page (int): Page number (1-based)
            per_page (int): Number of items per page
            
        Returns:
            Dict containing:
                images: List of image metadata
                total_pages: Total number of pages
        """
        try:
            # Get all metadata files
            metadata_files = [f for f in os.listdir(self.storage_path) 
                            if f.endswith('.json')]
            metadata_files.sort(key=lambda x: os.path.getmtime(self._get_full_path(x)), 
                              reverse=True)
            
            # Calculate pagination
            total_items = len(metadata_files)
            total_pages = (total_items + per_page - 1) // per_page
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            # Get metadata for current page
            page_files = metadata_files[start_idx:end_idx]
            images = []
            
            for filename in page_files:
                metadata = self.get_metadata(filename)
                if metadata:
                    images.append(metadata)
            
            return {
                'images': images,
                'total_pages': total_pages
            }
            
        except Exception as e:
            logger.error(f"Error listing images: {str(e)}", exc_info=True)
            raise