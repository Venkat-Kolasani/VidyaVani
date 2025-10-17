"""
NCERT Content Processing Module

This module handles the processing of NCERT textbook content including:
- Text extraction from PDFs
- Content chunking with overlap
- Metadata enrichment
- Embedding generation using OpenAI
"""

import os
import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import logging

import openai
import numpy as np
from PyPDF2 import PdfReader
import pdfplumber

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentChunk:
    """Represents a chunk of NCERT content with metadata"""
    id: str
    chapter_name: str
    section_name: str
    content_text: str
    subject: str  # Physics, Chemistry, Biology
    grade: int
    language: str
    word_count: int
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentChunk':
        """Create ContentChunk from dictionary"""
        if 'embedding' in data and data['embedding'] is not None:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)


class NCERTContentProcessor:
    """Processes NCERT content for the knowledge base"""
    
    def __init__(self, config: Config):
        self.config = config
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Content processing parameters
        self.chunk_size = config.CONTENT_CHUNK_SIZE  # 300 words
        self.overlap_size = config.CONTENT_OVERLAP   # 50 words
        
        # PDF storage directory
        self.pdf_directory = "data/ncert/pdfs"
        os.makedirs(self.pdf_directory, exist_ok=True)
        
        # Sample content for "Light - Reflection and Refraction" chapter (fallback)
        self.sample_content = self._get_sample_light_chapter_content()
    
    def _get_sample_light_chapter_content(self) -> Dict[str, str]:
        """
        Returns sample content from NCERT Class 10 Physics Chapter: Light - Reflection and Refraction
        This is used for the initial proof of concept implementation.
        """
        return {
            "10.1 Reflection of Light": """
            Light is a form of energy which enables us to see objects. Light travels in straight lines. 
            When light falls on a surface, it bounces back. This phenomenon is called reflection of light.
            
            The ray of light which falls on the surface is called the incident ray. The ray of light which 
            bounces back from the surface is called the reflected ray. The point at which the incident ray 
            strikes the surface is called the point of incidence. The perpendicular drawn at the point of 
            incidence is called the normal.
            
            Laws of Reflection:
            1. The incident ray, the reflected ray and the normal at the point of incidence all lie in the same plane.
            2. The angle of incidence is equal to the angle of reflection.
            
            The angle between the incident ray and the normal is called the angle of incidence. The angle 
            between the reflected ray and the normal is called the angle of reflection. These laws of 
            reflection are applicable to all types of reflecting surfaces including plane and curved surfaces.
            """,
            
            "10.2 Spherical Mirrors": """
            A spherical mirror is a mirror which has the shape of a piece cut out of a spherical surface. 
            There are two types of spherical mirrors: concave mirror and convex mirror.
            
            A concave mirror is a spherical mirror whose reflecting surface is curved inwards. It is also 
            called a converging mirror because it converges the light rays falling on it.
            
            A convex mirror is a spherical mirror whose reflecting surface is curved outwards. It is also 
            called a diverging mirror because it diverges the light rays falling on it.
            
            Important terms related to spherical mirrors:
            - Centre of curvature (C): The centre of the sphere of which the mirror is a part
            - Radius of curvature (R): The radius of the sphere of which the mirror is a part
            - Pole (P): The centre of the spherical mirror
            - Principal axis: The straight line passing through the pole and centre of curvature
            - Principal focus (F): The point on the principal axis where parallel rays converge after reflection
            - Focal length (f): The distance between the pole and the principal focus
            """,
            
            "10.3 Image Formation by Spherical Mirrors": """
            The image formed by a spherical mirror depends on the position of the object. The characteristics 
            of the image can be determined using ray diagrams or mirror formula.
            
            For Concave Mirrors:
            1. When object is at infinity: Image is formed at focus, real, inverted and highly diminished
            2. When object is beyond centre of curvature: Image is between F and C, real, inverted and diminished
            3. When object is at centre of curvature: Image is at C, real, inverted and same size
            4. When object is between C and F: Image is beyond C, real, inverted and enlarged
            5. When object is at focus: Image is at infinity, real, inverted and highly enlarged
            6. When object is between pole and focus: Image is behind mirror, virtual, erect and enlarged
            
            For Convex Mirrors:
            The image is always virtual, erect, diminished and formed between pole and focus, regardless 
            of the position of the object.
            
            Mirror Formula: 1/f = 1/v + 1/u
            Where f = focal length, v = image distance, u = object distance
            
            Magnification (m) = -v/u = height of image/height of object
            """,
            
            "10.4 Refraction of Light": """
            When light travels from one medium to another, it bends at the boundary between the two media. 
            This bending of light is called refraction of light.
            
            Refraction occurs because light travels at different speeds in different media. Light travels 
            fastest in vacuum, slower in air, and even slower in water and glass.
            
            Laws of Refraction (Snell's Law):
            1. The incident ray, the refracted ray and the normal at the point of incidence all lie in the same plane.
            2. The ratio of sine of angle of incidence to the sine of angle of refraction is constant for 
               a given pair of media. This constant is called the refractive index.
            
            Refractive Index (n) = sin i / sin r = c/v
            Where i = angle of incidence, r = angle of refraction, c = speed of light in vacuum, 
            v = speed of light in the medium
            
            When light goes from a rarer medium to a denser medium, it bends towards the normal.
            When light goes from a denser medium to a rarer medium, it bends away from the normal.
            """,
            
            "10.5 Refraction by Spherical Lenses": """
            A lens is a piece of transparent glass or plastic bound by two spherical surfaces. There are 
            two types of lenses: convex lens and concave lens.
            
            A convex lens is thicker at the centre than at the edges. It is also called a converging lens 
            because it converges parallel rays of light.
            
            A concave lens is thinner at the centre than at the edges. It is also called a diverging lens 
            because it diverges parallel rays of light.
            
            Important terms related to lenses:
            - Optical centre (O): The central point of the lens
            - Principal axis: The line passing through the optical centre and perpendicular to the lens
            - Principal focus: The point where parallel rays converge (convex) or appear to diverge from (concave)
            - Focal length: The distance between optical centre and principal focus
            
            Lens Formula: 1/f = 1/v - 1/u
            Power of lens (P) = 1/f (in metres), measured in dioptres (D)
            """
        }
    
    def find_ncert_pdfs(self) -> List[Dict[str, str]]:
        """
        Find NCERT PDF files in the pdf directory
        
        Returns:
            List of dictionaries with PDF file information
        """
        pdf_files = []
        
        if not os.path.exists(self.pdf_directory):
            logger.info(f"PDF directory {self.pdf_directory} not found")
            return pdf_files
        
        for filename in os.listdir(self.pdf_directory):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(self.pdf_directory, filename)
                
                # Try to extract metadata from filename
                pdf_info = self._parse_pdf_filename(filename)
                pdf_info['filepath'] = filepath
                pdf_info['filename'] = filename
                
                pdf_files.append(pdf_info)
        
        logger.info(f"Found {len(pdf_files)} PDF files in {self.pdf_directory}")
        return pdf_files
    
    def _parse_pdf_filename(self, filename: str) -> Dict[str, str]:
        """
        Parse PDF filename to extract subject, grade, and other metadata
        
        Expected formats:
        - "NCERT_Class_10_Science.pdf"
        - "Class_10_Physics.pdf" 
        - "10th_Science_Light.pdf"
        
        Args:
            filename: PDF filename
            
        Returns:
            Dictionary with parsed metadata
        """
        filename_lower = filename.lower().replace('.pdf', '')
        
        # Default values
        metadata = {
            'subject': 'Science',
            'grade': 10,
            'language': 'English',
            'chapter_hint': ''
        }
        
        # Extract grade/class
        if 'class' in filename_lower or 'grade' in filename_lower:
            import re
            grade_match = re.search(r'(?:class|grade)[\s_]*(\d+)', filename_lower)
            if grade_match:
                metadata['grade'] = int(grade_match.group(1))
        elif any(str(i) in filename_lower for i in range(6, 13)):  # Classes 6-12
            for i in range(6, 13):
                if str(i) in filename_lower:
                    metadata['grade'] = i
                    break
        
        # Extract subject
        subjects = {
            'physics': 'Physics',
            'chemistry': 'Chemistry', 
            'biology': 'Biology',
            'science': 'Science',
            'math': 'Mathematics',
            'english': 'English'
        }
        
        for key, value in subjects.items():
            if key in filename_lower:
                metadata['subject'] = value
                break
        
        # Extract chapter hints
        chapter_keywords = ['light', 'motion', 'force', 'energy', 'atom', 'acid', 'base', 'carbon', 'life']
        for keyword in chapter_keywords:
            if keyword in filename_lower:
                metadata['chapter_hint'] = keyword.title()
                break
        
        logger.debug(f"Parsed filename '{filename}' -> {metadata}")
        return metadata

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using PyPDF2 and pdfplumber as fallback
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Try PyPDF2 first
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                if text.strip():
                    logger.info(f"Successfully extracted text using PyPDF2 from {pdf_path}")
                    return text
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {pdf_path}: {e}")
        
        try:
            # Fallback to pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                logger.info(f"Successfully extracted text using pdfplumber from {pdf_path}")
                return text
        except Exception as e:
            logger.error(f"Both PDF extraction methods failed for {pdf_path}: {e}")
            raise
    
    def detect_chapters_and_sections(self, text: str) -> Dict[str, str]:
        """
        Detect chapters and sections from PDF text using pattern matching
        
        Args:
            text: Extracted PDF text
            
        Returns:
            Dictionary mapping section names to content
        """
        import re
        
        # Common NCERT chapter/section patterns
        patterns = [
            # Chapter patterns
            r'CHAPTER\s*(\d+)\s*([^\n]+)',
            r'Chapter\s*(\d+)\s*([^\n]+)',
            r'(\d+)\.\s*([A-Z][^\n]+)',
            
            # Section patterns  
            r'(\d+\.\d+)\s*([A-Z][^\n]+)',
            r'(\d+\.\d+\.\d+)\s*([A-Z][^\n]+)',
        ]
        
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line matches any section pattern
            section_found = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    if len(match.groups()) >= 2:
                        section_num = match.group(1)
                        section_title = match.group(2).strip()
                        current_section = f"{section_num} {section_title}"
                    else:
                        current_section = line
                    
                    current_content = []
                    section_found = True
                    break
            
            if not section_found:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # Filter out very short sections (likely headers/footers)
        filtered_sections = {}
        for section_name, content in sections.items():
            if len(content.split()) >= 50:  # At least 50 words
                filtered_sections[section_name] = content
        
        logger.info(f"Detected {len(filtered_sections)} sections from PDF text")
        for section_name in filtered_sections.keys():
            logger.debug(f"  - {section_name}")
        
        return filtered_sections

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (basic patterns)
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'NCERT.*?\n', '', text, flags=re.IGNORECASE)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        return text.strip()
    
    def split_into_chunks(self, text: str, section_name: str) -> List[str]:
        """
        Split text into overlapping chunks of specified word count
        
        Args:
            text: Text to split
            section_name: Name of the section for logging
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        if len(words) <= self.chunk_size:
            # If text is smaller than chunk size, return as single chunk
            chunks.append(text)
        else:
            # Create overlapping chunks
            start = 0
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                chunk_words = words[start:end]
                chunks.append(' '.join(chunk_words))
                
                # Move start position considering overlap
                if end == len(words):
                    break
                start = end - self.overlap_size
        
        logger.info(f"Split '{section_name}' into {len(chunks)} chunks")
        return chunks
    
    def generate_chunk_id(self, chapter: str, section: str, chunk_index: int) -> str:
        """
        Generate unique ID for content chunk
        
        Args:
            chapter: Chapter name
            section: Section name
            chunk_index: Index of chunk within section
            
        Returns:
            Unique chunk ID
        """
        content = f"{chapter}_{section}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def process_pdf_file(self, pdf_info: Dict[str, str]) -> List[ContentChunk]:
        """
        Process a single PDF file and create content chunks
        
        Args:
            pdf_info: Dictionary with PDF file information
            
        Returns:
            List of ContentChunk objects
        """
        logger.info(f"Processing PDF: {pdf_info['filename']}")
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_info['filepath'])
            
            if not text.strip():
                logger.error(f"No text extracted from {pdf_info['filename']}")
                return []
            
            # Clean the text
            cleaned_text = self.clean_text(text)
            
            # Detect chapters and sections
            sections = self.detect_chapters_and_sections(cleaned_text)
            
            if not sections:
                logger.warning(f"No sections detected in {pdf_info['filename']}, treating as single content")
                sections = {"Full Content": cleaned_text}
            
            # Create chunks from sections
            chunks = []
            chapter_name = pdf_info.get('chapter_hint', f"NCERT Class {pdf_info['grade']} {pdf_info['subject']}")
            
            for section_name, content_text in sections.items():
                # Clean the section content
                cleaned_content = self.clean_text(content_text)
                
                # Split into chunks
                text_chunks = self.split_into_chunks(cleaned_content, section_name)
                
                # Create ContentChunk objects
                for i, chunk_text in enumerate(text_chunks):
                    chunk_id = self.generate_chunk_id(chapter_name, section_name, i)
                    
                    chunk = ContentChunk(
                        id=chunk_id,
                        chapter_name=chapter_name,
                        section_name=section_name,
                        content_text=chunk_text,
                        subject=pdf_info['subject'],
                        grade=pdf_info['grade'],
                        language=pdf_info['language'],
                        word_count=len(chunk_text.split()),
                        chunk_index=i,
                        total_chunks=len(text_chunks),
                        metadata={
                            "source_file": pdf_info['filename'],
                            "difficulty": "medium",
                            "keywords": self._extract_keywords(chunk_text),
                            "topic_type": "theory"
                        }
                    )
                    chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {pdf_info['filename']}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_info['filename']}: {e}")
            return []

    def create_content_chunks(self, subject: str = "Physics", grade: int = 10, 
                            language: str = "English") -> List[ContentChunk]:
        """
        Create content chunks from sample NCERT content
        
        Args:
            subject: Subject name (Physics, Chemistry, Biology)
            grade: Grade level
            language: Content language
            
        Returns:
            List of ContentChunk objects
        """
        chunks = []
        chapter_name = "Light - Reflection and Refraction"
        
        for section_name, content_text in self.sample_content.items():
            # Clean the content
            cleaned_text = self.clean_text(content_text)
            
            # Split into chunks
            text_chunks = self.split_into_chunks(cleaned_text, section_name)
            
            # Create ContentChunk objects
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = self.generate_chunk_id(chapter_name, section_name, i)
                
                chunk = ContentChunk(
                    id=chunk_id,
                    chapter_name=chapter_name,
                    section_name=section_name,
                    content_text=chunk_text,
                    subject=subject,
                    grade=grade,
                    language=language,
                    word_count=len(chunk_text.split()),
                    chunk_index=i,
                    total_chunks=len(text_chunks),
                    metadata={
                        "chapter_number": "10",
                        "difficulty": "medium",
                        "keywords": self._extract_keywords(chunk_text),
                        "topic_type": "theory"
                    }
                )
                chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} content chunks for chapter '{chapter_name}'")
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract key scientific terms from text
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Common physics terms for light chapter
        physics_terms = [
            'light', 'reflection', 'refraction', 'mirror', 'lens', 'ray', 'incident', 'reflected',
            'refracted', 'normal', 'angle', 'focus', 'focal', 'concave', 'convex', 'image',
            'object', 'virtual', 'real', 'magnification', 'spherical', 'optical', 'centre',
            'curvature', 'radius', 'pole', 'axis', 'converging', 'diverging', 'medium',
            'refractive', 'index', 'snell', 'law', 'formula', 'dioptre', 'power'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for term in physics_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        return found_keywords[:10]  # Limit to top 10 keywords
    
    def generate_embeddings(self, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """
        Generate OpenAI embeddings for content chunks
        
        Args:
            chunks: List of ContentChunk objects
            
        Returns:
            List of ContentChunk objects with embeddings
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks using OpenAI")
        
        for i, chunk in enumerate(chunks):
            try:
                # Create embedding using OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk.content_text
                )
                
                # Extract embedding vector
                embedding = np.array(response.data[0].embedding)
                chunk.embedding = embedding
                
                logger.info(f"Generated embedding for chunk {i+1}/{len(chunks)} (ID: {chunk.id})")
                
            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {chunk.id}: {e}")
                # Set a zero vector as fallback
                chunk.embedding = np.zeros(1536)  # text-embedding-3-small dimension
        
        logger.info("Completed embedding generation for all chunks")
        return chunks
    
    def save_chunks_to_file(self, chunks: List[ContentChunk], filepath: str) -> None:
        """
        Save content chunks to JSON file
        
        Args:
            chunks: List of ContentChunk objects
            filepath: Path to save the JSON file
        """
        # Convert chunks to dictionaries for JSON serialization
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {filepath}")
    
    def load_chunks_from_file(self, filepath: str) -> List[ContentChunk]:
        """
        Load content chunks from JSON file
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            List of ContentChunk objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        chunks = [ContentChunk.from_dict(data) for data in chunks_data]
        logger.info(f"Loaded {len(chunks)} chunks from {filepath}")
        return chunks
    
    def process_all_content(self) -> List[ContentChunk]:
        """
        Process all available NCERT content (PDFs + sample content) and generate embeddings
        
        Returns:
            List of processed ContentChunk objects with embeddings
        """
        logger.info("Starting NCERT content processing")
        
        all_chunks = []
        
        # First, try to process PDF files
        pdf_files = self.find_ncert_pdfs()
        
        if pdf_files:
            logger.info(f"Processing {len(pdf_files)} PDF files")
            for pdf_info in pdf_files:
                pdf_chunks = self.process_pdf_file(pdf_info)
                all_chunks.extend(pdf_chunks)
        else:
            logger.info("No PDF files found, using sample content")
            # Fallback to sample content
            sample_chunks = self.create_content_chunks()
            all_chunks.extend(sample_chunks)
        
        if not all_chunks:
            logger.error("No content chunks created")
            return []
        
        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        chunks_with_embeddings = self.generate_embeddings(all_chunks)
        
        # Save to file
        output_path = "data/ncert/processed_content_chunks.json"
        self.save_chunks_to_file(chunks_with_embeddings, output_path)
        
        logger.info(f"Successfully processed {len(chunks_with_embeddings)} content chunks")
        return chunks_with_embeddings

    def process_sample_content(self) -> List[ContentChunk]:
        """
        Process the sample NCERT content and generate embeddings (for backward compatibility)
        
        Returns:
            List of processed ContentChunk objects with embeddings
        """
        logger.info("Starting NCERT content processing for sample chapter")
        
        # Create content chunks
        chunks = self.create_content_chunks()
        
        # Generate embeddings
        chunks_with_embeddings = self.generate_embeddings(chunks)
        
        # Save to file
        output_path = "data/ncert/light_reflection_refraction_chunks.json"
        self.save_chunks_to_file(chunks_with_embeddings, output_path)
        
        logger.info(f"Successfully processed {len(chunks_with_embeddings)} content chunks")
        return chunks_with_embeddings


def main():
    """Main function for testing the content processor"""
    config = Config()
    
    # Validate OpenAI API key
    if not config.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    processor = NCERTContentProcessor(config)
    
    # Process sample content
    chunks = processor.process_sample_content()
    
    print(f"\nProcessed {len(chunks)} content chunks:")
    for chunk in chunks[:3]:  # Show first 3 chunks
        print(f"\nChunk ID: {chunk.id}")
        print(f"Section: {chunk.section_name}")
        print(f"Words: {chunk.word_count}")
        print(f"Keywords: {chunk.metadata['keywords']}")
        print(f"Content preview: {chunk.content_text[:100]}...")
        print(f"Embedding shape: {chunk.embedding.shape if chunk.embedding is not None else 'None'}")


if __name__ == "__main__":
    main()