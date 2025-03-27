#!/bin/sh

# Check the first argument passed to the script
case "$1" in
  --production)
    echo "Running app.py in production mode using Gunicorn"
    # Ensure venv exists, although install should have created it
    if [ ! -d "venv" ]; then
        echo "Error: Virtual environment 'venv' not found. Run --install first."
        exit 1
    fi
    # Define default host and port
    DEFAULT_HOST="0.0.0.0"
    DEFAULT_PORT="8000"
    HOST=$DEFAULT_HOST
    PORT=$DEFAULT_PORT

    # Check if .env file exists and source it to load variables
    if [ -f ".env" ]; then
        echo "Loading environment variables from .env file"
        # Source the .env file - use '.' for POSIX compatibility
        # Use set -a/+a to export variables for the gunicorn process
        set -a
        . ./.env
        set +a

        # Override defaults if variables are set in .env
        if [ -n "$GUNICORN_HOST" ]; then
            HOST="$GUNICORN_HOST"
        fi
        if [ -n "$GUNICORN_PORT" ]; then
            PORT="$GUNICORN_PORT"
        fi
    else
        echo "No .env file found, using default host and port"
    fi

    BIND_ADDRESS="${HOST}:${PORT}"
    echo "Starting Gunicorn on $BIND_ADDRESS"

    # Run Gunicorn from the virtual environment
    # Assumes Flask app object is named 'app' in 'app.py'
    venv/bin/gunicorn --bind "$BIND_ADDRESS" app:app
    ;;
  --debug)
    echo "Running app.py in debug mode using Flask development server"
    # Ensure venv exists, create if not
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment 'venv'"
        python3 -m venv venv
        # Install requirements if venv was just created
        echo "Installing requirements..."
        venv/bin/pip install --upgrade pip
        venv/bin/pip install -r requirements.txt || { echo "Failed to install requirements"; exit 1; }
    fi

    # Set Flask environment to development for debug mode
    export FLASK_ENV=development
    # export FLASK_DEBUG=1 # Alternative or additional flag

    echo "Starting Flask development server..."
    # Run Flask development server from the virtual environment
    # It will typically bind to 127.0.0.1:5000 by default
    venv/bin/flask run
    ;;
  --install)
    echo "Install option selected"
    # Check if script is run as root
    if [ "$(id -u)" -ne 0 ]; then
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

    # Install/upgrade pip and install requirements using the venv's pip
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt

    # Verify key packages are installed correctly using the venv's python
    echo "Verifying installations..."
    venv/bin/python3 -c "import flask
import replicate
import openai
import redis
print('All key packages verified successfully!')" || {
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
    chmod +x app_run.sh

    # Start Redis server
    systemctl enable redis-server
    systemctl start redis-server

    echo "\n"
    echo "Installation completed successfully!"
    echo "Please configure your API keys in the .env file before running the application."
    echo "You can start the application by running: ./app_run.sh"
    ;;
  *)
    echo "Usage: $0 {--production|--debug|--install}"
    exit 1
    ;;
esac

exit 0
