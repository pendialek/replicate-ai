from flask import Flask, jsonify, request, send_from_directory, render_template
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
import logging
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load configuration
app.config.update(
    REPLICATE_API_TOKEN=os.getenv('REPLICATE_API_TOKEN'),
    OPENAI_API_KEY=os.getenv('OPENAI_API_KEY'),
    IMAGE_STORAGE_PATH=os.path.join(os.path.dirname(__file__), 'images'),
    METADATA_STORAGE_PATH=os.path.join(os.path.dirname(__file__), 'metadata')
)

# Validate required environment variables
if not app.config['REPLICATE_API_TOKEN']:
    raise ValueError("REPLICATE_API_TOKEN environment variable is required")
if not app.config['OPENAI_API_KEY']:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Import API clients after environment variables are loaded
from api.replicate_client import ReplicateClient
from api.openai_client import OpenAIClient
from utils.storage import ImageManager, MetadataManager

# Initialize clients and managers
replicate_client = ReplicateClient(app.config['REPLICATE_API_TOKEN'])
openai_client = OpenAIClient(app.config['OPENAI_API_KEY'])
image_manager = ImageManager(app.config['IMAGE_STORAGE_PATH'])
metadata_manager = MetadataManager(app.config['METADATA_STORAGE_PATH'])

# Ensure storage directories exist
os.makedirs(app.config['IMAGE_STORAGE_PATH'], exist_ok=True)
os.makedirs(app.config['METADATA_STORAGE_PATH'], exist_ok=True)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """Generate image endpoint"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        model = data.get('model', 'flux-pro')
        aspect_ratio = data.get('aspect_ratio', '1:1')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Translate prompt to English
        translated_prompt = openai_client.translate_to_english(prompt)

        # Generate image using Replicate with translated prompt
        result = replicate_client.generate_image(translated_prompt, model, aspect_ratio)

        # Add original and translated prompts to metadata
        result['metadata']['original_prompt'] = prompt
        result['metadata']['translated_prompt'] = translated_prompt

        # Save image and metadata
        image_filename = image_manager.save_image_from_file(result['image_url'])
        metadata_filename = metadata_manager.save_metadata(image_filename, result['metadata'])

        return jsonify({
            'status': 'success',
            'image_id': os.path.splitext(image_filename)[0],
            'image_url': f'/images/{image_filename}'
        })

    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500