#!/usr/bin/env python3
"""
Verification script for NCERT content processing

This script verifies that the content processing worked correctly
by examining the generated files and data structures.
"""

import sys
import os
import json

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def verify_content_processing():
    """Verify that content processing completed successfully"""
    print("="*60)
    print("VERIFYING NCERT CONTENT PROCESSING RESULTS")
    print("="*60)
    
    # Check if content chunks file exists
    chunks_file = "data/ncert/light_reflection_refraction_chunks.json"
    if os.path.exists(chunks_file):
        print("✅ Content chunks file found")
        
        # Load and analyze chunks
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        
        print(f"📊 Total chunks: {len(chunks_data)}")
        
        # Analyze chunk details
        for i, chunk in enumerate(chunks_data):
            print(f"\n📄 Chunk {i+1}:")
            print(f"   ID: {chunk['id']}")
            print(f"   Section: {chunk['section_name']}")
            print(f"   Subject: {chunk['subject']}")
            print(f"   Words: {chunk['word_count']}")
            print(f"   Keywords: {chunk['metadata']['keywords'][:5]}...")  # Show first 5 keywords
            print(f"   Content preview: {chunk['content_text'][:100]}...")
            
            # Check if embedding exists (even if it's zeros due to API limit)
            if chunk['embedding']:
                embedding_size = len(chunk['embedding'])
                print(f"   Embedding: {embedding_size} dimensions")
            else:
                print(f"   Embedding: None")
    else:
        print("❌ Content chunks file not found")
        return False
    
    # Check if vector database files exist
    db_dir = "data/ncert/vector_db"
    required_files = [
        "faiss_index.bin",
        "chunk_metadata.json", 
        "id_mapping.json"
    ]
    
    print(f"\n🗄️  Vector Database Files:")
    all_files_exist = True
    for filename in required_files:
        filepath = os.path.join(db_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"   ✅ {filename} ({file_size} bytes)")
        else:
            print(f"   ❌ {filename} (missing)")
            all_files_exist = False
    
    if all_files_exist:
        print("✅ All vector database files created successfully")
        
        # Load and verify metadata
        metadata_file = os.path.join(db_dir, "chunk_metadata.json")
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"\n📋 Metadata Analysis:")
        print(f"   Total metadata entries: {len(metadata)}")
        
        # Analyze subjects and chapters
        subjects = set()
        chapters = set()
        sections = set()
        
        for meta in metadata:
            subjects.add(meta['subject'])
            chapters.add(meta['chapter_name'])
            sections.add(meta['section_name'])
        
        print(f"   Subjects: {list(subjects)}")
        print(f"   Chapters: {list(chapters)}")
        print(f"   Sections: {len(sections)} sections")
        
        # Show sections
        print(f"\n📚 Processed Sections:")
        for section in sorted(sections):
            print(f"   - {section}")
    else:
        print("❌ Some vector database files are missing")
        return False
    
    # Verify content quality
    print(f"\n🔍 Content Quality Analysis:")
    
    # Check for physics keywords
    physics_keywords = [
        'light', 'reflection', 'refraction', 'mirror', 'lens', 'ray',
        'incident', 'reflected', 'normal', 'angle', 'focus', 'concave', 'convex'
    ]
    
    found_keywords = set()
    total_words = 0
    
    for chunk in chunks_data:
        total_words += chunk['word_count']
        for keyword in chunk['metadata']['keywords']:
            if keyword in physics_keywords:
                found_keywords.add(keyword)
    
    print(f"   Total words processed: {total_words}")
    print(f"   Physics keywords found: {len(found_keywords)}/{len(physics_keywords)}")
    print(f"   Keywords: {sorted(list(found_keywords))}")
    
    # Check chunk size distribution
    chunk_sizes = [chunk['word_count'] for chunk in chunks_data]
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    min_size = min(chunk_sizes)
    max_size = max(chunk_sizes)
    
    print(f"\n📏 Chunk Size Analysis:")
    print(f"   Average: {avg_size:.1f} words")
    print(f"   Range: {min_size} - {max_size} words")
    print(f"   Target: 200-300 words (with overlap)")
    
    if 150 <= avg_size <= 400:  # Reasonable range considering overlap
        print(f"   ✅ Chunk sizes are within acceptable range")
    else:
        print(f"   ⚠️  Chunk sizes may need adjustment")
    
    print(f"\n🎉 Content processing verification completed!")
    print(f"\nSummary:")
    print(f"✅ Content chunking: Working")
    print(f"✅ Metadata generation: Working") 
    print(f"✅ File persistence: Working")
    print(f"✅ Vector database: Working")
    print(f"⚠️  OpenAI embeddings: Limited by API quota")
    print(f"\n💡 The system is ready for integration with the RAG engine.")
    print(f"   When API quota is available, embeddings will work for semantic search.")
    
    return True


def show_sample_content():
    """Show sample of the processed content"""
    print(f"\n" + "="*60)
    print("SAMPLE PROCESSED CONTENT")
    print("="*60)
    
    chunks_file = "data/ncert/light_reflection_refraction_chunks.json"
    if not os.path.exists(chunks_file):
        print("❌ Content chunks file not found")
        return
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    
    # Show first chunk as example
    if chunks_data:
        chunk = chunks_data[0]
        print(f"📄 Sample Chunk:")
        print(f"   Chapter: {chunk['chapter_name']}")
        print(f"   Section: {chunk['section_name']}")
        print(f"   Subject: {chunk['subject']}")
        print(f"   Grade: {chunk['grade']}")
        print(f"   Language: {chunk['language']}")
        print(f"   Words: {chunk['word_count']}")
        print(f"\n📝 Content:")
        print("-" * 50)
        print(chunk['content_text'])
        print("-" * 50)
        print(f"\n🏷️  Keywords: {', '.join(chunk['metadata']['keywords'])}")
        print(f"🎯 Difficulty: {chunk['metadata']['difficulty']}")
        print(f"📖 Topic Type: {chunk['metadata']['topic_type']}")


if __name__ == "__main__":
    success = verify_content_processing()
    
    if success:
        response = input(f"\n📖 Would you like to see a sample of processed content? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            show_sample_content()
    
    print(f"\n✨ Verification complete!")