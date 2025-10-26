"""
VidyaVani AI-Powered IVR Learning System
Main Flask application entry point
"""

import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timezone
import numpy as np

# Import configuration
from config import Config

# Import session management
from src.session import session_manager

# Import IVR handler
from src.ivr.ivr_handler import IVRHandler

# Import audio storage
from src.storage.audio_storage import register_audio_routes

# Import performance tracking and error tracking
from src.utils.performance_tracker import performance_tracker
from src.utils.error_tracker import error_tracker
from src.utils.logging_config import setup_logging
from src.utils.call_recorder import call_recorder

# Import production utilities
from src.utils.production_logger import setup_request_logging
from src.utils.health_monitor import get_health_monitor
from src.utils.backup_manager import get_backup_manager
from src.utils.load_balancer import setup_load_balancing

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Setup Google Cloud credentials
Config.setup_google_credentials()

# Configure logging with performance tracking
setup_logging()
logger = logging.getLogger(__name__)

# Setup production logging and monitoring
if Config.IS_PRODUCTION:
    logger.info("Setting up production environment...")
    
    # Setup request logging
    prod_logger = setup_request_logging(app, Config)
    
    # Setup health monitoring
    health_monitor = get_health_monitor(Config)
    health_monitor.start_monitoring(interval=60)  # Check every minute
    
    # Setup backup manager
    backup_manager = get_backup_manager(Config)
    backup_manager.start_auto_backup()
    
    # Setup load balancing
    load_balancer = setup_load_balancing(app, Config)
    
    logger.info("Production environment setup completed")

# Initialize IVR handler lazily to avoid blocking startup
ivr_handler = None

def get_ivr_handler():
    """Get IVR handler instance (lazy initialization)"""
    global ivr_handler
    if ivr_handler is None:
        ivr_handler = IVRHandler(session_manager)
    return ivr_handler

