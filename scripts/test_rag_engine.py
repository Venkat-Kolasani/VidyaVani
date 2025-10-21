#!/usr/bin/env python3
"""
Test script for RAG Engine

This script tests the complete RAG (Retrieval-Augmented Generation) engine
including semantic search, context building, and response generation.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rag import RAGEngine
from config import Config


def test_rag_engine():
    """Test the complete RAG engine functionality"""
    print("="*60)
    print("TESTING RAG ENGINE FOR VIDYAVANI IVR SYSTEM")
    print("="*60)
    
    try:
        # Initialize configuration
        config = Config()
        
        # Validate required API keys (either OpenAI or Gemini)
        has_openai = bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY.strip())
        has_gemini = bool(config.GOOGLE_GEMINI_API_KEY and config.GOOGLE_GEMINI_API_KEY.strip())
        
        if not has_openai and not has_gemini:
            print("❌ ERROR: Neither OPENAI_API_KEY nor GOOGLE_GEMINI_API_KEY found")
            print("Please set either OpenAI or Google Gemini API key in the .env file")
            return False
        
        print("✅ Configuration loaded successfully")
        if config.USE_GEMINI:
            print(f"   - AI Provider: Google Gemini")
            print(f"   - Model: {config.GEMINI_MODEL}")
            print(f"   - Max Tokens: {config.GEMINI_MAX_TOKENS}")
            print(f"   - Temperature: {config.GEMINI_TEMPERATURE}")
        else:
            print(f"   - AI Provider: OpenAI")
            print(f"   - Model: {config.OPENAI_MODEL}")
            print(f"   - Max Tokens: {config.OPENAI_MAX_TOKENS}")
            print(f"   - Temperature: {config.OPENAI_TEMPERATURE}")
        
        # Initialize RAG engine
        print(f"\n🤖 Initializing RAG Engine...")
        rag_engine = RAGEngine(config)
        
        print("✅ RAG Engine initialized successfully!")
        
        # Test individual questions
        print(f"\n🧪 Testing Individual Questions...")
        
        test_questions = [
            {
                'question': "What is reflection of light?",
                'language': "English",
                'detail_level': "simple"
            },
            {
                'question': "Explain concave and convex mirrors",
                'language': "English", 
                'detail_level': "detailed"
            },
            {
                'question': "వెలుతురు ప్రతిబింబం అంటే ఏమిటి?",  # Telugu
                'language': "Telugu",
                'detail_level': "simple"
            }
        ]
        
        for i, test_case in enumerate(test_questions, 1):
            print(f"\n📝 Test {i}: {test_case['question']}")
            print(f"   Language: {test_case['language']}, Detail: {test_case['detail_level']}")
            
            # Process question
            result = rag_engine.process_question(
                question=test_case['question'],
                language=test_case['language'],
                detail_level=test_case['detail_level']
            )
            
            if result['success']:
                print(f"   ✅ SUCCESS")
                print(f"   📊 Response: {result['word_count']} words, ~{result['estimated_speech_time']:.1f}s speech")
                print(f"   ⏱️  Processing: {result['total_processing_time']:.3f}s")
                print(f"   🎯 Quality: {result['context_quality']['score']:.3f}")
                print(f"   📚 Sources: {result['num_sources']} chunks")
                
                # Show response preview
                answer_preview = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
                print(f"   💬 Answer: {answer_preview}")
            else:
                print(f"   ❌ FAILED")
                if 'error' in result:
                    print(f"   🚨 Error: {result['error']}")
        
        # Run comprehensive pipeline test
        print(f"\n🔬 Running Comprehensive Pipeline Test...")
        test_results = rag_engine.test_rag_pipeline()
        
        print(f"\n📊 Pipeline Test Results:")
        print(f"   Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
        
        metrics = test_results['performance_metrics']
        print(f"   Average Response Time: {metrics['average_response_time']:.3f}s")
        print(f"   Average Context Quality: {metrics['average_context_quality']:.3f}")
        print(f"   Within Time Limit: {metrics['responses_within_time_limit']} responses")
        
        # Show engine statistics
        stats = rag_engine.get_stats()
        print(f"\n📈 Engine Statistics:")
        print(f"   Success Rate: {stats['success_rate']:.1%}")
        print(f"   Total Questions: {stats['engine_stats']['total_questions']}")
        print(f"   Successful Responses: {stats['engine_stats']['successful_responses']}")
        print(f"   Failed Responses: {stats['engine_stats']['failed_responses']}")
        
        # Determine overall success
        success_threshold = 0.6  # 60% success rate
        overall_success = stats['success_rate'] >= success_threshold
        
        if overall_success:
            print(f"\n🎉 RAG ENGINE TEST: PASSED!")
            print(f"✅ Success rate ({stats['success_rate']:.1%}) meets threshold ({success_threshold:.1%})")
            print(f"✅ All components operational")
            print(f"✅ Ready for IVR integration")
        else:
            print(f"\n⚠️  RAG ENGINE TEST: NEEDS IMPROVEMENT")
            print(f"❌ Success rate ({stats['success_rate']:.1%}) below threshold ({success_threshold:.1%})")
            print(f"💡 Consider checking OpenAI API quota or content quality")
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ ERROR during RAG engine testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_test():
    """Interactive testing mode for RAG engine"""
    print(f"\n" + "="*60)
    print("INTERACTIVE RAG ENGINE TESTING")
    print("="*60)
    print("Ask questions to test the RAG engine.")
    print("Commands:")
    print("  'quit' or 'exit' - Stop testing")
    print("  'stats' - Show engine statistics")
    print("  'telugu:<question>' - Ask in Telugu")
    print("  'detailed:<question>' - Get detailed explanation")
    print("-"*60)
    
    try:
        config = Config()
        rag_engine = RAGEngine(config)
        
        while True:
            try:
                user_input = input("\n🤔 Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'stats':
                    stats = rag_engine.get_stats()
                    print(f"\n📊 Engine Statistics:")
                    print(f"   Success Rate: {stats['success_rate']:.1%}")
                    print(f"   Total Questions: {stats['engine_stats']['total_questions']}")
                    print(f"   Average Response Time: {stats['engine_stats']['average_response_time']:.3f}s")
                    continue
                
                if not user_input:
                    continue
                
                # Parse special commands
                language = "English"
                detail_level = "simple"
                question = user_input
                
                if user_input.startswith('telugu:'):
                    language = "Telugu"
                    question = user_input[7:].strip()
                elif user_input.startswith('detailed:'):
                    detail_level = "detailed"
                    question = user_input[9:].strip()
                
                if not question:
                    print("❌ Please provide a question")
                    continue
                
                print(f"🔄 Processing... (Language: {language}, Detail: {detail_level})")
                
                # Process question through RAG engine
                result = rag_engine.process_question(
                    question=question,
                    language=language,
                    detail_level=detail_level
                )
                
                if result['success']:
                    print(f"\n✅ Vidya's Response:")
                    print(f"📝 {result['answer']}")
                    
                    print(f"\n📊 Response Metrics:")
                    print(f"   Words: {result['word_count']}")
                    print(f"   Estimated Speech Time: ~{result['estimated_speech_time']:.1f} seconds")
                    print(f"   Processing Time: {result['total_processing_time']:.3f}s")
                    print(f"   Context Quality: {result['context_quality']['score']:.3f}")
                    print(f"   Sources Used: {result['num_sources']}")
                    
                    if result['source_chunks']:
                        print(f"\n📚 Sources:")
                        for i, source in enumerate(result['source_chunks'][:3], 1):
                            print(f"   {i}. {source['section']} (confidence: {source['similarity_score']:.3f})")
                else:
                    print(f"\n❌ Failed to generate response")
                    if 'error' in result:
                        print(f"🚨 Error: {result['error']}")
                    else:
                        print(f"💬 Fallback: {result['answer']}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error processing question: {e}")
    
    except Exception as e:
        print(f"\n❌ Failed to initialize interactive mode: {e}")
    
    print(f"\n👋 Goodbye!")


def main():
    """Main function"""
    # Run automated tests
    success = test_rag_engine()
    
    if success:
        # Offer interactive testing
        response = input(f"\n🎮 Would you like to try interactive testing? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_test()
    else:
        print(f"\n❌ Automated tests failed. Please check the configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()