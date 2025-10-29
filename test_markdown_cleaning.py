#!/usr/bin/env python3
"""Test markdown cleaning function"""

import re

def clean_markdown_formatting(text):
    """Remove markdown formatting from text for voice/plain text display"""
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove code blocks (```code```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # Remove inline code (`code`)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove headers (# Header)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove links [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    return text.strip()

# Test with the example text
test_text = """Hello there! That's a great question! A solenoid is basically a long coil of wire that creates a strong magnetic field inside it when an electric current passes through. This means it acts like a temporary magnet, or an **electromagnet**, whose magnetic properties can be switched on or off and its strength controlled. Because of this versatile nature, solenoids are widely used in many everyday devices like **electric bells**, automatic **door locks**, and even in **valves** to control the flow of liquids or gases. Isn't it fascinating how a simple coil of wire can be so powerful?"""

print("Original text:")
print(test_text)
print("\n" + "="*60 + "\n")

cleaned = clean_markdown_formatting(test_text)
print("Cleaned text:")
print(cleaned)
print("\n" + "="*60 + "\n")

# Check if asterisks are removed
if "**" in cleaned:
    print("❌ FAILED: Still contains **")
else:
    print("✅ PASSED: No ** found")
