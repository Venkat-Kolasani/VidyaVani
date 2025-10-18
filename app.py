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

# Import IVR handler
from src.ivr.ivr_handler import IVRHandler

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

# Initialize IVR handler
ivr_handler = IVRHandler(session_manager)

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
            'webhook_language': '/webhook/language-selection',
            'webhook_grade': '/webhook/grade-confirmation',
            'webhook_interaction': '/webhook/interaction-mode-selection',
            'webhook_recording': '/webhook/question-recording',
            'webhook_response': '/webhook/response-delivery',
            'webhook_followup': '/webhook/follow-up-menu',
            'webhook_callend': '/webhook/call-end',
            'demo_xml': '/demo/xml-responses',
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

# Exotel IVR Webhook Endpoints

@app.route('/webhook/incoming-call', methods=['POST'])
def webhook_incoming_call():
    """Handle incoming call webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Incoming call webhook: {request_data}")
        
        # Handle the call using IVR handler
        response = ivr_handler.handle_incoming_call(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in incoming call webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was a technical issue. Please try calling again.")

@app.route('/webhook/language-selection', methods=['POST'])
def webhook_language_selection():
    """Handle language selection webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Language selection webhook: {request_data}")
        
        # Handle language selection using IVR handler
        response = ivr_handler.handle_language_selection(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in language selection webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/grade-confirmation', methods=['POST'])
def webhook_grade_confirmation():
    """Handle grade confirmation webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Grade confirmation webhook: {request_data}")
        
        # Handle grade confirmation using IVR handler
        response = ivr_handler.handle_grade_confirmation(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in grade confirmation webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/interaction-mode', methods=['POST'])
def webhook_interaction_mode():
    """Redirect to interaction mode selection"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Interaction mode redirect webhook: {request_data}")
        
        # Handle grade confirmation (which redirects to interaction mode)
        response = ivr_handler.handle_grade_confirmation(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in interaction mode webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/interaction-mode-selection', methods=['POST'])
def webhook_interaction_mode_selection():
    """Handle interaction mode selection webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Interaction mode selection webhook: {request_data}")
        
        # Handle interaction mode selection using IVR handler
        response = ivr_handler.handle_interaction_mode_selection(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in interaction mode selection webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/question-recording', methods=['POST'])
def webhook_question_recording():
    """Handle question recording webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Question recording webhook: {request_data}")
        
        # Handle question recording using IVR handler
        response = ivr_handler.handle_question_recording(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in question recording webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error processing your question.")

@app.route('/webhook/recording-status', methods=['POST'])
def webhook_recording_status():
    """Handle recording status callback from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Recording status webhook: {request_data}")
        
        # This is just a status callback, no response needed
        return '', 200
        
    except Exception as e:
        logger.error(f"Error in recording status webhook: {str(e)}")
        return '', 500

@app.route('/webhook/response-delivery', methods=['POST'])
def webhook_response_delivery():
    """Handle response delivery webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Response delivery webhook: {request_data}")
        
        # Handle response delivery using IVR handler
        response = ivr_handler.handle_response_delivery(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in response delivery webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error delivering the response.")

@app.route('/webhook/follow-up-menu', methods=['POST'])
def webhook_follow_up_menu():
    """Handle follow-up menu selection webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Follow-up menu webhook: {request_data}")
        
        # Handle follow-up menu using IVR handler
        response = ivr_handler.handle_follow_up_menu(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in follow-up menu webhook: {str(e)}")
        return ivr_handler._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/call-end', methods=['POST'])
def webhook_call_end():
    """Handle call end webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Call end webhook: {request_data}")
        
        # Handle call end using IVR handler
        response = ivr_handler.handle_call_end(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in call end webhook: {str(e)}")
        return '', 500

# Demo XML Response Endpoint

@app.route('/demo/xml-responses', methods=['GET'])
def demo_xml_responses():
    """Demo endpoint to show XML response examples"""
    try:
        # Create a demo session for XML generation
        demo_phone = "+919999999999"
        session = session_manager.create_session(demo_phone)
        session_manager.update_session_language(demo_phone, 'english')
        
        examples = {
            'welcome': ivr_handler._generate_welcome_xml(),
            'grade_confirmation_english': ivr_handler._generate_grade_confirmation_xml('english'),
            'grade_confirmation_telugu': ivr_handler._generate_grade_confirmation_xml('telugu'),
            'interaction_mode_english': ivr_handler._generate_interaction_mode_xml('english'),
            'interaction_mode_telugu': ivr_handler._generate_interaction_mode_xml('telugu'),
            'question_recording_english': ivr_handler._generate_question_recording_xml('english'),
            'question_recording_telugu': ivr_handler._generate_question_recording_xml('telugu'),
            'processing_english': ivr_handler._generate_processing_xml('english'),
            'processing_telugu': ivr_handler._generate_processing_xml('telugu'),
            'response_delivery': ivr_handler._generate_response_delivery_xml('https://example.com/response.wav', 'english'),
            'invalid_selection': ivr_handler._generate_invalid_selection_xml('language', 'english'),
            'error_response': ivr_handler._generate_error_xml('This is a sample error message')
        }
        
        # Clean up demo session
        session_manager.cleanup_session(demo_phone)
        
        # Return as HTML for easy viewing
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>VidyaVani IVR XML Responses Demo</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .xml-example { margin: 20px 0; padding: 15px; border: 1px solid #ccc; background: #f9f9f9; }
                .xml-title { font-weight: bold; color: #333; margin-bottom: 10px; }
                pre { background: #fff; padding: 10px; border: 1px solid #ddd; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>VidyaVani IVR XML Responses Demo</h1>
            <p>This page shows example XML responses generated by the IVR system.</p>
        """
        
        for title, xml_content in examples.items():
            html_content += f"""
            <div class="xml-example">
                <div class="xml-title">{title.replace('_', ' ').title()}</div>
                <pre>{xml_content}</pre>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        logger.error(f"Error generating XML demo: {str(e)}")
        return jsonify({'error': 'Failed to generate XML demo'}), 500

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