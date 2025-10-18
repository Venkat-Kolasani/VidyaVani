"""
Response Generator for RAG Engine

This module generates educational responses using OpenAI GPT-4o-mini with
the "Vidya" AI tutor persona for rural Indian students.
"""

import logging
from typing import Dict, Any, Optional
import time
import json

import openai

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Add performance tracking
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.performance_decorators import track_performance
from utils.error_tracker import error_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VidyaPersona:
    """
    Defines the "Vidya" AI tutor persona and prompts
    """
    
    @staticmethod
    def get_system_prompt(language: str = "English", detail_level: str = "simple") -> str:
        """
        Get system prompt for Vidya persona
        
        Args:
            language: Response language (English/Telugu)
            detail_level: Level of detail (simple/detailed)
            
        Returns:
            System prompt string
        """
        base_persona = """You are 'Vidya', a friendly AI tutor for 10th-grade students in rural India. 

Your teaching style:
- Use simple, clear language that rural students can understand
- Explain concepts using everyday analogies from village life (cooking, farming, household items)
- Be encouraging and patient, like a caring teacher
- Keep responses under 90 seconds when spoken (approximately 200-250 words)
- Focus on helping students understand, not just memorize

Your knowledge:
- You have access to NCERT Class 10 Science curriculum content
- Always base your answers on the provided NCERT content
- If the content doesn't cover the question, say so honestly
- Encourage students to ask follow-up questions"""

        if language.lower() == "telugu":
            language_instruction = """
Response Language: Telugu
- Respond in clear, simple Telugu that rural students understand
- Use common Telugu words, avoid complex Sanskrit terms
- Include English scientific terms in parentheses when needed
- Example: "వెలుతురు (light) అనేది ఒక శక్తి రూపం"
"""
        else:
            language_instruction = """
Response Language: English
- Use simple Indian English that rural students understand
- Avoid complex vocabulary and technical jargon
- Explain scientific terms in simple words
- Use "we" and "our" to be inclusive
"""

        if detail_level == "detailed":
            detail_instruction = """
Detail Level: Detailed Explanation
- Provide comprehensive explanations with examples
- Include step-by-step processes when relevant
- Add practical applications and real-world connections
- Use multiple analogies to ensure understanding
"""
        else:
            detail_instruction = """
Detail Level: Simple Explanation
- Keep explanations concise and focused
- Use one clear analogy or example
- Focus on the main concept without too many details
- Perfect for quick understanding
"""

        return f"{base_persona}\n\n{language_instruction}\n{detail_instruction}"
    
    @staticmethod
    def get_user_prompt_template() -> str:
        """
        Get user prompt template for questions
        
        Returns:
            User prompt template
        """
        return """Student Question: {question}

{context}

Please answer the student's question based on the NCERT content provided above. Remember to:
1. Use simple language and everyday analogies
2. Be encouraging and supportive
3. Keep the response under 90 seconds when spoken
4. Base your answer on the provided NCERT content
5. If the content doesn't fully answer the question, acknowledge this and provide what you can

Answer:"""

    @staticmethod
    def get_fallback_responses(language: str = "English") -> Dict[str, str]:
        """
        Get fallback responses for common scenarios
        
        Args:
            language: Response language
            
        Returns:
            Dictionary of fallback responses
        """
        if language.lower() == "telugu":
            return {
                'no_content': """క్షమించండి, మీ ప్రశ్న గురించి NCERT పుస్తకాలలో సమాచారం లేదు. దయచేసి 10వ తరగతి సైన్స్ విషయాలు గురించి అడగండి - భౌతిక శాస్త్రం, రసాయన శాస్త్రం, లేదా జీవ శాస్త్రం గురించి.""",
                
                'unclear_question': """మీ ప్రశ్న స్పష్టంగా అర్థం కాలేదు. దయచేసి మరింత స్పష్టంగా అడగండి. ఉదాహరణ: "వెలుతురు ప్రతిబింబం అంటే ఏమిటి?" లేదా "అద్దాలు ఎలా పని చేస్తాయి?".""",
                
                'off_topic': """ఈ ప్రశ్న 10వ తరగతి సైన్స్ పాఠ్యక్రమంలో లేదు. దయచేసి వెలుతురు, ధ్వని, ఆమ్లాలు మరియు క్షారాలు, జీవ ప్రక్రియలు వంటి విషయాలు గురించి అడగండి.""",
                
                'technical_error': """క్షమించండి, సాంకేతిక సమస్య వల్ల మీ ప్రశ్నకు సమాధానం ఇవ్వలేకపోతున్నాను. దయచేసి మళ్లీ ప్రయత్నించండి."""
            }
        else:
            return {
                'no_content': """I'm sorry, but I couldn't find information about your question in our NCERT textbooks. Please ask about 10th grade science topics like physics, chemistry, or biology that are covered in your curriculum.""",
                
                'unclear_question': """I didn't quite understand your question. Could you please ask it more clearly? For example: "What is reflection of light?" or "How do mirrors work?".""",
                
                'off_topic': """This question is not covered in the 10th grade science curriculum. Please ask about topics like light, sound, acids and bases, or life processes that we study in class.""",
                
                'technical_error': """I'm sorry, I'm having some technical difficulties and cannot answer your question right now. Please try asking again."""
            }


