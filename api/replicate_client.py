import replicate
import logging
from typing import Dict, Optional

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
        self.client = replicate.Client(api_token=api_token)

    def generate_image(self, prompt: str, model_key: str, aspect_ratio: str) -> Dict:
        """
        Generate image using specified model
        
        Args:
            prompt (str): Image generation prompt
            model_key (str): Key of the model to use
            aspect_ratio (str): Desired aspect ratio (e.g., '1:1', '16:9')
        
        Returns:
            Dict: Response from the API containing image URL and metadata
        """
        if model_key not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model_key}")

        try:
            # Convert aspect ratio to dimensions
            width, height = self._get_dimensions(aspect_ratio)
            
            # Get the model
            model = self.client.models.get(self.SUPPORTED_MODELS[model_key])
            
            # Start the prediction
            prediction = model.predict(
                prompt=prompt,
                width=width,
                height=height
            )

            return {
                'status': 'success',
                'image_url': prediction[0],  # First output is typically the image URL
                'metadata': {
                    'model': model_key,
                    'prompt': prompt,
                    'aspect_ratio': aspect_ratio,
                    'width': width,
                    'height': height
                }
            }

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            raise

    def _get_dimensions(self, aspect_ratio: str) -> tuple[int, int]:
        """Convert aspect ratio to pixel dimensions"""
        ratios = {
            '1:1': (1024, 1024),
            '4:3': (1024, 768),
            '16:9': (1024, 576),
            '21:9': (1024, 439)
        }
        
        if aspect_ratio not in ratios:
            raise ValueError(f"Unsupported aspect ratio: {aspect_ratio}")
            
        return ratios[aspect_ratio]