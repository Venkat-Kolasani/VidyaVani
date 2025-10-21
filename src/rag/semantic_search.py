"""
Semantic Search Engine for RAG

This module provides semantic search functionality using FAISS to retrieve
the most relevant NCERT content chunks for student questions.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
import time

import numpy as np
import openai

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from content import NCERTKnowledgeBase, ContentChunk
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """
    Semantic search engine that retrieves relevant NCERT content chunks
    using FAISS vector similarity search
    """
    
    def __init__(self, config: Config):
        """
        Initialize semantic search engine
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.knowledge_base = NCERTKnowledgeBase(config)
        
        # Initialize knowledge base asynchronously to avoid blocking startup
        import threading
        self._initialization_thread = threading.Thread(
            target=self._initialize_async,
            daemon=True
        )
        self._initialization_thread.start()
        
        # Search parameters
        self.top_k = config.TOP_K_RETRIEVAL  # Default: 3
        self.min_similarity = 0.1  # Minimum similarity threshold
        
        logger.info("Semantic search engine initialized (knowledge base loading in background)")
    
    def is_ready(self) -> bool:
        """Check if knowledge base is ready for searches"""
        try:
            stats = self.knowledge_base.search_engine.get_stats()
            return stats['total_chunks'] > 0
        except:
            return False
    
    def _initialize_async(self):
        """Initialize knowledge base in background thread"""
        try:
            logger.info("Starting background knowledge base initialization...")
            self.knowledge_base.initialize_knowledge_base()
            logger.info("Background knowledge base initialization completed")
        except Exception as e:
            logger.error(f"Error in background knowledge base initialization: {e}")
    
    def search(self, question: str, 
               subject_filter: Optional[str] = None,
               top_k: Optional[int] = None,
               min_similarity: Optional[float] = None) -> List[Tuple[ContentChunk, float]]:
        """
        Search for relevant content chunks using semantic similarity
        
        Args:
            question: Student's question text
            subject_filter: Optional subject filter (Physics, Chemistry, Biology)
            top_k: Number of results to return (default: config.TOP_K_RETRIEVAL)
            min_similarity: Minimum similarity threshold (default: 0.1)
            
        Returns:
            List of tuples (ContentChunk, similarity_score) ordered by relevance
        """
        start_time = time.time()
        
        # Check if knowledge base is ready
        if not self.is_ready():
            logger.warning("Knowledge base not ready yet, returning empty results")
            return []
        
        # Use provided parameters or defaults
        k = top_k or self.top_k
        min_sim = min_similarity or self.min_similarity
        
        logger.info(f"Searching for: '{question[:50]}...' (top_k={k})")
        
        try:
            # Use knowledge base search functionality
            results = self.knowledge_base.search_relevant_content(
                question=question,
                subject_filter=subject_filter,
                top_k=k
            )
            
            # Filter by minimum similarity
            filtered_results = [
                (chunk, score) for chunk, score in results 
                if score >= min_sim
            ]
            
            search_time = time.time() - start_time
            logger.info(f"Found {len(filtered_results)} relevant chunks in {search_time:.3f}s")
            
            # Log top results for debugging
            for i, (chunk, score) in enumerate(filtered_results[:3], 1):
                logger.debug(f"  {i}. {chunk.section_name} (score: {score:.3f})")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_search_context(self, question: str,
                          subject_filter: Optional[str] = None,
                          max_context_words: int = 800) -> Dict[str, Any]:
        """
        Get formatted search context for RAG processing
        
        Args:
            question: Student's question
            subject_filter: Optional subject filter
            max_context_words: Maximum words in context
            
        Returns:
            Dictionary with search context and metadata
        """
        start_time = time.time()
        
        # Search for relevant content
        results = self.search(question, subject_filter)
        
        if not results:
            return {
                'context_text': '',
                'source_chunks': [],
                'confidence': 0.0,
                'found_relevant_content': False,
                'search_time': time.time() - start_time,
                'total_words': 0
            }
        
        # Build context from results
        context_parts = []
        source_chunks = []
        total_words = 0
        
        for chunk, score in results:
            chunk_words = len(chunk.content_text.split())
            
            # Check word limit
            if total_words + chunk_words > max_context_words and context_parts:
                break
            
            # Format context with source attribution
            context_part = f"[From {chunk.section_name}]\n{chunk.content_text}"
            context_parts.append(context_part)
            
            # Store chunk metadata
            source_chunks.append({
                'chunk_id': chunk.id,
                'section': chunk.section_name,
                'chapter': chunk.chapter_name,
                'subject': chunk.subject,
                'similarity_score': float(score),
                'word_count': chunk_words,
                'source_file': chunk.metadata.get('source_file', 'unknown')
            })
            
            total_words += chunk_words
        
        context_text = "\n\n".join(context_parts)
        
        # Calculate overall confidence (average similarity)
        confidence = sum(score for _, score in results[:len(source_chunks)]) / len(source_chunks)
        
        search_time = time.time() - start_time
        
        return {
            'context_text': context_text,
            'source_chunks': source_chunks,
            'confidence': float(confidence),
            'found_relevant_content': True,
            'search_time': search_time,
            'total_words': total_words,
            'question': question
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        kb_stats = self.knowledge_base.get_knowledge_base_stats()
        
        return {
            'knowledge_base_stats': kb_stats,
            'search_config': {
                'top_k': self.top_k,
                'min_similarity': self.min_similarity
            }
        }
    
    def test_search_functionality(self) -> Dict[str, Any]:
        """
        Test search functionality with sample questions
        
        Returns:
            Test results dictionary
        """
        logger.info("Testing semantic search functionality...")
        
        test_questions = [
            "What is reflection of light?",
            "Explain the laws of reflection",
            "What are concave and convex mirrors?",
            "How does refraction work?",
            "What is the difference between real and virtual images?",
            "Explain Snell's law of refraction"
        ]
        
        test_results = {
            'total_questions': len(test_questions),
            'successful_searches': 0,
            'failed_searches': 0,
            'average_confidence': 0.0,
            'average_search_time': 0.0,
            'results': []
        }
        
        total_confidence = 0.0
        total_time = 0.0
        
        for question in test_questions:
            try:
                context = self.get_search_context(question, subject_filter="Science")
                
                result = {
                    'question': question,
                    'found_content': context['found_relevant_content'],
                    'confidence': context['confidence'],
                    'search_time': context['search_time'],
                    'num_sources': len(context['source_chunks']),
                    'total_words': context['total_words']
                }
                
                if context['found_relevant_content']:
                    test_results['successful_searches'] += 1
                    total_confidence += context['confidence']
                    
                    # Log top source
                    if context['source_chunks']:
                        top_source = context['source_chunks'][0]
                        result['top_source'] = top_source['section']
                        logger.info(f"✅ '{question}' -> {top_source['section']} (confidence: {context['confidence']:.3f})")
                else:
                    test_results['failed_searches'] += 1
                    logger.warning(f"❌ '{question}' -> No relevant content found")
                
                total_time += context['search_time']
                test_results['results'].append(result)
                
            except Exception as e:
                logger.error(f"Search test failed for '{question}': {e}")
                test_results['failed_searches'] += 1
                test_results['results'].append({
                    'question': question,
                    'found_content': False,
                    'error': str(e)
                })
        
        # Calculate averages
        if test_results['successful_searches'] > 0:
            test_results['average_confidence'] = total_confidence / test_results['successful_searches']
        
        test_results['average_search_time'] = total_time / len(test_questions)
        
        logger.info(f"Search test completed: {test_results['successful_searches']}/{test_results['total_questions']} successful")
        
        return test_results


def main():
    """Main function for testing semantic search"""
    config = Config()
    
    # Initialize search engine
    search_engine = SemanticSearchEngine(config)
    
    # Run tests
    test_results = search_engine.test_search_functionality()
    
    print(f"\n📊 Semantic Search Test Results:")
    print(f"Successful searches: {test_results['successful_searches']}/{test_results['total_questions']}")
    print(f"Average confidence: {test_results['average_confidence']:.3f}")
    print(f"Average search time: {test_results['average_search_time']:.3f}s")
    
    # Show detailed results
    print(f"\n📋 Detailed Results:")
    for result in test_results['results']:
        status = "✅" if result['found_content'] else "❌"
        confidence = f"({result['confidence']:.3f})" if result.get('confidence') else ""
        print(f"{status} {result['question']} {confidence}")


if __name__ == "__main__":
    main()