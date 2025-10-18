"""
Main RAG Engine

This module provides the complete RAG (Retrieval-Augmented Generation) engine
that combines semantic search, context building, and response generation for
the VidyaVani IVR learning system.
"""

import logging
from typing import Dict, Any, Optional
import time
import json

from .semantic_search import SemanticSearchEngine
from .context_builder import ContextBuilder
from .response_generator import ResponseGenerator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Add performance tracking
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.performance_decorators import track_performance, PipelineTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Complete RAG engine for educational question answering
    
    Combines semantic search, context building, and response generation
    to provide accurate, educational responses to student questions.
    """
    
    def __init__(self, config: Config):
        """
        Initialize RAG engine
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize components
        logger.info("Initializing RAG engine components...")
        
        self.search_engine = SemanticSearchEngine(config)
        self.context_builder = ContextBuilder(config)
        self.response_generator = ResponseGenerator(config)
        
        # Performance tracking
        self.stats = {
            'total_questions': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0,
            'average_context_quality': 0.0
        }
        
        logger.info("RAG engine initialized successfully")
    
    @track_performance("RAG_Processing")
    def process_question(self, question: str,
                        language: str = "English",
                        detail_level: str = "simple",
                        subject_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a student question through the complete RAG pipeline
        
        Args:
            question: Student's question text
            language: Response language (English/Telugu)
            detail_level: Level of detail (simple/detailed)
            subject_filter: Optional subject filter (Physics, Chemistry, Biology)
            
        Returns:
            Complete response dictionary with generated answer and metadata
        """
        start_time = time.time()
        
        logger.info(f"Processing question: '{question[:50]}...' (lang: {language}, detail: {detail_level})")
        
        try:
            # Step 1: Build context using semantic search
            context = self.context_builder.build_context(
                question=question,
                language=language,
                detail_level=detail_level,
                subject_filter=subject_filter
            )
            
            # Step 2: Generate response using context
            response = self.response_generator.generate_response(context)
            
            # Step 3: Compile complete result
            total_time = time.time() - start_time
            
            result = {
                'question': question,
                'answer': response['response_text'],
                'language': language,
                'detail_level': detail_level,
                'subject_filter': subject_filter,
                
                # Response metadata
                'success': response['success'],
                'word_count': response['word_count'],
                'estimated_speech_time': response['estimated_speech_time'],
                'within_time_limit': response['within_time_limit'],
                
                # Context metadata
                'context_quality': response['context_quality'],
                'source_chunks': response['source_chunks'],
                'num_sources': len(response['source_chunks']),
                
                # Performance metadata
                'total_processing_time': total_time,
                'context_build_time': context['build_time'],
                'response_generation_time': response['generation_time'],
                
                # Technical metadata
                'model_used': response['model_used'],
                'tokens_used': response.get('tokens_used', 0),
                'timestamp': time.time()
            }
            
            # Update statistics
            self._update_stats(result)
            
            logger.info(f"Question processed successfully in {total_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
            
            # Return error response
            error_result = {
                'question': question,
                'answer': self._get_error_response(language),
                'language': language,
                'detail_level': detail_level,
                'subject_filter': subject_filter,
                'success': False,
                'error': str(e),
                'total_processing_time': time.time() - start_time,
                'timestamp': time.time()
            }
            
            self._update_stats(error_result)
            return error_result
    
    def _get_error_response(self, language: str) -> str:
        """
        Get error response in appropriate language
        
        Args:
            language: Response language
            
        Returns:
            Error response text
        """
        if language.lower() == "telugu":
            return "క్షమించండి, సాంకేతిక సమస్య వల్ల మీ ప్రశ్నకు సమాధానం ఇవ్వలేకపోతున్నాను. దయచేసి మళ్లీ ప్రయత్నించండి."
        else:
            return "I'm sorry, I'm having technical difficulties and cannot answer your question right now. Please try asking again."
    
    def _update_stats(self, result: Dict[str, Any]) -> None:
        """
        Update engine statistics
        
        Args:
            result: Processing result dictionary
        """
        self.stats['total_questions'] += 1
        
        if result['success']:
            self.stats['successful_responses'] += 1
            
            # Update averages
            total_successful = self.stats['successful_responses']
            
            # Update average response time
            current_avg_time = self.stats['average_response_time']
            new_time = result['total_processing_time']
            self.stats['average_response_time'] = (
                (current_avg_time * (total_successful - 1) + new_time) / total_successful
            )
            
            # Update average context quality
            if 'context_quality' in result and 'score' in result['context_quality']:
                current_avg_quality = self.stats['average_context_quality']
                new_quality = result['context_quality']['score']
                self.stats['average_context_quality'] = (
                    (current_avg_quality * (total_successful - 1) + new_quality) / total_successful
                )
        else:
            self.stats['failed_responses'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive RAG engine statistics
        
        Returns:
            Statistics dictionary
        """
        success_rate = 0.0
        if self.stats['total_questions'] > 0:
            success_rate = self.stats['successful_responses'] / self.stats['total_questions']
        
        return {
            'engine_stats': self.stats.copy(),
            'success_rate': success_rate,
            'search_engine_stats': self.search_engine.get_stats(),
            'component_status': {
                'search_engine': 'operational',
                'context_builder': 'operational', 
                'response_generator': 'operational'
            }
        }
    
    def test_rag_pipeline(self) -> Dict[str, Any]:
        """
        Test the complete RAG pipeline with sample questions
        
        Returns:
            Comprehensive test results
        """
        logger.info("Testing complete RAG pipeline...")
        
        test_questions = [
            {
                'question': "What is reflection of light?",
                'language': "English",
                'detail_level': "simple",
                'expected_success': True
            },
            {
                'question': "Explain the laws of reflection in detail with examples",
                'language': "English",
                'detail_level': "detailed",
                'expected_success': True
            },
            {
                'question': "What are concave and convex mirrors?",
                'language': "English",
                'detail_level': "simple",
                'expected_success': True
            },
            {
                'question': "వెలుతురు ప్రతిబింబం అంటే ఏమిటి?",  # Telugu: What is reflection of light?
                'language': "Telugu",
                'detail_level': "simple",
                'expected_success': True
            },
            {
                'question': "How do quantum computers work?",  # Off-topic
                'language': "English",
                'detail_level': "simple",
                'expected_success': False
            },
            {
                'question': "What is photosynthesis?",  # Biology topic
                'language': "English",
                'detail_level': "simple",
                'expected_success': True  # Should work if biology content exists
            }
        ]
        
        test_results = {
            'total_tests': len(test_questions),
            'passed_tests': 0,
            'failed_tests': 0,
            'performance_metrics': {
                'average_response_time': 0.0,
                'average_context_quality': 0.0,
                'responses_within_time_limit': 0
            },
            'results': []
        }
        
        total_time = 0.0
        total_quality = 0.0
        successful_tests = 0
        
        for i, test_case in enumerate(test_questions, 1):
            logger.info(f"RAG Test {i}: {test_case['question']}")
            
            try:
                # Process question through RAG pipeline
                result = self.process_question(
                    question=test_case['question'],
                    language=test_case['language'],
                    detail_level=test_case['detail_level']
                )
                
                # Evaluate result
                expected_success = test_case['expected_success']
                actual_success = result['success']
                
                # Test passes if expectation matches reality
                test_passed = (expected_success == actual_success)
                
                if test_passed:
                    test_results['passed_tests'] += 1
                    logger.info(f"  ✅ PASS - Success: {actual_success} (expected: {expected_success})")
                else:
                    test_results['failed_tests'] += 1
                    logger.warning(f"  ❌ FAIL - Success: {actual_success} (expected: {expected_success})")
                
                # Collect metrics for successful responses
                if result['success']:
                    successful_tests += 1
                    total_time += result['total_processing_time']
                    
                    if 'context_quality' in result and 'score' in result['context_quality']:
                        total_quality += result['context_quality']['score']
                    
                    if result.get('within_time_limit', False):
                        test_results['performance_metrics']['responses_within_time_limit'] += 1
                
                # Store detailed result
                test_result = {
                    'test_case': test_case,
                    'result': {
                        'success': result['success'],
                        'response_length': result.get('word_count', 0),
                        'processing_time': result['total_processing_time'],
                        'context_quality': result.get('context_quality', {}).get('score', 0.0),
                        'within_time_limit': result.get('within_time_limit', False),
                        'num_sources': result.get('num_sources', 0)
                    },
                    'passed': test_passed
                }
                
                test_results['results'].append(test_result)
                
            except Exception as e:
                logger.error(f"RAG Test {i} failed with error: {e}")
                test_results['failed_tests'] += 1
                test_results['results'].append({
                    'test_case': test_case,
                    'error': str(e),
                    'passed': False
                })
        
        # Calculate performance metrics
        if successful_tests > 0:
            test_results['performance_metrics']['average_response_time'] = total_time / successful_tests
            test_results['performance_metrics']['average_context_quality'] = total_quality / successful_tests
        
        logger.info(f"RAG pipeline tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    def reset_stats(self) -> None:
        """Reset engine statistics"""
        self.stats = {
            'total_questions': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0,
            'average_context_quality': 0.0
        }
        logger.info("RAG engine statistics reset")


def main():
    """Main function for testing RAG engine"""
    config = Config()
    
    # Validate OpenAI API key
    if not config.OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
        return
    
    # Initialize RAG engine
    rag_engine = RAGEngine(config)
    
    # Run comprehensive tests
    test_results = rag_engine.test_rag_pipeline()
    
    print(f"\n🎯 RAG Engine Test Results:")
    print(f"Passed tests: {test_results['passed_tests']}/{test_results['total_tests']}")
    
    metrics = test_results['performance_metrics']
    print(f"Average response time: {metrics['average_response_time']:.3f}s")
    print(f"Average context quality: {metrics['average_context_quality']:.3f}")
    print(f"Responses within time limit: {metrics['responses_within_time_limit']}")
    
    # Show detailed results
    print(f"\n📋 Detailed Test Results:")
    for i, result in enumerate(test_results['results'], 1):
        status = "✅" if result['passed'] else "❌"
        question = result['test_case']['question']
        
        if 'result' in result:
            res = result['result']
            print(f"{status} Test {i}: {question[:40]}...")
            print(f"    Success: {res['success']}, Time: {res['processing_time']:.3f}s, Quality: {res['context_quality']:.3f}")
        else:
            print(f"{status} Test {i}: {question[:40]}... (Error: {result.get('error', 'Unknown')})")
    
    # Show engine statistics
    stats = rag_engine.get_stats()
    print(f"\n📊 Engine Statistics:")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Total questions processed: {stats['engine_stats']['total_questions']}")


if __name__ == "__main__":
    main()