"""
VidyaVani AI-Powered IVR Learning System
Main Flask application entry point
"""

import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime, timezone
import numpy as np

# Import configuration
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'VidyaVani IVR Learning System',
        'llm_model': os.environ.get('LLM_MODEL', 'gpt-5-nano'),
        'embedding_model': 'text-embedding-3-small',
        'timestamp': str(np.datetime64('now'))
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'VidyaVani AI-Powered IVR Learning System',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'webhook_incoming': '/webhook/incoming-call',
            'webhook_passthru': '/webhook/passthru',
            'api_docs': '/api/docs'
        }
    })

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Start the application
    logger.info("Starting VidyaVani IVR Learning System")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )