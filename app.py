from flask import Flask, jsonify, request, send_from_directory, render_template
from pythonjsonlogger import jsonlogger
import logging
import os
from api.replicate_client import ReplicateClient
from api.openai_client import OpenAIClient
from utils.storage import ImageManager, MetadataManager

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

        # Generate image using Replicate
        result = replicate_client.generate_image(prompt, model, aspect_ratio)

        # Save image and metadata
        image_filename = image_manager.save_image_from_url(result['image_url'])
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
def improve_prompt():
    """Improve prompt using GPT-4"""
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
def list_images():
    """List images with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        result = metadata_manager.list_images(page, per_page)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error listing images: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/metadata/<image_id>', methods=['GET'])
def get_metadata(image_id):
    """Get metadata for an image"""
    try:
        metadata = metadata_manager.get_metadata(f"{image_id}.json")
        if metadata is None:
            return jsonify({'error': 'Metadata not found'}), 404
        return jsonify(metadata)

    except Exception as e:
        logger.error(f"Error getting metadata: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/image/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image and its metadata"""
    try:
        image_filename = f"{image_id}.png"
        metadata_filename = f"{image_id}.json"

        image_manager.delete_image(image_filename)
        metadata_manager.delete_metadata(metadata_filename)

        return jsonify({'status': 'success'})

    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/images/<filename>')
def serve_image(filename):
    """Serve image files"""
    return send_from_directory(app.config['IMAGE_STORAGE_PATH'], filename)

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    return jsonify({
        'error': str(error),
        'type': error.__class__.__name__
    }), getattr(error, 'code', 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)