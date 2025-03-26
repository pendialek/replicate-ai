from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
import logging
import os
from logging.handlers import RotatingFileHandler

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger()
log_file = os.getenv('LOG_FILE', 'app.log')
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))

# Add file handler with rotation
file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=10)
file_handler.setFormatter(jsonlogger.JsonFormatter())
logger.addHandler(file_handler)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(jsonlogger.JsonFormatter())
logger.addHandler(console_handler)

logger.setLevel(log_level)

# Initialize Flask app
app = Flask(__name__,
    static_folder='static',
    template_folder='templates'
)

# Initialize CORS
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://'),
    default_limits=[os.getenv('RATELIMIT_DEFAULT', '30/hour')],
    strategy=os.getenv('RATELIMIT_STRATEGY', 'fixed-window')
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

# Custom error handlers
@app.errorhandler(400)
def bad_request_error(error):
    """Bad request error handler"""
    logger.warning(f"Bad request: {str(error)}")
    return jsonify({
        'error': 'Bad request',
        'message': str(error),
        'type': 'BadRequestError'
    }), 400

@app.errorhandler(404)
def not_found_error(error):
    """Not found error handler"""
    logger.warning(f"Not found: {str(error)}")
    return jsonify({
        'error': 'Not found',
        'message': str(error),
        'type': 'NotFoundError'
    }), 404

@app.errorhandler(429)
def ratelimit_error(error):
    """Rate limit exceeded error handler"""
    logger.warning(f"Rate limit exceeded: {str(error)}")
    return jsonify({
        'error': 'Too many requests',
        'message': 'Rate limit exceeded. Please try again later.',
        'type': 'RateLimitError'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    """Internal server error handler"""
    logger.error(f"Internal server error: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'type': 'InternalServerError'
    }), 500

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler for unhandled exceptions"""
    logger.error(f"Unhandled error occurred: {str(error)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred',
        'type': error.__class__.__name__
    }), getattr(error, 'code', 500)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
@limiter.limit("60/minute")
def health_check():
    """Basic health check endpoint"""
    return jsonify({'status': 'healthy'})

# Rate-limited endpoints
@app.route('/api/generate-image', methods=['POST'])
@limiter.limit("5/minute")
def generate_image():
    """Generate image endpoint with rate limiting"""
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

@app.route('/api/improve-prompt', methods=['POST'])
@limiter.limit("10/minute")
def improve_prompt():
    """Improve prompt endpoint with rate limiting"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        improved_prompt = openai_client.improve_prompt(prompt)
        return jsonify({'improved_prompt': improved_prompt})

    except Exception as e:
        logger.error(f"Error improving prompt: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/images', methods=['GET'])
@limiter.limit("30/minute")
def list_images():
    """List images with pagination and rate limiting"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        result = metadata_manager.list_images(page, per_page)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error listing images: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/metadata/<image_id>', methods=['GET'])
@limiter.limit("30/minute")
def get_metadata(image_id):
    """Get metadata for an image with rate limiting"""
    try:
        metadata = metadata_manager.get_metadata(f"{image_id}.json")
        if metadata is None:
            return jsonify({'error': 'Metadata not found'}), 404
        return jsonify(metadata)

    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/image/<image_id>', methods=['DELETE'])
@limiter.limit("10/minute")
def delete_image(image_id):
    """Delete image and its metadata with rate limiting"""
    try:
        image_filename = f"{image_id}.webp"
        metadata_filename = f"{image_id}.json"

        image_manager.delete_image(image_filename)
        metadata_manager.delete_metadata(metadata_filename)

        return jsonify({'status': 'success'})

    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
@limiter.limit("60/minute")
def serve_image(filename):
    """Serve image files with rate limiting"""
    return send_from_directory(app.config['IMAGE_STORAGE_PATH'], filename)

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Run the app
    app.run(
        host=host,
        port=port,
        debug=debug
    )