class ResponseGenerator:
    """
    Generates educational responses using OpenAI with Vidya persona
    """
    
    def __init__(self, config: Config):
        """
        Initialize response generator
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Response parameters
        self.model = config.OPENAI_MODEL  # gpt-4o-mini
        self.max_tokens = config.OPENAI_MAX_TOKENS  # 150
        self.temperature = config.OPENAI_TEMPERATURE  # 0.3
        
        # Adjust max_tokens for longer educational responses
        self.max_response_tokens = 300  # Allow longer responses for education
        
        logger.info(f"Response generator initialized with model: {self.model}")
    
    @track_performance("OpenAI_Response_Generation", track_api_usage=True, service_name="openai_gpt", estimate_cost=True)
    def generate_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate educational response using Vidya persona
        
        Args:
            context: Context dictionary from ContextBuilder
            
        Returns:
            Response dictionary with generated content and metadata
        """
        start_time = time.time()
        
        question = context['question']
        language = context.get('language', 'English')
        detail_level = context.get('detail_level', 'simple')
        
        logger.info(f"Generating response for: '{question[:50]}...' (lang: {language})")
        
        try:
            # Handle no content scenario
            if not context['search_results']['found_relevant_content']:
                return self._generate_fallback_response(context, 'no_content')
            
            # Check context quality
            quality = context['context_quality']
            if quality['score'] < 0.2:
                return self._generate_fallback_response(context, 'no_content')
            
            # Build prompts
            system_prompt = VidyaPersona.get_system_prompt(language, detail_level)
            user_prompt = VidyaPersona.get_user_prompt_template().format(
                question=question,
                context=context['formatted_context']
            )
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_response_tokens,
                temperature=self.temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Calculate response metrics
            generation_time = time.time() - start_time
            word_count = len(generated_text.split())
            estimated_speech_time = word_count / 2.5  # ~2.5 words per second
            
            # Check if response is within time limit (90 seconds)
            within_time_limit = estimated_speech_time <= 90
            
            result = {
                'response_text': generated_text,
                'language': language,
                'detail_level': detail_level,
                'generation_time': generation_time,
                'word_count': word_count,
                'estimated_speech_time': estimated_speech_time,
                'within_time_limit': within_time_limit,
                'context_quality': quality,
                'source_chunks': context['search_results']['source_chunks'],
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens,
                'success': True
            }
            
            logger.info(f"Response generated in {generation_time:.3f}s ({word_count} words, ~{estimated_speech_time:.1f}s speech)")
            
            return result
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            error_tracker.track_error('OpenAI_Response_Generation', e, 
                                     recovery_action='Generated fallback response')
            return self._generate_fallback_response(context, 'technical_error', error=str(e))
    
    def _generate_fallback_response(self, context: Dict[str, Any], 
                                  fallback_type: str, 
                                  error: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate fallback response for error scenarios
        
        Args:
            context: Context dictionary
            fallback_type: Type of fallback (no_content, unclear_question, etc.)
            error: Optional error message
            
        Returns:
            Fallback response dictionary
        """
        language = context.get('language', 'English')
        fallback_responses = VidyaPersona.get_fallback_responses(language)
        
        response_text = fallback_responses.get(fallback_type, fallback_responses['technical_error'])
        
        return {
            'response_text': response_text,
            'language': language,
            'detail_level': context.get('detail_level', 'simple'),
            'generation_time': 0.0,
            'word_count': len(response_text.split()),
            'estimated_speech_time': len(response_text.split()) / 2.5,
            'within_time_limit': True,
            'context_quality': context.get('context_quality', {'score': 0.0}),
            'source_chunks': [],
            'model_used': 'fallback',
            'tokens_used': 0,
            'success': False,
            'fallback_type': fallback_type,
            'error': error
        }
    
    def test_response_generation(self) -> Dict[str, Any]:
        """
        Test response generation with sample contexts
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing response generation functionality...")
        
        # Import here to avoid circular imports
        from .context_builder import ContextBuilder
        
        context_builder = ContextBuilder(self.config)
        
        test_questions = [
            {
                'question': "What is reflection of light?",
                'language': "English",
                'detail_level': "simple"
            },
            {
                'question': "Explain the laws of reflection in detail",
                'language': "English",
                'detail_level': "detailed"
            },
            {
                'question': "వెలుతురు ప్రతిబింబం అంటే ఏమిటి?",  # Telugu
                'language': "Telugu",
                'detail_level': "simple"
            }
        ]
        
        test_results = {
            'total_tests': len(test_questions),
            'successful_responses': 0,
            'failed_responses': 0,
            'results': []
        }
        
        for i, test_case in enumerate(test_questions, 1):
            try:
                logger.info(f"Test {i}: {test_case['question']}")
                
                # Build context
                context = context_builder.build_context(
                    question=test_case['question'],
                    language=test_case['language'],
                    detail_level=test_case['detail_level']
                )
                
                # Generate response
                response = self.generate_response(context)
                
                if response['success']:
                    test_results['successful_responses'] += 1
                    logger.info(f"  ✅ SUCCESS - {response['word_count']} words, ~{response['estimated_speech_time']:.1f}s speech")
                else:
                    test_results['failed_responses'] += 1
                    logger.warning(f"  ❌ FAILED - {response.get('fallback_type', 'unknown error')}")
                
                test_results['results'].append({
                    'test_case': test_case,
                    'response': response,
                    'passed': response['success']
                })
                
            except Exception as e:
                logger.error(f"Test {i} failed with error: {e}")
                test_results['failed_responses'] += 1
                test_results['results'].append({
                    'test_case': test_case,
                    'error': str(e),
                    'passed': False
                })
        
        logger.info(f"Response generation tests completed: {test_results['successful_responses']}/{test_results['total_tests']} successful")
        
        return test_results


def main():
    """Main function for testing response generator"""
    config = Config()
    
    # Validate OpenAI API key
    if not config.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        return
    
    # Initialize response generator
    response_generator = ResponseGenerator(config)
    
    # Run tests
    test_results = response_generator.test_response_generation()
    
    print(f"\n📊 Response Generator Test Results:")
    print(f"Successful responses: {test_results['successful_responses']}/{test_results['total_tests']}")
    
    # Show detailed results
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(test_results['results'], 1):
        status = "✅" if result['passed'] else "❌"
        question = result['test_case']['question']
        if 'response' in result:
            word_count = result['response']['word_count']
            speech_time = result['response']['estimated_speech_time']
            print(f"{status} Test {i}: {question[:40]}... ({word_count} words, ~{speech_time:.1f}s)")
        else:
            print(f"{status} Test {i}: {question[:40]}... (Error: {result.get('error', 'Unknown')})")


if __name__ == "__main__":
    main()