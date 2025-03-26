#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

# Update package lists
apt-get update

# Install Python3, pip, and other required packages
apt-get install -y python3 python3-pip python3-venv redis-server

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verify key packages are installed correctly
echo "Verifying installations..."
python3 -c "
import flask
import replicate
import openai
import redis
print('All key packages verified successfully!')
" || {
    echo "Error: Some required packages failed to install correctly"
    exit 1
}

# Create necessary directories
mkdir -p images
mkdir -p metadata

# Setup .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Generate random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    # Replace placeholder with generated secret key
    sed -i "s/your_secret_key_here/$SECRET_KEY/" .env
    echo "Created .env file. Please update API keys in .env file:"
    echo "REPLICATE_API_TOKEN and OPENAI_API_KEY"
fi

# Set correct permissions
chown -R $SUDO_USER:$SUDO_USER .
chmod -R 755 .
chmod 600 .env

# Start Redis server
systemctl enable redis-server
systemctl start redis-server

echo "Installation completed successfully!"
echo "Please configure your API keys in the .env file before running the application."
echo "You can start the application with: source venv/bin/activate && python app.py"