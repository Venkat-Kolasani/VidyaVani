"""
Context Builder for RAG Engine

This module assembles retrieved content with student questions to create
optimal context for OpenAI processing.
"""

import logging
from typing import List, Dict, Any, Optional
import time

from .semantic_search import SemanticSearchEngine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context for RAG processing by combining search results with questions
    """
    
    def __init__(self, config: Config):
        """
        Initialize context builder
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.search_engine = SemanticSearchEngine(config)
        
        # Context parameters
        self.max_context_words = 800  # Maximum words in context
        self.max_sources = 3  # Maximum number of sources to include
        
        logger.info("Context builder initialized")
    
    def build_context(self, question: str,
                     language: str = "English",
                     detail_level: str = "simple",
                     subject_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Build complete context for RAG processing
        
        Args:
            question: Student's question
            language: Response language (English/Telugu)
            detail_level: Level of detail (simple/detailed)
            subject_filter: Optional subject filter
            
        Returns:
            Complete context dictionary for response generation
        """
        start_time = time.time()
        
        logger.info(f"Building context for: '{question[:50]}...' (lang: {language}, detail: {detail_level})")
        
        # Get search context
        search_context = self.search_engine.get_search_context(
            question=question,
            subject_filter=subject_filter,
            max_context_words=self.max_context_words
        )
        
        # Build complete context
        context = {
            'question': question,
            'language': language,
            'detail_level': detail_level,
            'subject_filter': subject_filter,
            'search_results': search_context,
            'context_quality': self._assess_context_quality(search_context),
            'build_time': time.time() - start_time
        }
        
        # Add formatted context for prompt
        context['formatted_context'] = self._format_context_for_prompt(context)
        
        logger.info(f"Context built in {context['build_time']:.3f}s (quality: {context['context_quality']['score']:.2f})")
        
        return context
    
    def _assess_context_quality(self, search_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the quality of retrieved context
        
        Args:
            search_context: Search results from semantic search
            
        Returns:
            Context quality assessment
        """
        if not search_context['found_relevant_content']:
            return {
                'score': 0.0,
                'level': 'no_content',
                'issues': ['No relevant content found'],
                'recommendations': ['Try rephrasing the question', 'Ask about basic science topics']
            }
        
        confidence = search_context['confidence']
        num_sources = len(search_context['source_chunks'])
        total_words = search_context['total_words']
        
        # Calculate quality score (0.0 to 1.0)
        score = 0.0
        issues = []
        recommendations = []
        
        # Confidence component (40% of score)
        if confidence >= 0.7:
            score += 0.4
        elif confidence >= 0.5:
            score += 0.3
        elif confidence >= 0.3:
            score += 0.2
            issues.append("Low confidence in content relevance")
            recommendations.append("Consider asking more specific questions")
        else:
            score += 0.1
            issues.append("Very low confidence in content relevance")
            recommendations.append("Try asking about basic science concepts")
        
        # Source diversity component (30% of score)
        if num_sources >= 3:
            score += 0.3
        elif num_sources >= 2:
            score += 0.2
        else:
            score += 0.1
            issues.append("Limited source diversity")
            recommendations.append("Question might be too specific or not covered in curriculum")
        
        # Content completeness component (30% of score)
        if total_words >= 400:
            score += 0.3
        elif total_words >= 200:
            score += 0.2
        else:
            score += 0.1
            issues.append("Limited content available")
            recommendations.append("Ask for more general explanations")
        
        # Determine quality level
        if score >= 0.8:
            level = 'excellent'
        elif score >= 0.6:
            level = 'good'
        elif score >= 0.4:
            level = 'fair'
        else:
            level = 'poor'
        
        return {
            'score': score,
            'level': level,
            'confidence': confidence,
            'num_sources': num_sources,
            'total_words': total_words,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """
        Format context for use in OpenAI prompt
        
        Args:
            context: Complete context dictionary
            
        Returns:
            Formatted context string for prompt
        """
        search_results = context['search_results']
        
        if not search_results['found_relevant_content']:
            return "No relevant content found in NCERT curriculum for this question."
        
        # Build formatted context
        parts = []
        
        # Add context header
        parts.append("=== RELEVANT NCERT CONTENT ===")
        
        # Add retrieved content
        parts.append(search_results['context_text'])
        
        # Add source information
        parts.append("\n=== SOURCES ===")
        for i, source in enumerate(search_results['source_chunks'], 1):
            chapter = source.get('chapter', 'Unknown Chapter')
            section = source.get('section', 'Unknown Section')
            confidence = source.get('similarity_score', 0.0)
            source_info = f"{i}. {chapter} - {section} (Confidence: {confidence:.2f})"
            parts.append(source_info)
        
        # Add context metadata
        parts.append(f"\n=== CONTEXT INFO ===")
        parts.append(f"Total content words: {search_results['total_words']}")
        parts.append(f"Overall confidence: {search_results['confidence']:.2f}")
        parts.append(f"Number of sources: {len(search_results['source_chunks'])}")
        
        return "\n".join(parts)
    
    def get_fallback_context(self, question: str, language: str = "English") -> Dict[str, Any]:
        """
        Get fallback context when search fails
        
        Args:
            question: Student's question
            language: Response language
            
        Returns:
            Fallback context dictionary
        """
        return {
            'question': question,
            'language': language,
            'detail_level': 'simple',
            'subject_filter': None,
            'search_results': {
                'context_text': '',
                'source_chunks': [],
                'confidence': 0.0,
                'found_relevant_content': False,
                'total_words': 0
            },
            'context_quality': {
                'score': 0.0,
                'level': 'no_content',
                'issues': ['No relevant content found'],
                'recommendations': ['Try asking about basic science topics']
            },
            'formatted_context': "No relevant content found in NCERT curriculum for this question.",
            'is_fallback': True
        }
    
    def test_context_building(self) -> Dict[str, Any]:
        """
        Test context building with sample questions
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing context building functionality...")
        
        test_cases = [
            {
                'question': "What is reflection of light?",
                'language': "English",
                'detail_level': "simple",
                'expected_quality': 'good'
            },
            {
                'question': "Explain the laws of reflection in detail",
                'language': "English", 
                'detail_level': "detailed",
                'expected_quality': 'good'
            },
            {
                'question': "What are mirrors?",
                'language': "Telugu",
                'detail_level': "simple",
                'expected_quality': 'fair'
            },
            {
                'question': "How do quantum computers work?",  # Off-topic
                'language': "English",
                'detail_level': "simple",
                'expected_quality': 'poor'
            }
        ]
        
        test_results = {
            'total_tests': len(test_cases),
            'passed_tests': 0,
            'failed_tests': 0,
            'results': []
        }
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                logger.info(f"Test {i}: {test_case['question']}")
                
                context = self.build_context(
                    question=test_case['question'],
                    language=test_case['language'],
                    detail_level=test_case['detail_level']
                )
                
                quality_level = context['context_quality']['level']
                expected_level = test_case['expected_quality']
                
                # Simple pass/fail based on quality expectations
                passed = (
                    (expected_level == 'good' and quality_level in ['excellent', 'good']) or
                    (expected_level == 'fair' and quality_level in ['excellent', 'good', 'fair']) or
                    (expected_level == 'poor' and quality_level in ['poor', 'no_content'])
                )
                
                if passed:
                    test_results['passed_tests'] += 1
                    logger.info(f"  ✅ PASS - Quality: {quality_level} (expected: {expected_level})")
                else:
                    test_results['failed_tests'] += 1
                    logger.warning(f"  ❌ FAIL - Quality: {quality_level} (expected: {expected_level})")
                
                test_results['results'].append({
                    'test_case': test_case,
                    'context_quality': context['context_quality'],
                    'build_time': context['build_time'],
                    'passed': passed
                })
                
            except Exception as e:
                logger.error(f"Test {i} failed with error: {e}")
                test_results['failed_tests'] += 1
                test_results['results'].append({
                    'test_case': test_case,
                    'error': str(e),
                    'passed': False
                })
        
        logger.info(f"Context building tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results


def main():
    """Main function for testing context builder"""
    config = Config()
    
    # Initialize context builder
    context_builder = ContextBuilder(config)
    
    # Run tests
    test_results = context_builder.test_context_building()
    
    print(f"\n📊 Context Builder Test Results:")
    print(f"Passed tests: {test_results['passed_tests']}/{test_results['total_tests']}")
    
    # Show detailed results
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(test_results['results'], 1):
        status = "✅" if result['passed'] else "❌"
        question = result['test_case']['question']
        if 'context_quality' in result:
            quality = result['context_quality']['level']
            print(f"{status} Test {i}: {question[:40]}... (Quality: {quality})")
        else:
            print(f"{status} Test {i}: {question[:40]}... (Error: {result.get('error', 'Unknown')})")


if __name__ == "__main__":
    main()