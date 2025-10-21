"""
NCERT Knowledge Base Manager

This module provides a high-level interface for managing the NCERT content
knowledge base, including content processing, vector database operations,
and semantic search capabilities.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
import json

import openai
import numpy as np

from .content_processor import NCERTContentProcessor, ContentChunk
from .vector_database import SemanticSearchEngine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NCERTKnowledgeBase:
    """
    High-level manager for NCERT content knowledge base
    
    This class provides a unified interface for:
    - Processing NCERT content
    - Managing vector database
    - Performing semantic search
    - Retrieving relevant content for questions
    """
    
    def __init__(self, config: Config):
        """
        Initialize NCERT Knowledge Base
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize AI client for embeddings
        if config.USE_GEMINI and config.GOOGLE_GEMINI_API_KEY:
            # Use Gemini with OpenAI-compatible interface
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from utils.gemini_adapter import GeminiOpenAIClient
            self.openai_client = GeminiOpenAIClient(
                api_key=config.GOOGLE_GEMINI_API_KEY,
                model=config.GEMINI_MODEL
            )
            logger.info(f"Using Google Gemini for embeddings: {config.GEMINI_MODEL}")
        else:
            # Use OpenAI or OpenRouter (but OpenRouter doesn't support embeddings)
            client_kwargs = {"api_key": config.OPENAI_API_KEY}
            if hasattr(config, 'OPENAI_BASE_URL') and config.OPENAI_BASE_URL:
                client_kwargs["base_url"] = config.OPENAI_BASE_URL
                logger.info(f"Using custom OpenAI base URL for embeddings: {config.OPENAI_BASE_URL}")
            
            self.openai_client = openai.OpenAI(**client_kwargs)
            logger.info("Using OpenAI for embeddings")
        
        # Initialize components
        self.content_processor = NCERTContentProcessor(config)
        self.search_engine = SemanticSearchEngine(config)
        
        # Cache for recent queries (simple in-memory cache)
        self.query_cache: Dict[str, List[Tuple[ContentChunk, float]]] = {}
        self.cache_max_size = 100
    
    def initialize_knowledge_base(self, force_rebuild: bool = False) -> None:
        """
        Initialize the knowledge base with sample NCERT content
        
        Args:
            force_rebuild: If True, rebuild the knowledge base from scratch
        """
        logger.info("Initializing NCERT Knowledge Base...")
        
        # Check if we already have data
        stats = self.search_engine.get_stats()
        
        if stats['total_chunks'] > 0 and not force_rebuild:
            logger.info(f"Knowledge base already initialized with {stats['total_chunks']} chunks")
            return
        
        if force_rebuild:
            logger.info("Force rebuilding knowledge base...")
            self.search_engine.vector_db.clear_database()
        
        # Process all available content (PDFs + sample content)
        logger.info("Processing NCERT content...")
        chunks = self.content_processor.process_all_content()
        
        # Add to search engine (even if embeddings failed)
        logger.info("Adding content to vector database...")
        self.search_engine.add_content(chunks)
        
        # Force save the database even with zero embeddings
        logger.info("Saving vector database...")
        self.search_engine.vector_db.save_database()
        
        # Display final statistics
        final_stats = self.search_engine.get_stats()
        logger.info(f"Knowledge base initialized successfully!")
        logger.info(f"Total chunks: {final_stats['total_chunks']}")
        logger.info(f"Subjects: {list(final_stats['subjects'].keys())}")
        logger.info(f"Chapters: {list(final_stats['chapters'].keys())}")
    
    def generate_query_embedding(self, query_text: str) -> np.ndarray:
        """
        Generate embedding for a query text using OpenAI
        
        Args:
            query_text: Question or query text
            
        Returns:
            Query embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query_text.strip()
            )
            
            embedding = np.array(response.data[0].embedding)
            logger.debug(f"Generated embedding for query: '{query_text[:50]}...'")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(1536)
    
    def search_relevant_content(self, question: str, 
                              subject_filter: Optional[str] = None,
                              top_k: int = 3,
                              use_cache: bool = True) -> List[Tuple[ContentChunk, float]]:
        """
        Search for content relevant to a student's question
        
        Args:
            question: Student's question text
            subject_filter: Optional subject filter (Physics, Chemistry, Biology)
            top_k: Number of relevant chunks to return
            use_cache: Whether to use query cache
            
        Returns:
            List of tuples (ContentChunk, similarity_score)
        """
        # Create cache key
        cache_key = f"{question.lower().strip()}_{subject_filter}_{top_k}"
        
        # Check cache first
        if use_cache and cache_key in self.query_cache:
            logger.debug(f"Cache hit for query: '{question[:50]}...'")
            return self.query_cache[cache_key]
        
        logger.info(f"Searching for content relevant to: '{question[:100]}...'")
        
        # Generate query embedding
        query_embedding = self.generate_query_embedding(question)
        
        # Search in vector database
        results = self.search_engine.search_content(
            query_embedding=query_embedding,
            subject_filter=subject_filter,
            top_k=top_k
        )
        
        # Cache the results
        if use_cache:
            self._add_to_cache(cache_key, results)
        
        logger.info(f"Found {len(results)} relevant content chunks")
        for i, (chunk, score) in enumerate(results):
            logger.debug(f"  {i+1}. {chunk.section_name} (score: {score:.3f})")
        
        return results
    
    def get_content_context(self, question: str, 
                          subject_filter: Optional[str] = None,
                          max_context_words: int = 800) -> Dict[str, Any]:
        """
        Get formatted context for a question to use with LLM
        
        Args:
            question: Student's question
            subject_filter: Optional subject filter
            max_context_words: Maximum words in context
            
        Returns:
            Dictionary with context information
        """
        # Search for relevant content
        relevant_chunks = self.search_relevant_content(
            question=question,
            subject_filter=subject_filter,
            top_k=self.config.TOP_K_RETRIEVAL
        )
        
        if not relevant_chunks:
            return {
                'context_text': '',
                'source_info': [],
                'confidence': 0.0,
                'found_content': False
            }
        
        # Build context text
        context_parts = []
        source_info = []
        total_words = 0
        
        for chunk, score in relevant_chunks:
            chunk_words = len(chunk.content_text.split())
            
            # Check if adding this chunk would exceed word limit
            if total_words + chunk_words > max_context_words and context_parts:
                break
            
            context_parts.append(f"[From {chunk.section_name}]\n{chunk.content_text}")
            source_info.append({
                'section': chunk.section_name,
                'chapter': chunk.chapter_name,
                'subject': chunk.subject,
                'similarity_score': float(score),
                'word_count': chunk_words
            })
            
            total_words += chunk_words
        
        context_text = "\n\n".join(context_parts)
        
        # Calculate overall confidence (average similarity score)
        confidence = sum(score for _, score in relevant_chunks[:len(source_info)]) / len(source_info)
        
        return {
            'context_text': context_text,
            'source_info': source_info,
            'confidence': float(confidence),
            'found_content': True,
            'total_words': total_words
        }
    
    def _add_to_cache(self, cache_key: str, results: List[Tuple[ContentChunk, float]]) -> None:
        """
        Add query results to cache with size management
        
        Args:
            cache_key: Cache key
            results: Search results to cache
        """
        # Remove oldest entries if cache is full
        if len(self.query_cache) >= self.cache_max_size:
            # Remove first (oldest) entry
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        self.query_cache[cache_key] = results
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the knowledge base
        
        Returns:
            Dictionary with knowledge base statistics
        """
        db_stats = self.search_engine.get_stats()
        
        return {
            'database_stats': db_stats,
            'cache_stats': {
                'cached_queries': len(self.query_cache),
                'cache_max_size': self.cache_max_size
            },
            'configuration': {
                'chunk_size': self.config.CONTENT_CHUNK_SIZE,
                'overlap_size': self.config.CONTENT_OVERLAP,
                'top_k_retrieval': self.config.TOP_K_RETRIEVAL,
                'embedding_model': 'text-embedding-3-small'
            }
        }
    
    def test_search_functionality(self) -> None:
        """
        Test the search functionality with sample queries
        """
        logger.info("Testing knowledge base search functionality...")
        
        test_queries = [
            "What is reflection of light?",
            "Explain the laws of reflection",
            "What are concave and convex mirrors?",
            "How do lenses work?",
            "What is refraction of light?",
            "Explain Snell's law"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            
            context = self.get_content_context(query, subject_filter="Physics")
            
            if context['found_content']:
                logger.info(f"  Confidence: {context['confidence']:.3f}")
                logger.info(f"  Sources: {len(context['source_info'])}")
                logger.info(f"  Context words: {context['total_words']}")
                
                for source in context['source_info']:
                    logger.info(f"    - {source['section']} (score: {source['similarity_score']:.3f})")
            else:
                logger.warning(f"  No relevant content found")
    
    def clear_cache(self) -> None:
        """Clear the query cache"""
        self.query_cache.clear()
        logger.info("Query cache cleared")


def main():
    """Main function for testing the knowledge base"""
    config = Config()
    
    # Validate OpenAI API key
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Initialize knowledge base
    kb = NCERTKnowledgeBase(config)
    
    # Initialize with sample content
    kb.initialize_knowledge_base()
    
    # Display statistics
    stats = kb.get_knowledge_base_stats()
    print(f"\nKnowledge Base Statistics:")
    print(f"Total chunks: {stats['database_stats']['total_chunks']}")
    print(f"Subjects: {stats['database_stats']['subjects']}")
    print(f"Chapters: {stats['database_stats']['chapters']}")
    print(f"Configuration: {stats['configuration']}")
    
    # Test search functionality
    kb.test_search_functionality()
    
    # Interactive testing
    print(f"\n" + "="*50)
    print("Interactive Testing - Enter questions to test search")
    print("Type 'quit' to exit")
    print("="*50)
    
    while True:
        try:
            question = input("\nEnter your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            # Search for relevant content
            context = kb.get_content_context(question)
            
            if context['found_content']:
                print(f"\nFound relevant content (confidence: {context['confidence']:.3f}):")
                print(f"Context ({context['total_words']} words):")
                print("-" * 40)
                print(context['context_text'][:500] + "..." if len(context['context_text']) > 500 else context['context_text'])
                print("-" * 40)
                
                print(f"\nSources:")
                for source in context['source_info']:
                    print(f"  - {source['section']} (score: {source['similarity_score']:.3f})")
            else:
                print("No relevant content found for this question.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()