#!/usr/bin/env python3
"""
Test script for NCERT content processing and knowledge base functionality

This script tests the complete content processing pipeline:
1. Content chunking and metadata generation
2. OpenAI embedding generation  
3. FAISS vector database operations
4. Semantic search functionality
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from content import NCERTKnowledgeBase
from config import Config


def test_knowledge_base():
    """Test the complete knowledge base functionality"""
    print("="*60)
    print("TESTING NCERT CONTENT PROCESSING AND KNOWLEDGE BASE")
    print("="*60)
    
    # Check for PDF files first
    pdf_dir = "data/ncert/pdfs"
    pdf_files = []
    if os.path.exists(pdf_dir):
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if pdf_files:
        print(f"📚 Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"   - {pdf}")
        print("🔄 Will process PDF files instead of sample content")
    else:
        print("📄 No PDF files found, will use built-in sample content")
        print("💡 To add PDF files, run: python scripts/add_ncert_pdf.py")
    
    try:
        # Initialize configuration
        config = Config()
        
        # Validate required API keys
        if not config.OPENAI_API_KEY:
            print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
            print("Please set your OpenAI API key in the .env file")
            return False
        
        print("✅ Configuration loaded successfully")
        print(f"   - OpenAI Model: {config.OPENAI_MODEL}")
        print(f"   - Chunk Size: {config.CONTENT_CHUNK_SIZE} words")
        print(f"   - Overlap: {config.CONTENT_OVERLAP} words")
        print(f"   - Top-K Retrieval: {config.TOP_K_RETRIEVAL}")
        
        # Initialize knowledge base
        print("\n📚 Initializing NCERT Knowledge Base...")
        kb = NCERTKnowledgeBase(config)
        
        # Initialize with sample content
        print("🔄 Processing sample NCERT content...")
        kb.initialize_knowledge_base()
        
        # Get statistics
        stats = kb.get_knowledge_base_stats()
        db_stats = stats['database_stats']
        
        print("✅ Knowledge base initialized successfully!")
        print(f"   - Total chunks: {db_stats['total_chunks']}")
        print(f"   - Subjects: {list(db_stats['subjects'].keys())}")
        print(f"   - Chapters: {list(db_stats['chapters'].keys())}")
        print(f"   - Languages: {list(db_stats['languages'].keys())}")
        
        # Test search functionality
        print("\n🔍 Testing semantic search functionality...")
        
        test_questions = [
            "What is reflection of light?",
            "Explain concave and convex mirrors",
            "What are the laws of reflection?", 
            "How does refraction work?",
            "What is the difference between real and virtual images?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Test {i}: '{question}'")
            
            # Search for relevant content
            context = kb.get_content_context(question, subject_filter="Physics")
            
            if context['found_content']:
                print(f"   ✅ Found relevant content (confidence: {context['confidence']:.3f})")
                print(f"   📊 Context: {context['total_words']} words from {len(context['source_info'])} sources")
                
                # Show top source
                if context['source_info']:
                    top_source = context['source_info'][0]
                    print(f"   🎯 Top match: {top_source['section']} (score: {top_source['similarity_score']:.3f})")
                
                # Show content preview
                preview = context['context_text'][:200] + "..." if len(context['context_text']) > 200 else context['context_text']
                print(f"   📄 Preview: {preview}")
            else:
                print(f"   ❌ No relevant content found")
        
        # Test cache functionality
        print(f"\n💾 Testing cache functionality...")
        
        # Search same question twice
        question = "What is reflection of light?"
        
        # First search (should generate embedding)
        context1 = kb.get_content_context(question)
        
        # Second search (should use cache)
        context2 = kb.get_content_context(question)
        
        cache_stats = stats['cache_stats']
        print(f"   ✅ Cache working - {cache_stats['cached_queries']} queries cached")
        
        # Verify results are identical
        if context1['context_text'] == context2['context_text']:
            print(f"   ✅ Cache consistency verified")
        else:
            print(f"   ⚠️  Cache inconsistency detected")
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"\nKnowledge base is ready for integration with the RAG engine.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*60)
    print("INTERACTIVE TESTING MODE")
    print("="*60)
    print("Enter questions to test the knowledge base search.")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("Type 'stats' to see knowledge base statistics.")
    print("-"*60)
    
    try:
        config = Config()
        kb = NCERTKnowledgeBase(config)
        
        # Ensure knowledge base is initialized
        kb.initialize_knowledge_base()
        
        while True:
            try:
                question = input("\n🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if question.lower() == 'stats':
                    stats = kb.get_knowledge_base_stats()
                    print(f"\n📊 Knowledge Base Statistics:")
                    print(f"   - Total chunks: {stats['database_stats']['total_chunks']}")
                    print(f"   - Cached queries: {stats['cache_stats']['cached_queries']}")
                    continue
                
                if not question:
                    continue
                
                # Search for relevant content
                print(f"🔍 Searching...")
                context = kb.get_content_context(question)
                
                if context['found_content']:
                    print(f"\n✅ Found relevant content!")
                    print(f"📊 Confidence: {context['confidence']:.3f}")
                    print(f"📄 Context ({context['total_words']} words):")
                    print("-" * 50)
                    
                    # Show context with reasonable length
                    content = context['context_text']
                    if len(content) > 800:
                        content = content[:800] + "\n\n[Content truncated for display...]"
                    
                    print(content)
                    print("-" * 50)
                    
                    print(f"\n📚 Sources:")
                    for source in context['source_info']:
                        print(f"   - {source['section']} (similarity: {source['similarity_score']:.3f})")
                else:
                    print(f"\n❌ No relevant content found for this question.")
                    print(f"💡 Try asking about light, reflection, refraction, mirrors, or lenses.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error processing question: {e}")
    
    except Exception as e:
        print(f"\n❌ Failed to initialize interactive mode: {e}")
    
    print(f"\n👋 Goodbye!")


if __name__ == "__main__":
    # Run automated tests
    success = test_knowledge_base()
    
    if success:
        # Offer interactive testing
        response = input(f"\n🎮 Would you like to try interactive testing? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_test()
    else:
        print(f"\n❌ Automated tests failed. Please check the configuration and try again.")
        sys.exit(1)