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

# Import session management
from src.session import session_manager

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
            'api_docs': '/api/docs',
            'session_stats': '/api/session/stats',
            'demo_questions': '/api/demo/questions'
        }
    })

# Session Management API Endpoints

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create new session for phone number"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({'error': 'phone_number is required'}), 400
        
        session = session_manager.create_session(phone_number)
        
        return jsonify({
            'success': True,
            'session_id': session.session_id,
            'phone_number': session.phone_number,
            'language': session.language,
            'current_menu': session.current_menu,
            'start_time': session.start_time.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({'error': 'Failed to create session'}), 500

@app.route('/api/session/<phone_number>', methods=['GET'])
def get_session(phone_number):
    """Get session by phone number"""
    try:
        session = session_manager.get_session(phone_number)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session.session_id,
            'phone_number': session.phone_number,
            'language': session.language,
            'current_menu': session.current_menu,
            'question_count': len(session.question_history),
            'response_count': len(session.response_history),
            'call_active': session.call_active,
            'start_time': session.start_time.isoformat(),
            'last_activity': session.last_activity.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        return jsonify({'error': 'Failed to get session'}), 500

@app.route('/api/session/<phone_number>/language', methods=['PUT'])
def update_session_language(phone_number):
    """Update session language"""
    try:
        data = request.get_json()
        language = data.get('language')
        
        if language not in ['english', 'telugu']:
            return jsonify({'error': 'Language must be english or telugu'}), 400
        
        success = session_manager.update_session_language(phone_number, language)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'language': language})
    
    except Exception as e:
        logger.error(f"Error updating session language: {str(e)}")
        return jsonify({'error': 'Failed to update language'}), 500

@app.route('/api/session/<phone_number>/menu', methods=['PUT'])
def update_session_menu(phone_number):
    """Update session menu state"""
    try:
        data = request.get_json()
        menu_state = data.get('menu_state')
        
        if not menu_state:
            return jsonify({'error': 'menu_state is required'}), 400
        
        success = session_manager.update_session_menu(phone_number, menu_state)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'menu_state': menu_state})
    
    except Exception as e:
        logger.error(f"Error updating session menu: {str(e)}")
        return jsonify({'error': 'Failed to update menu state'}), 500

@app.route('/api/session/<phone_number>/question', methods=['POST'])
def add_question_to_session(phone_number):
    """Add question to session history"""
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        success = session_manager.add_question_to_session(phone_number, question)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'question': question})
    
    except Exception as e:
        logger.error(f"Error adding question to session: {str(e)}")
        return jsonify({'error': 'Failed to add question'}), 500

@app.route('/api/session/<phone_number>/response', methods=['POST'])
def add_response_to_session(phone_number):
    """Add response to session history"""
    try:
        data = request.get_json()
        response = data.get('response')
        
        if not response:
            return jsonify({'error': 'response is required'}), 400
        
        success = session_manager.add_response_to_session(phone_number, response)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'response': response})
    
    except Exception as e:
        logger.error(f"Error adding response to session: {str(e)}")
        return jsonify({'error': 'Failed to add response'}), 500

@app.route('/api/session/<phone_number>/context', methods=['GET'])
def get_conversation_context(phone_number):
    """Get conversation context for RAG engine"""
    try:
        context = session_manager.get_conversation_context(phone_number)
        
        return jsonify({
            'phone_number': phone_number,
            'context': context
        })
    
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        return jsonify({'error': 'Failed to get context'}), 500

@app.route('/api/session/<phone_number>/end', methods=['POST'])
def end_session(phone_number):
    """End session when call ends"""
    try:
        success = session_manager.end_session(phone_number)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'message': 'Session ended'})
    
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        return jsonify({'error': 'Failed to end session'}), 500

@app.route('/api/session/<phone_number>/cleanup', methods=['DELETE'])
def cleanup_session(phone_number):
    """Remove session from memory"""
    try:
        success = session_manager.cleanup_session(phone_number)
        
        if not success:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({'success': True, 'message': 'Session cleaned up'})
    
    except Exception as e:
        logger.error(f"Error cleaning up session: {str(e)}")
        return jsonify({'error': 'Failed to cleanup session'}), 500

@app.route('/api/session/stats', methods=['GET'])
def get_session_stats():
    """Get session statistics"""
    try:
        stats = session_manager.get_session_stats()
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500

# Demo Question Cache API Endpoints

@app.route('/api/demo/questions', methods=['GET'])
def get_demo_questions():
    """Get list of demo questions"""
    try:
        questions = session_manager.get_demo_questions()
        return jsonify({
            'demo_questions': questions,
            'count': len(questions)
        })
    
    except Exception as e:
        logger.error(f"Error getting demo questions: {str(e)}")
        return jsonify({'error': 'Failed to get demo questions'}), 500

@app.route('/api/demo/response', methods=['POST'])
def get_demo_response():
    """Get cached response for demo question"""
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        response = session_manager.get_cached_demo_response(question)
        
        if response:
            return jsonify({
                'question': question,
                'response': response,
                'cached': True
            })
        else:
            return jsonify({
                'question': question,
                'response': None,
                'cached': False,
                'message': 'No cached response found'
            })
    
    except Exception as e:
        logger.error(f"Error getting demo response: {str(e)}")
        return jsonify({'error': 'Failed to get demo response'}), 500

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