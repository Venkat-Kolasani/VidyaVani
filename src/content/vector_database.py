"""
FAISS Vector Database Module

This module handles the FAISS vector database operations for semantic search
of NCERT content chunks using OpenAI embeddings.
"""

import os
import pickle
import logging
from typing import List, Tuple, Optional, Dict, Any
import json

import faiss
import numpy as np

from .content_processor import ContentChunk
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSVectorDatabase:
    """FAISS-based vector database for semantic search of NCERT content"""
    
    def __init__(self, config: Config, embedding_dimension: int = 1536):
        """
        Initialize FAISS vector database
        
        Args:
            config: Application configuration
            embedding_dimension: Dimension of OpenAI embeddings (1536 for text-embedding-3-small)
        """
        self.config = config
        self.embedding_dimension = embedding_dimension
        
        # Initialize FAISS index (Inner Product for cosine similarity)
        self.index = faiss.IndexFlatIP(embedding_dimension)
        
        # Store metadata separately (FAISS only stores vectors)
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.chunk_id_to_index: Dict[str, int] = {}
        
        # Database file paths
        self.db_dir = "data/ncert/vector_db"
        self.index_path = os.path.join(self.db_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(self.db_dir, "chunk_metadata.json")
        self.id_mapping_path = os.path.join(self.db_dir, "id_mapping.json")
        
        # Ensure database directory exists
        os.makedirs(self.db_dir, exist_ok=True)
    
    def normalize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Normalize embeddings for cosine similarity using Inner Product
        
        Args:
            embeddings: Array of embeddings to normalize
            
        Returns:
            Normalized embeddings
        """
        # Normalize to unit vectors for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        return embeddings / norms
    
    def add_chunks(self, chunks: List[ContentChunk]) -> None:
        """
        Add content chunks to the vector database
        
        Args:
            chunks: List of ContentChunk objects with embeddings
        """
        if not chunks:
            logger.warning("No chunks provided to add to database")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to FAISS vector database")
        
        # Extract embeddings and metadata
        embeddings = []
        metadata = []
        
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                continue
            
            embeddings.append(chunk.embedding)
            
            # Store metadata (everything except embedding)
            chunk_metadata = {
                'id': chunk.id,
                'chapter_name': chunk.chapter_name,
                'section_name': chunk.section_name,
                'content_text': chunk.content_text,
                'subject': chunk.subject,
                'grade': chunk.grade,
                'language': chunk.language,
                'word_count': chunk.word_count,
                'chunk_index': chunk.chunk_index,
                'total_chunks': chunk.total_chunks,
                'metadata': chunk.metadata
            }
            metadata.append(chunk_metadata)
        
        if not embeddings:
            logger.error("No valid embeddings found in chunks")
            return
        
        # Convert to numpy array and normalize
        embeddings_array = np.array(embeddings).astype('float32')
        normalized_embeddings = self.normalize_embeddings(embeddings_array)
        
        # Add to FAISS index
        start_index = self.index.ntotal
        self.index.add(normalized_embeddings)
        
        # Update metadata and ID mapping
        for i, chunk_meta in enumerate(metadata):
            faiss_index = start_index + i
            self.chunk_metadata.append(chunk_meta)
            self.chunk_id_to_index[chunk_meta['id']] = faiss_index
        
        logger.info(f"Successfully added {len(embeddings)} chunks to database. Total chunks: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, top_k: int = 3, 
               min_similarity: float = 0.1) -> List[Tuple[ContentChunk, float]]:
        """
        Search for similar content chunks using semantic similarity
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of tuples (ContentChunk, similarity_score)
        """
        if self.index.ntotal == 0:
            logger.warning("Vector database is empty")
            return []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        normalized_query = self.normalize_embeddings(query_embedding)
        
        # Search in FAISS index
        similarities, indices = self.index.search(normalized_query, min(top_k, self.index.ntotal))
        
        # Convert results to ContentChunk objects
        results = []
        for similarity, idx in zip(similarities[0], indices[0]):
            if similarity < min_similarity:
                continue
            
            if idx < len(self.chunk_metadata):
                metadata = self.chunk_metadata[idx]
                
                # Reconstruct ContentChunk (without embedding to save memory)
                chunk = ContentChunk(
                    id=metadata['id'],
                    chapter_name=metadata['chapter_name'],
                    section_name=metadata['section_name'],
                    content_text=metadata['content_text'],
                    subject=metadata['subject'],
                    grade=metadata['grade'],
                    language=metadata['language'],
                    word_count=metadata['word_count'],
                    chunk_index=metadata['chunk_index'],
                    total_chunks=metadata['total_chunks'],
                    metadata=metadata['metadata'],
                    embedding=None  # Don't load embedding for search results
                )
                
                results.append((chunk, float(similarity)))
        
        logger.info(f"Found {len(results)} similar chunks for query (top_k={top_k})")
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[ContentChunk]:
        """
        Retrieve a specific chunk by its ID
        
        Args:
            chunk_id: Unique chunk identifier
            
        Returns:
            ContentChunk object or None if not found
        """
        if chunk_id not in self.chunk_id_to_index:
            return None
        
        faiss_index = self.chunk_id_to_index[chunk_id]
        if faiss_index >= len(self.chunk_metadata):
            return None
        
        metadata = self.chunk_metadata[faiss_index]
        
        # Reconstruct ContentChunk
        chunk = ContentChunk(
            id=metadata['id'],
            chapter_name=metadata['chapter_name'],
            section_name=metadata['section_name'],
            content_text=metadata['content_text'],
            subject=metadata['subject'],
            grade=metadata['grade'],
            language=metadata['language'],
            word_count=metadata['word_count'],
            chunk_index=metadata['chunk_index'],
            total_chunks=metadata['total_chunks'],
            metadata=metadata['metadata'],
            embedding=None
        )
        
        return chunk
    
    def save_database(self) -> None:
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_metadata, f, indent=2, ensure_ascii=False)
            
            # Save ID mapping
            with open(self.id_mapping_path, 'w', encoding='utf-8') as f:
                json.dump(self.chunk_id_to_index, f, indent=2)
            
            logger.info(f"Saved vector database to {self.db_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save vector database: {e}")
            raise
    
    def load_database(self) -> bool:
        """
        Load FAISS index and metadata from disk
        
        Returns:
            True if successfully loaded, False otherwise
        """
        try:
            if not all(os.path.exists(path) for path in [self.index_path, self.metadata_path, self.id_mapping_path]):
                logger.info("Vector database files not found, starting with empty database")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load metadata
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.chunk_metadata = json.load(f)
            
            # Load ID mapping
            with open(self.id_mapping_path, 'r', encoding='utf-8') as f:
                self.chunk_id_to_index = json.load(f)
            
            logger.info(f"Loaded vector database with {self.index.ntotal} chunks from {self.db_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vector database: {e}")
            # Reset to empty database
            self.index = faiss.IndexFlatIP(self.embedding_dimension)
            self.chunk_metadata = []
            self.chunk_id_to_index = {}
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with database statistics
        """
        stats = {
            'total_chunks': self.index.ntotal,
            'embedding_dimension': self.embedding_dimension,
            'index_type': type(self.index).__name__,
            'subjects': {},
            'chapters': {},
            'languages': {}
        }
        
        # Analyze metadata
        for metadata in self.chunk_metadata:
            # Count by subject
            subject = metadata.get('subject', 'Unknown')
            stats['subjects'][subject] = stats['subjects'].get(subject, 0) + 1
            
            # Count by chapter
            chapter = metadata.get('chapter_name', 'Unknown')
            stats['chapters'][chapter] = stats['chapters'].get(chapter, 0) + 1
            
            # Count by language
            language = metadata.get('language', 'Unknown')
            stats['languages'][language] = stats['languages'].get(language, 0) + 1
        
        return stats
    
    def clear_database(self) -> None:
        """Clear all data from the vector database"""
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.chunk_metadata = []
        self.chunk_id_to_index = {}
        logger.info("Cleared vector database")


class SemanticSearchEngine:
    """High-level semantic search engine using FAISS vector database"""
    
    def __init__(self, config: Config):
        """
        Initialize semantic search engine
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.vector_db = FAISSVectorDatabase(config)
        
        # Try to load existing database
        self.vector_db.load_database()
    
    def add_content(self, chunks: List[ContentChunk]) -> None:
        """
        Add content chunks to the search engine
        
        Args:
            chunks: List of ContentChunk objects with embeddings
        """
        self.vector_db.add_chunks(chunks)
        self.vector_db.save_database()
    
    def search_content(self, query_embedding: np.ndarray, 
                      subject_filter: Optional[str] = None,
                      chapter_filter: Optional[str] = None,
                      top_k: int = 3) -> List[Tuple[ContentChunk, float]]:
        """
        Search for relevant content chunks
        
        Args:
            query_embedding: Query embedding vector
            subject_filter: Optional subject filter (Physics, Chemistry, Biology)
            chapter_filter: Optional chapter name filter
            top_k: Number of results to return
            
        Returns:
            List of tuples (ContentChunk, similarity_score)
        """
        # Get initial results from vector database
        results = self.vector_db.search(query_embedding, top_k * 2)  # Get more for filtering
        
        # Apply filters if specified
        filtered_results = []
        for chunk, score in results:
            if subject_filter and chunk.subject != subject_filter:
                continue
            if chapter_filter and chunk.chapter_name != chapter_filter:
                continue
            filtered_results.append((chunk, score))
        
        # Return top_k results
        return filtered_results[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return self.vector_db.get_database_stats()


def main():
    """Main function for testing the vector database"""
    from .content_processor import NCERTContentProcessor
    
    config = Config()
    
    # Initialize components
    processor = NCERTContentProcessor(config)
    search_engine = SemanticSearchEngine(config)
    
    # Check if we have existing data
    stats = search_engine.get_stats()
    if stats['total_chunks'] == 0:
        print("No existing data found. Processing sample content...")
        
        # Process sample content
        chunks = processor.process_sample_content()
        
        # Add to search engine
        search_engine.add_content(chunks)
        
        print(f"Added {len(chunks)} chunks to vector database")
    else:
        print(f"Found existing database with {stats['total_chunks']} chunks")
    
    # Display database statistics
    stats = search_engine.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Subjects: {stats['subjects']}")
    print(f"Chapters: {stats['chapters']}")
    print(f"Languages: {stats['languages']}")


if __name__ == "__main__":
    main()