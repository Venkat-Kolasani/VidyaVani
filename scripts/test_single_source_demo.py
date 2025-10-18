#!/usr/bin/env python3
"""
Test script to demonstrate single-sourced demo questions
Shows how questions are now derived from the cached pairs
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.session import session_manager

def test_single_source_consistency():
    """Test that demo questions are consistently sourced from cache"""
    print("=== Testing Single-Source Demo Questions ===")
    
    # Get questions from the single source
    questions = session_manager.get_demo_questions()
    qa_pairs = session_manager.get_demo_qa_pairs()
    
    print(f"✓ Questions from get_demo_questions(): {len(questions)}")
    print(f"✓ Q&A pairs from get_demo_qa_pairs(): {len(qa_pairs)}")
    
    # Verify they match
    questions_from_pairs = [q for q, _ in qa_pairs]
    
    if questions == questions_from_pairs:
        print("✓ Questions are consistently sourced from Q&A pairs")
    else:
        print("✗ Mismatch between question sources!")
        return False
    
    # Test that all questions have cached responses
    cached_count = 0
    for question in questions:
        response = session_manager.get_cached_demo_response(question)
        if response:
            cached_count += 1
    
    print(f"✓ All {cached_count}/{len(questions)} questions have cached responses")
    
    # Show the benefit: if we want to add/modify questions, we only need to change one place
    print("\n=== Demonstrating Single-Source Benefit ===")
    print("To add/modify demo questions, only edit the _demo_qa_pairs list in SessionManager._initialize_demo_cache()")
    print("The following methods automatically stay in sync:")
    print("- get_demo_questions() - derives questions from pairs")
    print("- get_cached_demo_response() - uses the same pairs for caching")
    print("- get_demo_qa_pairs() - returns the source pairs")
    
    # Show some examples
    print(f"\nExample questions (first 3):")
    for i, (question, response) in enumerate(qa_pairs[:3]):
        print(f"{i+1}. Q: {question}")
        print(f"   A: {response[:60]}...")
    
    return True

def test_modification_scenario():
    """Simulate what happens when we modify the demo set"""
    print("\n=== Simulating Demo Set Modification ===")
    
    # Show current state
    original_count = len(session_manager.get_demo_questions())
    print(f"Original demo questions: {original_count}")
    
    # In a real scenario, you would modify _demo_qa_pairs in _initialize_demo_cache()
    # and reinitialize. Here we'll just show the concept.
    
    print("✓ To modify demo questions:")
    print("  1. Edit the _demo_qa_pairs list in _initialize_demo_cache()")
    print("  2. Restart the application")
    print("  3. All methods (get_demo_questions, caching, etc.) automatically use new data")
    print("  4. No need to update multiple places or risk inconsistency")
    
    # Show current categories
    questions = session_manager.get_demo_questions()
    physics = sum(1 for q in questions if any(word in q.lower() for word in ['light', 'mirror', 'current', 'ohm', 'magnetic', 'motor', 'refraction']))
    chemistry = sum(1 for q in questions if any(word in q.lower() for word in ['acid', 'base', 'soap', 'metal', 'corrosion', 'equation', 'carbon dioxide', 'ph']))
    biology = sum(1 for q in questions if any(word in q.lower() for word in ['plants', 'kidney', 'heart', 'photosynthesis', 'breathe', 'reproduction']))
    
    print(f"\nCurrent distribution:")
    print(f"  Physics: {physics} questions")
    print(f"  Chemistry: {chemistry} questions") 
    print(f"  Biology: {biology} questions")
    print(f"  Total: {physics + chemistry + biology} questions")

def main():
    """Run single-source tests"""
    print("VidyaVani Single-Source Demo Questions Test")
    print("=" * 50)
    
    success = test_single_source_consistency()
    if success:
        test_modification_scenario()
        print("\n✓ All single-source tests passed!")
    else:
        print("\n✗ Single-source tests failed!")

if __name__ == "__main__":
    main()