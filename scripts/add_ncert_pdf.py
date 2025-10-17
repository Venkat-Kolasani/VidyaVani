#!/usr/bin/env python3
"""
Script to add and process NCERT PDF files

This script helps users add NCERT PDF files to the system and process them
into the knowledge base.
"""

import sys
import os
import shutil

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from content import NCERTKnowledgeBase
from config import Config


def setup_pdf_directory():
    """Create the PDF directory if it doesn't exist"""
    pdf_dir = "data/ncert/pdfs"
    os.makedirs(pdf_dir, exist_ok=True)
    return pdf_dir


def list_existing_pdfs():
    """List existing PDF files"""
    pdf_dir = "data/ncert/pdfs"
    
    if not os.path.exists(pdf_dir):
        print("📁 PDF directory doesn't exist yet")
        return []
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if pdf_files:
        print(f"📚 Found {len(pdf_files)} existing PDF files:")
        for i, filename in enumerate(pdf_files, 1):
            file_path = os.path.join(pdf_dir, filename)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"   {i}. {filename} ({file_size:.1f} MB)")
    else:
        print("📁 No PDF files found in data/ncert/pdfs/")
    
    return pdf_files


def add_pdf_file(source_path: str) -> bool:
    """
    Add a PDF file to the system
    
    Args:
        source_path: Path to the source PDF file
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(source_path):
        print(f"❌ File not found: {source_path}")
        return False
    
    if not source_path.lower().endswith('.pdf'):
        print(f"❌ File is not a PDF: {source_path}")
        return False
    
    # Setup destination
    pdf_dir = setup_pdf_directory()
    filename = os.path.basename(source_path)
    dest_path = os.path.join(pdf_dir, filename)
    
    # Check if file already exists
    if os.path.exists(dest_path):
        response = input(f"📄 File '{filename}' already exists. Overwrite? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return False
    
    try:
        # Copy file
        shutil.copy2(source_path, dest_path)
        file_size = os.path.getsize(dest_path) / (1024 * 1024)  # MB
        print(f"✅ Successfully added: {filename} ({file_size:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to copy file: {e}")
        return False


def process_pdfs():
    """Process all PDF files in the system"""
    print("\n🔄 Processing NCERT PDF files...")
    
    try:
        config = Config()
        
        # Validate OpenAI API key
        if not config.OPENAI_API_KEY:
            print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
            print("Please set your OpenAI API key in the .env file")
            return False
        
        # Initialize knowledge base
        kb = NCERTKnowledgeBase(config)
        
        # Process content (will use PDFs if available, sample content as fallback)
        kb.initialize_knowledge_base(force_rebuild=True)
        
        # Show results
        stats = kb.get_knowledge_base_stats()
        db_stats = stats['database_stats']
        
        print(f"\n✅ Processing completed successfully!")
        print(f"📊 Results:")
        print(f"   - Total chunks: {db_stats['total_chunks']}")
        print(f"   - Subjects: {list(db_stats['subjects'].keys())}")
        print(f"   - Chapters: {len(db_stats['chapters'])} chapters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_mode():
    """Interactive mode for adding and processing PDFs"""
    print("="*60)
    print("NCERT PDF MANAGEMENT SYSTEM")
    print("="*60)
    
    while True:
        print(f"\n📋 Options:")
        print(f"1. List existing PDF files")
        print(f"2. Add a new PDF file")
        print(f"3. Process all PDF files")
        print(f"4. Exit")
        
        choice = input(f"\n🤔 Choose an option (1-4): ").strip()
        
        if choice == '1':
            print(f"\n📚 Existing PDF Files:")
            list_existing_pdfs()
            
        elif choice == '2':
            pdf_path = input(f"\n📄 Enter path to PDF file: ").strip()
            if pdf_path:
                # Handle quoted paths
                pdf_path = pdf_path.strip('"\'')
                add_pdf_file(pdf_path)
            
        elif choice == '3':
            process_pdfs()
            
        elif choice == '4':
            print(f"\n👋 Goodbye!")
            break
            
        else:
            print(f"❌ Invalid choice. Please select 1-4.")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == 'list':
            list_existing_pdfs()
        elif sys.argv[1] == 'add' and len(sys.argv) > 2:
            pdf_path = sys.argv[2]
            if add_pdf_file(pdf_path):
                print(f"\n💡 Run 'python scripts/add_ncert_pdf.py process' to process the PDF")
        elif sys.argv[1] == 'process':
            process_pdfs()
        else:
            print(f"Usage:")
            print(f"  python scripts/add_ncert_pdf.py list           # List existing PDFs")
            print(f"  python scripts/add_ncert_pdf.py add <path>     # Add a PDF file")
            print(f"  python scripts/add_ncert_pdf.py process        # Process all PDFs")
            print(f"  python scripts/add_ncert_pdf.py               # Interactive mode")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()