# Register audio serving routes
register_audio_routes(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'VidyaVani IVR Learning System'
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """Detailed health check endpoint"""
    try:
        # Import health monitor
        from src.utils.health_monitor import get_health_monitor
        health_monitor = get_health_monitor(Config)
        
        # Perform quick health check
        health_status = health_monitor.perform_health_check()
        
        return jsonify({
            'status': health_status.overall_status,
            'service': 'VidyaVani IVR Learning System',
            'llm_model': os.environ.get('LLM_MODEL', 'gpt-5-nano'),
            'embedding_model': 'text-embedding-3-small',
            'timestamp': str(np.datetime64('now')),
            'components': {
                'healthy': health_status.healthy_components,
                'warning': health_status.warning_components,
                'critical': health_status.critical_components
            },
            'deployment': Config.get_deployment_info()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'service': 'VidyaVani IVR Learning System',
            'error': str(e),
            'timestamp': str(np.datetime64('now'))
        }), 500

@app.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check endpoint"""
    try:
        from src.utils.health_monitor import get_health_monitor
        health_monitor = get_health_monitor(Config)
        
        health_status = health_monitor.get_health_status()
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health/history', methods=['GET'])
def health_history():
    """Health check history endpoint"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        from src.utils.health_monitor import get_health_monitor
        health_monitor = get_health_monitor(Config)
        
        history = health_monitor.get_health_history(hours)
        return jsonify({
            'history': history,
            'hours': hours,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Health history failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health/restart', methods=['POST'])
def manual_restart():
    """Manual system restart endpoint (admin only)"""
    try:
        # Basic authentication check (in production, use proper auth)
        auth_key = request.headers.get('X-Admin-Key')
        if auth_key != os.getenv('ADMIN_RESTART_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        from src.utils.health_monitor import get_health_monitor
        health_monitor = get_health_monitor(Config)
        
        success = health_monitor.restart_system()
        
        if success:
            return jsonify({'message': 'System restart initiated'})
        else:
            return jsonify({'error': 'Restart failed'}), 500
            
    except Exception as e:
        logger.error(f"Manual restart failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - Serve the main frontend"""
    try:
        # Try to serve the new frontend first
        from flask import send_from_directory
        return send_from_directory('frontend', 'index.html')
    except:
        # Fallback to API info
        return jsonify({
            'message': 'VidyaVani AI-Powered IVR Learning System',
            'status': 'running',
            'frontend': '/app',
            'endpoints': {
                'health': '/health',
                'webhook_incoming': '/webhook/incoming-call',
                'webhook_language': '/webhook/language-selection',
                'webhook_grade': '/webhook/grade-confirmation',
                'webhook_interaction': '/webhook/interaction-mode-selection',
                'webhook_recording': '/webhook/question-recording',
                'webhook_response': '/webhook/response-delivery',
                'webhook_followup': '/webhook/follow-up-menu',
                'webhook_error_recovery': '/webhook/error-recovery',
                'webhook_callend': '/webhook/call-end',
                'api_process_question': '/api/process-question',
                'api_processing_status': '/api/processing-status/<phone_number>',
                'demo_xml': '/demo/xml-responses',
                'api_docs': '/api/docs',
                'session_stats': '/api/session/stats',
                'demo_questions': '/api/demo/questions',
                'performance_metrics': '/api/performance/metrics',
                'performance_dashboard': '/api/performance/dashboard',
                'performance_components': '/api/performance/components',
                'performance_api_usage': '/api/performance/api-usage',
                'performance_cache': '/api/performance/cache',
                'performance_alerts': '/api/performance/alerts',
                'error_summary': '/api/errors/summary',
                'debugging_report': '/api/errors/debugging-report',
                'dashboard_page': '/dashboard',
                'demo_simulator': '/demo/simulator',
                'processing_dashboard': '/demo/processing-dashboard',
                'call_recordings': '/api/demo/recordings',
                'demo_summary': '/api/demo/summary'
            }
        })

@app.route('/app', methods=['GET'])
def frontend_app():
    """Serve the main frontend application"""
    try:
        with open('frontend/index.html', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        return f"<h1>Frontend Error</h1><p>Could not load frontend: {str(e)}</p>", 500

@app.route('/frontend/<path:filename>', methods=['GET'])
def serve_frontend_files(filename):
    """Serve frontend static files"""
    try:
        from flask import send_from_directory
        return send_from_directory('frontend', filename)
    except Exception as e:
        logger.error(f"Error serving frontend file {filename}: {str(e)}")
        return f"File not found: {filename}", 404

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
    request_data = {}  # Initialize to prevent UnboundLocalError
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Incoming call webhook: {request_data}")
        
        # Handle the call using IVR handler
        response = get_ivr_handler().handle_incoming_call(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in incoming call webhook: {str(e)}")
        error_tracker.track_error('Exotel_Incoming_Call', e, 
                                 phone_number=request_data.get('From', 'unknown'),
                                 recovery_action='Generated error XML response')
        return get_ivr_handler()._generate_error_xml("Sorry, there was a technical issue. Please try calling again.")

@app.route('/webhook/language-selection', methods=['POST'])
def webhook_language_selection():
    """Handle language selection webhook from Exotel"""
    request_data = {}  # Initialize to prevent UnboundLocalError
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Language selection webhook: {request_data}")
        
        # Handle language selection using IVR handler
        response = get_ivr_handler().handle_language_selection(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in language selection webhook: {str(e)}")
        error_tracker.track_error('Exotel_Language_Selection', e,
                                 phone_number=request_data.get('From', 'unknown'),
                                 recovery_action='Generated error XML response')
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/grade-confirmation', methods=['POST'])
def webhook_grade_confirmation():
    """Handle grade confirmation webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Grade confirmation webhook: {request_data}")
        
        # Handle grade confirmation using IVR handler
        response = get_ivr_handler().handle_grade_confirmation(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in grade confirmation webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/interaction-mode', methods=['POST'])
def webhook_interaction_mode():
    """Redirect to interaction mode selection"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Interaction mode redirect webhook: {request_data}")
        
        # Handle grade confirmation (which redirects to interaction mode)
        response = get_ivr_handler().handle_grade_confirmation(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in interaction mode webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/interaction-mode-selection', methods=['POST'])
def webhook_interaction_mode_selection():
    """Handle interaction mode selection webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Interaction mode selection webhook: {request_data}")
        
        # Handle interaction mode selection using IVR handler
        response = get_ivr_handler().handle_interaction_mode_selection(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in interaction mode selection webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/question-recording', methods=['POST'])
def webhook_question_recording():
    """Handle question recording webhook from Exotel"""
    request_data = {}  # Initialize to prevent UnboundLocalError
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Question recording webhook: {request_data}")
        
        # Handle question recording using IVR handler
        response = get_ivr_handler().handle_question_recording(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in question recording webhook: {str(e)}")
        error_tracker.track_error('Exotel_Question_Recording', e,
                                 phone_number=request_data.get('From', 'unknown'),
                                 recovery_action='Generated error XML response')
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error processing your question.")

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
        response = get_ivr_handler().handle_response_delivery(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in response delivery webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error delivering the response.")

@app.route('/webhook/follow-up-menu', methods=['POST'])
def webhook_follow_up_menu():
    """Handle follow-up menu selection webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Follow-up menu webhook: {request_data}")
        
        # Handle follow-up menu using IVR handler
        response = get_ivr_handler().handle_follow_up_menu(request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in follow-up menu webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try again.")

@app.route('/webhook/error-recovery', methods=['POST'])
def webhook_error_recovery():
    """Handle error recovery menu selection"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Error recovery webhook: {request_data}")
        
        from_number = request_data.get('From', '')
        digits = request_data.get('Digits', '')
        
        # Get session
        session = session_manager.get_session(from_number)
        if not session:
            return get_ivr_handler()._generate_error_xml("Session not found. Please call again.")
        
        if digits == '1':  # Try asking again
            # Reset to question recording
            session_manager.update_session_menu(from_number, get_ivr_handler().MENU_STATES['recording_question'])
            xml_response = get_ivr_handler()._generate_question_recording_xml(session.language)
            return Response(xml_response, mimetype='application/xml')
        
        elif digits == '9':  # Main menu
            # Reset to interaction mode
            session_manager.update_session_menu(from_number, get_ivr_handler().MENU_STATES['interaction_mode'])
            xml_response = get_ivr_handler()._generate_interaction_mode_xml(session.language)
            return Response(xml_response, mimetype='application/xml')
        
        else:
            # Invalid selection, redirect to interaction mode
            session_manager.update_session_menu(from_number, get_ivr_handler().MENU_STATES['interaction_mode'])
            xml_response = get_ivr_handler()._generate_interaction_mode_xml(session.language)
            return Response(xml_response, mimetype='application/xml')
        
    except Exception as e:
        logger.error(f"Error in error recovery webhook: {str(e)}")
        return get_ivr_handler()._generate_error_xml("Sorry, there was an error. Please try calling again.")

@app.route('/webhook/call-end', methods=['POST'])
def webhook_call_end():
    """Handle call end webhook from Exotel"""
    try:
        # Get request data from Exotel
        request_data = request.form.to_dict() if request.form else request.get_json() or {}
        
        logger.info(f"Call end webhook: {request_data}")
        
        # Handle call end using IVR handler
        response = get_ivr_handler().handle_call_end(request_data)
        
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
            'welcome': get_ivr_handler()._generate_welcome_xml(),
            'grade_confirmation_english': get_ivr_handler()._generate_grade_confirmation_xml('english'),
            'grade_confirmation_telugu': get_ivr_handler()._generate_grade_confirmation_xml('telugu'),
            'interaction_mode_english': get_ivr_handler()._generate_interaction_mode_xml('english'),
            'interaction_mode_telugu': get_ivr_handler()._generate_interaction_mode_xml('telugu'),
            'question_recording_english': get_ivr_handler()._generate_question_recording_xml('english'),
            'question_recording_telugu': get_ivr_handler()._generate_question_recording_xml('telugu'),
            'processing_english': get_ivr_handler()._generate_processing_xml('english'),
            'processing_telugu': get_ivr_handler()._generate_processing_xml('telugu'),
            'response_delivery': get_ivr_handler()._generate_response_delivery_xml('https://example.com/response.wav', 'english'),
            'invalid_selection': get_ivr_handler()._generate_invalid_selection_xml('language', 'english'),
            'error_response': get_ivr_handler()._generate_error_xml('This is a sample error message')
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

# Question Processing API Endpoints

@app.route('/api/process-question', methods=['POST'])
def process_question():
    """Process question asynchronously and return result"""
    # Initialize variables to prevent UnboundLocalError
    session_id = None
    phone_number = None
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        audio_url = data.get('audio_url')
        language = data.get('language', 'english')
        phone_number = data.get('phone_number')
        
        if not all([session_id, audio_url, phone_number]):
            return jsonify({
                'error': 'session_id, audio_url, and phone_number are required'
            }), 400
        
        # Validate language
        if language not in ['english', 'telugu']:
            return jsonify({'error': 'Language must be english or telugu'}), 400
        
        # Get or create session
        session = session_manager.get_or_create_session(phone_number)
        
        # Update processing status
        session_manager.update_processing_status(phone_number, 'processing_audio')
        
        # Process question synchronously (for demo simplicity)
        from src.ivr.processing_pipeline import IVRProcessingPipeline
        pipeline = IVRProcessingPipeline(Config())
        
        result = pipeline.process_question_sync(audio_url, language, phone_number)
        
        if result.success:
            # Store response data in session
            from src.session.session_manager import ResponseData
            response_data = ResponseData(
                question_text=result.question_text,
                response_text=result.response_text,
                response_audio_url=result.response_audio_url,
                detailed_response_text=result.detailed_response_text,
                detailed_audio_url=result.detailed_audio_url,
                language=language
            )
            
            session_manager.store_response_data(phone_number, response_data)
            session_manager.update_processing_status(phone_number, 'ready')
            
            # Add to session history
            session_manager.add_question_to_session(phone_number, result.question_text)
            session_manager.add_response_to_session(phone_number, result.response_text)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'question_text': result.question_text,
                'response_text': result.response_text,
                'response_audio_url': result.response_audio_url,
                'detailed_response_text': result.detailed_response_text,
                'detailed_audio_url': result.detailed_audio_url,
                'processing_time': result.processing_time
            })
        else:
            session_manager.update_processing_status(phone_number, 'error')
            return jsonify({
                'success': False,
                'session_id': session_id,
                'error_message': result.error_message,
                'processing_time': result.processing_time
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        error_tracker.track_error('Question_Processing', e,
                                 session_id=session_id,
                                 phone_number=phone_number,
                                 recovery_action='Returned error response to client')
        return jsonify({'error': 'Failed to process question'}), 500

@app.route('/api/processing-status/<phone_number>', methods=['GET'])
def get_processing_status(phone_number):
    """Get current processing status for a session"""
    try:
        session = session_manager.get_session(phone_number)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        response_data = session_manager.get_current_response_data(phone_number)
        
        return jsonify({
            'phone_number': phone_number,
            'processing_status': session.processing_status,
            'has_response': response_data is not None,
            'response_ready': session.processing_status == 'ready' and response_data is not None,
            'last_activity': session.last_activity.isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        return jsonify({'error': 'Failed to get processing status'}), 500

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

@app.route('/api/answer-question', methods=['POST'])
def answer_question():
    """Answer question using RAG + Gemini AI (text-based, no audio)"""
    try:
        data = request.get_json()
        question = data.get('question')
        language = data.get('language', 'english')
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        logger.info(f"Processing text question: {question}")
        
        # Import RAG components
        from src.rag.context_builder import ContextBuilder
        from src.rag.response_generator import ResponseGenerator
        
        # Initialize components
        context_builder = ContextBuilder(Config())
        response_generator = ResponseGenerator(Config())
        
        # Step 1 & 2: Build context (includes semantic search)
        context = context_builder.build_context(
            question=question,
            language=language.capitalize(),
            detail_level='simple',
            subject_filter='science'
        )
        
        sources_count = len(context.get('search_results', {}).get('results', []))
        logger.info(f"Context built with {sources_count} passages")
        
        # Step 3: Generate response using Gemini
        response_data = response_generator.generate_response(context)
        
        if response_data.get('success'):
            return jsonify({
                'success': True,
                'question': question,
                'response': response_data.get('response_text', ''),
                'detailed_response': response_data.get('detailed_response', ''),
                'sources_used': sources_count,
                'language': language,
                'method': 'rag' if sources_count > 0 else 'gemini_direct'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate response',
                'message': response_data.get('error', 'Unknown error')
            }), 500
    
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process question',
            'message': str(e)
        }), 500

@app.route('/api/gemini-direct', methods=['POST'])
def gemini_direct():
    """Answer question using Gemini AI directly (fallback when RAG fails)"""
    try:
        data = request.get_json()
        question = data.get('question')
        language = data.get('language', 'english')
        
        if not question:
            return jsonify({'error': 'question is required'}), 400
        
        logger.info(f"Using Gemini direct for: {question}")
        
        # Import Gemini adapter
        from src.llm.gemini_adapter import GeminiAdapter
        
        # Initialize Gemini
        gemini = GeminiAdapter(Config())
        
        # Create a simple prompt for Class 10 Science
        prompt = f"""You are Vidya, an AI tutor for Class 10 Science students in India. 
        
Student's question: {question}

Please provide a clear, educational answer suitable for Class 10 students. Include:
1. A simple explanation of the concept
2. Key points to remember
3. A practical example if relevant

Keep the language simple and engaging. Answer in {language}."""
        
        # Generate response
        response_text = gemini.generate_text(prompt, max_tokens=500)
        
        if response_text:
            return jsonify({
                'success': True,
                'question': question,
                'response': response_text,
                'sources_used': 0,
                'language': language,
                'method': 'gemini_direct'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate response'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in Gemini direct: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process question',
            'message': str(e)
        }), 500

# Performance Monitoring API Endpoints

@app.route('/api/performance/metrics', methods=['GET'])
def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        metrics = performance_tracker.get_performance_summary()
        return jsonify(metrics)
    
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': 'Failed to get performance metrics'}), 500

@app.route('/api/performance/components', methods=['GET'])
def get_component_performance():
    """Get component-specific performance metrics"""
    try:
        metrics = performance_tracker.get_performance_summary()
        return jsonify({
            'component_metrics': metrics['component_metrics'],
            'timestamp': metrics['system_metrics']['last_activity_time']
        })
    
    except Exception as e:
        logger.error(f"Error getting component performance: {str(e)}")
        return jsonify({'error': 'Failed to get component performance'}), 500

@app.route('/api/performance/api-usage', methods=['GET'])
def get_api_usage_metrics():
    """Get API usage and cost tracking metrics"""
    try:
        metrics = performance_tracker.get_performance_summary()
        return jsonify({
            'api_metrics': metrics['api_metrics'],
            'total_estimated_cost': sum(
                api_data['estimated_cost'] 
                for api_data in metrics['api_metrics'].values()
            ),
            'timestamp': metrics['system_metrics']['last_activity_time']
        })
    
    except Exception as e:
        logger.error(f"Error getting API usage metrics: {str(e)}")
        return jsonify({'error': 'Failed to get API usage metrics'}), 500

@app.route('/api/performance/cache', methods=['GET'])
def get_cache_performance():
    """Get cache performance metrics"""
    try:
        metrics = performance_tracker.get_performance_summary()
        return jsonify({
            'cache_metrics': metrics['cache_metrics'],
            'overall_hit_rate': sum(
                cache_data['cache_hits'] 
                for cache_data in metrics['cache_metrics'].values()
            ) / max(1, sum(
                cache_data['total_requests'] 
                for cache_data in metrics['cache_metrics'].values()
            )) * 100,
            'timestamp': metrics['system_metrics']['last_activity_time']
        })
    
    except Exception as e:
        logger.error(f"Error getting cache performance: {str(e)}")
        return jsonify({'error': 'Failed to get cache performance'}), 500

@app.route('/api/performance/alerts', methods=['GET'])
def get_performance_alerts():
    """Get recent performance alerts"""
    try:
        metrics = performance_tracker.get_performance_summary()
        return jsonify({
            'recent_alerts': metrics['recent_alerts'],
            'alert_count': len(metrics['recent_alerts']),
            'timestamp': metrics['system_metrics']['last_activity_time']
        })
    
    except Exception as e:
        logger.error(f"Error getting performance alerts: {str(e)}")
        return jsonify({'error': 'Failed to get performance alerts'}), 500

@app.route('/api/performance/export', methods=['POST'])
def export_performance_metrics():
    """Export performance metrics to file"""
    try:
        data = request.get_json() or {}
        filepath = data.get('filepath')
        
        performance_tracker.export_metrics_to_file(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Performance metrics exported successfully',
            'filepath': filepath or 'logs/performance_metrics_*.json'
        })
    
    except Exception as e:
        logger.error(f"Error exporting performance metrics: {str(e)}")
        return jsonify({'error': 'Failed to export performance metrics'}), 500

@app.route('/api/performance/reset', methods=['POST'])
def reset_performance_metrics():
    """Reset all performance metrics (for testing)"""
    try:
        performance_tracker.reset_metrics()
        
        return jsonify({
            'success': True,
            'message': 'Performance metrics reset successfully'
        })
    
    except Exception as e:
        logger.error(f"Error resetting performance metrics: {str(e)}")
        return jsonify({'error': 'Failed to reset performance metrics'}), 500

@app.route('/api/performance/dashboard', methods=['GET'])
def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        metrics = performance_tracker.get_performance_summary()
        
        # Calculate key performance indicators
        total_calls = metrics['system_metrics']['total_calls']
        concurrent_calls = metrics['system_metrics']['concurrent_calls']
        uptime_hours = metrics['uptime_seconds'] / 3600
        
        # Component performance summary
        component_summary = {}
        for name, comp_metrics in metrics['component_metrics'].items():
            component_summary[name] = {
                'avg_response_time': comp_metrics['average_response_time'],
                'success_rate': comp_metrics['success_rate'],
                'total_calls': comp_metrics['total_calls']
            }
        
        # API cost summary
        total_cost = sum(
            api_data['estimated_cost'] 
            for api_data in metrics['api_metrics'].values()
        )
        
        # Cache efficiency
        total_cache_requests = sum(
            cache_data['total_requests'] 
            for cache_data in metrics['cache_metrics'].values()
        )
        total_cache_hits = sum(
            cache_data['cache_hits'] 
            for cache_data in metrics['cache_metrics'].values()
        )
        overall_cache_hit_rate = (total_cache_hits / max(1, total_cache_requests)) * 100
        
        dashboard_data = {
            'system_overview': {
                'total_calls': total_calls,
                'concurrent_calls': concurrent_calls,
                'uptime_hours': uptime_hours,
                'system_health': 'healthy' if len(metrics['recent_alerts']) == 0 else 'warning'
            },
            'performance_summary': {
                'components': component_summary,
                'total_estimated_cost': total_cost,
                'cache_hit_rate': overall_cache_hit_rate,
                'recent_alerts_count': len(metrics['recent_alerts'])
            },
            'detailed_metrics': metrics
        }
        
        return jsonify(dashboard_data)
    
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {str(e)}")
        return jsonify({'error': 'Failed to get performance dashboard'}), 500

@app.route('/dashboard', methods=['GET'])
def performance_dashboard_page():
    """Serve the performance dashboard HTML page"""
    try:
        return render_template('performance_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving dashboard page: {str(e)}")
        return f"<h1>Dashboard Error</h1><p>Could not load dashboard: {str(e)}</p>", 500

@app.route('/production-dashboard', methods=['GET'])
def production_dashboard_page():
    """Serve the production dashboard HTML page"""
    try:
        return render_template('production_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving production dashboard page: {str(e)}")
        return f"<h1>Production Dashboard Error</h1><p>Could not load dashboard: {str(e)}</p>", 500

# Backup Management API Endpoints

@app.route('/api/backup/create', methods=['POST'])
def create_backup():
    """Create system backup"""
    try:
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'full')
        components = data.get('components')
        
        if Config.IS_PRODUCTION:
            backup_manager = get_backup_manager(Config)
            backup_info = backup_manager.create_backup(backup_type, components)
            
            if backup_info:
                return jsonify({
                    'success': True,
                    'backup_id': backup_info.backup_id,
                    'backup_type': backup_info.backup_type,
                    'size_mb': backup_info.size_bytes / 1024 / 1024,
                    'components': backup_info.components
                })
            else:
                return jsonify({'error': 'Backup creation failed'}), 500
        else:
            return jsonify({'error': 'Backup only available in production'}), 400
            
    except Exception as e:
        logger.error(f"Backup creation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/restore', methods=['POST'])
def restore_backup():
    """Restore from backup"""
    try:
        data = request.get_json()
        backup_id = data.get('backup_id')
        components = data.get('components')
        
        if not backup_id:
            return jsonify({'error': 'backup_id is required'}), 400
        
        if Config.IS_PRODUCTION:
            backup_manager = get_backup_manager(Config)
            success = backup_manager.restore_backup(backup_id, components)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Restore from backup {backup_id} completed'
                })
            else:
                return jsonify({'error': 'Restore failed'}), 500
        else:
            return jsonify({'error': 'Restore only available in production'}), 400
            
    except Exception as e:
        logger.error(f"Backup restore error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """List available backups"""
    try:
        if Config.IS_PRODUCTION:
            backup_manager = get_backup_manager(Config)
            backups = backup_manager.list_backups()
            status = backup_manager.get_backup_status()
            
            return jsonify({
                'backups': backups,
                'status': status
            })
        else:
            return jsonify({'backups': [], 'status': {'message': 'Backup not available in development'}})
            
    except Exception as e:
        logger.error(f"Backup list error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Load Balancer API Endpoints

@app.route('/api/load-balancer/status', methods=['GET'])
def get_load_balancer_status():
    """Get load balancer status"""
    try:
        if Config.IS_PRODUCTION:
            load_balancer = get_load_balancer(Config)
            status = load_balancer.get_load_status()
            return jsonify(status)
        else:
            return jsonify({'message': 'Load balancer not active in development'})
            
    except Exception as e:
        logger.error(f"Load balancer status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-balancer/metrics', methods=['GET'])
def get_load_balancer_metrics():
    """Get load balancer performance metrics"""
    try:
        if Config.IS_PRODUCTION:
            load_balancer = get_load_balancer(Config)
            metrics = load_balancer.get_performance_metrics()
            return jsonify(metrics)
        else:
            return jsonify({'load_balancer': {'message': 'Not active in development'}})
            
    except Exception as e:
        logger.error(f"Load balancer metrics error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error Tracking API Endpoints

@app.route('/api/errors/summary', methods=['GET'])
def get_error_summary():
    """Get error summary for debugging"""
    try:
        hours = request.args.get('hours', 24, type=int)
        summary = error_tracker.get_error_summary(hours)
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Error getting error summary: {str(e)}")
        return jsonify({'error': 'Failed to get error summary'}), 500

@app.route('/api/errors/debugging-report', methods=['GET'])
def get_debugging_report():
    """Get comprehensive debugging report"""
    try:
        report = error_tracker.get_debugging_report()
        return jsonify(report)
    
    except Exception as e:
        logger.error(f"Error getting debugging report: {str(e)}")
        return jsonify({'error': 'Failed to get debugging report'}), 500

@app.route('/api/errors/export', methods=['POST'])
def export_error_report():
    """Export error report to file"""
    try:
        data = request.get_json() or {}
        filepath = data.get('filepath')
        
        exported_path = error_tracker.export_error_report(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Error report exported successfully',
            'filepath': exported_path
        })
    
    except Exception as e:
        logger.error(f"Error exporting error report: {str(e)}")
        return jsonify({'error': 'Failed to export error report'}), 500

# Demo System and Presentation Tools Endpoints

@app.route('/demo/simulator', methods=['GET'])
def demo_simulator_page():
    """Serve the demo simulator HTML page"""
    try:
        return render_template('demo_simulator.html')
    except Exception as e:
        logger.error(f"Error serving demo simulator page: {str(e)}")
        return f"<h1>Demo Simulator Error</h1><p>Could not load demo simulator: {str(e)}</p>", 500

@app.route('/demo/processing-dashboard', methods=['GET'])
def processing_dashboard_page():
    """Serve the processing pipeline dashboard HTML page"""
    try:
        return render_template('processing_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving processing dashboard page: {str(e)}")
        return f"<h1>Processing Dashboard Error</h1><p>Could not load processing dashboard: {str(e)}</p>", 500

@app.route('/api/demo/recordings', methods=['GET'])
def get_demo_recordings():
    """Get list of demo call recordings"""
    try:
        demo_only = request.args.get('demo_only', 'true').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        recordings = call_recorder.list_recordings(demo_only=demo_only, limit=limit)
        
        recordings_data = []
        for recording in recordings:
            recordings_data.append({
                'recording_id': recording.recording_id,
                'phone_number': recording.phone_number,
                'session_id': recording.session_id,
                'start_time': recording.start_time.isoformat(),
                'end_time': recording.end_time.isoformat() if recording.end_time else None,
                'duration_seconds': recording.duration_seconds,
                'language': recording.language,
                'questions_count': len(recording.questions_asked),
                'responses_count': len(recording.responses_given),
                'audio_files_count': len(recording.audio_files),
                'call_status': recording.call_status,
                'demo_mode': recording.demo_mode,
                'created_at': recording.created_at.isoformat()
            })
        
        return jsonify({
            'recordings': recordings_data,
            'total_count': len(recordings_data),
            'demo_only': demo_only
        })
    
    except Exception as e:
        logger.error(f"Error getting demo recordings: {str(e)}")
        return jsonify({'error': 'Failed to get demo recordings'}), 500

@app.route('/api/demo/recordings/<recording_id>', methods=['GET'])
def get_demo_recording_details(recording_id):
    """Get detailed information about a specific recording"""
    try:
        recording = call_recorder.get_recording(recording_id)
        
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        recording_data = {
            'recording_id': recording.recording_id,
            'phone_number': recording.phone_number,
            'session_id': recording.session_id,
            'start_time': recording.start_time.isoformat(),
            'end_time': recording.end_time.isoformat() if recording.end_time else None,
            'duration_seconds': recording.duration_seconds,
            'language': recording.language,
            'questions_asked': recording.questions_asked,
            'responses_given': recording.responses_given,
            'audio_files': recording.audio_files,
            'processing_metrics': recording.processing_metrics,
            'call_status': recording.call_status,
            'demo_mode': recording.demo_mode,
            'created_at': recording.created_at.isoformat()
        }
        
        return jsonify(recording_data)
    
    except Exception as e:
        logger.error(f"Error getting recording details: {str(e)}")
        return jsonify({'error': 'Failed to get recording details'}), 500

@app.route('/api/demo/recordings/<recording_id>/export', methods=['POST'])
def export_demo_recording(recording_id):
    """Export a demo recording to file"""
    try:
        data = request.get_json() or {}
        export_path = data.get('export_path')
        
        exported_path = call_recorder.export_recording(recording_id, export_path)
        
        return jsonify({
            'success': True,
            'message': 'Recording exported successfully',
            'filepath': exported_path
        })
    
    except Exception as e:
        logger.error(f"Error exporting recording: {str(e)}")
        return jsonify({'error': 'Failed to export recording'}), 500

@app.route('/api/demo/summary', methods=['GET'])
def get_demo_summary():
    """Get comprehensive demo summary for presentation"""
    try:
        summary = call_recorder.create_demo_summary()
        
        # Add additional system metrics
        performance_metrics = performance_tracker.get_performance_summary()
        
        enhanced_summary = {
            **summary,
            'system_performance': {
                'total_calls': performance_metrics['system_metrics']['total_calls'],
                'average_response_time': performance_metrics['system_metrics'].get('average_response_time', 0),
                'success_rate': performance_metrics['system_metrics'].get('success_rate', 100),
                'uptime_hours': performance_metrics.get('uptime_seconds', 0) / 3600
            },
            'demo_questions_available': len(session_manager.get_demo_questions()),
            'cached_responses': len(session_manager.demo_cache),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(enhanced_summary)
    
    except Exception as e:
        logger.error(f"Error getting demo summary: {str(e)}")
        return jsonify({'error': 'Failed to get demo summary'}), 500

@app.route('/api/demo/start-recording', methods=['POST'])
def start_demo_recording():
    """Start recording a demo call session"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        session_id = data.get('session_id')
        language = data.get('language', 'english')
        
        if not all([phone_number, session_id]):
            return jsonify({'error': 'phone_number and session_id are required'}), 400
        
        recording_id = call_recorder.start_recording(
            phone_number=phone_number,
            session_id=session_id,
            language=language,
            demo_mode=True
        )
        
        return jsonify({
            'success': True,
            'recording_id': recording_id,
            'message': 'Demo recording started'
        })
    
    except Exception as e:
        logger.error(f"Error starting demo recording: {str(e)}")
        return jsonify({'error': 'Failed to start demo recording'}), 500

@app.route('/api/demo/end-recording', methods=['POST'])
def end_demo_recording():
    """End a demo call recording"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        status = data.get('status', 'completed')
        
        if not phone_number:
            return jsonify({'error': 'phone_number is required'}), 400
        
        recording_id = call_recorder.end_recording(phone_number, status)
        
        if recording_id:
            return jsonify({
                'success': True,
                'recording_id': recording_id,
                'message': 'Demo recording ended'
            })
        else:
            return jsonify({'error': 'No active recording found'}), 404
    
    except Exception as e:
        logger.error(f"Error ending demo recording: {str(e)}")
        return jsonify({'error': 'Failed to end demo recording'}), 500

@app.route('/api/demo/curated-questions', methods=['GET'])
def get_curated_demo_questions():
    """Get the 20 curated demo questions with categories"""
    try:
        # Get demo questions from session manager
        questions = session_manager.get_demo_questions()
        qa_pairs = session_manager.get_demo_qa_pairs()
        
        # Categorize questions
        categorized_questions = {
            'physics': [],
            'chemistry': [],
            'biology': []
        }
        
        # Simple categorization based on keywords
        physics_keywords = ['light', 'reflection', 'mirror', 'current', 'magnetic', 'motor', 'ohm', 'refraction']
        chemistry_keywords = ['acid', 'base', 'soap', 'metal', 'corrosion', 'equation', 'carbon dioxide', 'ph']
        biology_keywords = ['plant', 'food', 'kidney', 'heart', 'blood', 'photosynthesis', 'breathe', 'reproduction']
        
        for i, (question, response) in enumerate(qa_pairs):
            question_lower = question.lower()
            
            category = 'biology'  # default
            if any(keyword in question_lower for keyword in physics_keywords):
                category = 'physics'
            elif any(keyword in question_lower for keyword in chemistry_keywords):
                category = 'chemistry'
            
            categorized_questions[category].append({
                'id': i + 1,
                'question': question,
                'response': response,
                'category': category
            })
        
        return jsonify({
            'total_questions': len(questions),
            'categories': categorized_questions,
            'physics_count': len(categorized_questions['physics']),
            'chemistry_count': len(categorized_questions['chemistry']),
            'biology_count': len(categorized_questions['biology'])
        })
    
    except Exception as e:
        logger.error(f"Error getting curated demo questions: {str(e)}")
        return jsonify({'error': 'Failed to get curated demo questions'}), 500

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