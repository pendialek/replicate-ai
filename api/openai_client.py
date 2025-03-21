from openai import OpenAI
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI API"""

    def __init__(self, api_key: str):
        """Initialize OpenAI client with API key"""
        self.client = OpenAI(api_key=api_key)

    def improve_prompt(self, prompt: str) -> str:
        """
        Improve the image generation prompt using GPT-4
        
        Args:
            prompt (str): Original prompt to improve
            
        Returns:
            str: Improved prompt
        """
        try:
            system_message = """You are an expert at writing prompts for AI image generation.
            Your task is to enhance the given prompt to create more detailed and visually appealing images.
            Focus on:
            - Adding more descriptive details
            - Specifying art style and medium
            - Including lighting and atmosphere details
            - Maintaining the original intent
            Respond only with the enhanced prompt, no explanations."""

            completion = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Enhance this image prompt: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=200
            )

            improved_prompt = completion.choices[0].message.content.strip()
            
            logger.info(f"Improved prompt: {improved_prompt}")
            return improved_prompt

        except Exception as e:
            logger.error(f"Error improving prompt: {str(e)}", exc_info=True)
            raise