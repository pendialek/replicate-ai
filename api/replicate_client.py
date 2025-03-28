import replicate
import logging
import requests
from typing import Dict, Optional
from replicate.exceptions import ModelError
import base64
import tempfile
import os

logger = logging.getLogger(__name__)

class ReplicateClient:
    """Client for interacting with Replicate API"""
    
    SUPPORTED_MODELS = {
        'flux-pro': 'black-forest-labs/flux-pro',
        'flux-1.1-pro-ultra': 'black-forest-labs/flux-1.1-pro-ultra',
        'flux-1.1-pro': 'black-forest-labs/flux-1.1-pro',
        'flux-schnell-lora': 'black-forest-labs/flux-schnell-lora'
    }

    def __init__(self, api_token: str):
        """Initialize Replicate client with API token"""
        # API token is automatically loaded from REPLICATE_API_TOKEN env var

    def generate_image(self, prompt: str, model_key: str, aspect_ratio: str) -> Dict:
        """
        Generate image using specified model
        
        Args:
            prompt (str): Image generation prompt
            model_key (str): Key of the model to use
            aspect_ratio (str): Desired aspect ratio (e.g., '1:1', '16:9')
        
        Returns:
            Dict: Response containing image URL and metadata
        """
        if model_key not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model_key}")

        try:
            # Convert aspect ratio to dimensions
            width, height = self._get_dimensions(aspect_ratio)
            
            # Generate seed
            seed = self._generate_seed()
            
            # Log API parameters
            logger.info("Calling Replicate API with parameters", extra={
                "model": self.SUPPORTED_MODELS[model_key],
                "prompt": prompt,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "seed": seed
            })
            
            # Run the model
            output = replicate.run(
                self.SUPPORTED_MODELS[model_key],
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "seed": seed
                }
            )

            # Log the output for debugging
            logger.info(f"Model output: {output}")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webp', mode='wb') as temp_file:
                logger.info("Writing image data to file")
                # Process all chunks of output
                for chunk in output:
                    if not chunk:
                        continue
                    temp_file.write(chunk)
                temp_file.flush()
                
                # Return the path to the temporary file
                return {
                    'status': 'success',
                    'image_url': temp_file.name,
                    'metadata': {
                        'model': model_key,
                        'prompt': prompt,
                        'aspect_ratio': aspect_ratio,
                        'width': width,
                        'height': height
                    }
                }

        except ModelError as e:
            logger.error(f"Model error: {str(e)}", exc_info=True)
            if hasattr(e, 'prediction'):
                logger.error(f"Prediction ID: {e.prediction.id}")
                logger.error(f"Prediction logs: {e.prediction.logs}")
            raise
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            raise

    def _generate_seed(self) -> int:
        """Generate a random seed for image generation"""
        return int.from_bytes(os.urandom(4), byteorder='big') % 1000000000

    def _get_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        """Convert aspect ratio to pixel dimensions"""
        # Base dimension to maintain consistent image sizes
        base_dim = 1024
        
        ratios = {
            '1:1': (base_dim, base_dim),
            '16:9': (base_dim, int(base_dim * 9/16)),
            '3:2': (base_dim, int(base_dim * 2/3)),
            '2:3': (int(base_dim * 2/3), base_dim),
            '4:5': (int(base_dim * 4/5), base_dim),
            '5:4': (base_dim, int(base_dim * 4/5)),
            '9:16': (int(base_dim * 9/16), base_dim),
            '3:4': (int(base_dim * 3/4), base_dim),
            '4:3': (base_dim, int(base_dim * 3/4))
        }
        
        if aspect_ratio not in ratios:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
        return ratios[aspect_ratio]