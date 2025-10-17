# NCERT PDF Files Directory

This directory is for storing NCERT textbook PDF files that will be processed by the VidyaVani system.

## How to Add PDF Files

### Method 1: Using the Script (Recommended)
```bash
# Interactive mode
python scripts/add_ncert_pdf.py

# Command line mode
python scripts/add_ncert_pdf.py add /path/to/your/ncert_book.pdf
python scripts/add_ncert_pdf.py process
```

### Method 2: Manual Copy
1. Copy your NCERT PDF files directly to this directory
2. Run the processing script:
   ```bash
   python scripts/add_ncert_pdf.py process
   ```

## Supported PDF Formats

The system works best with:
- **NCERT Class 6-12 textbooks**
- **Science subjects**: Physics, Chemistry, Biology
- **Clear, text-based PDFs** (not scanned images)

## Filename Conventions

For best results, use descriptive filenames:
- `NCERT_Class_10_Science.pdf`
- `Class_10_Physics.pdf`
- `10th_Science_Light_Chapter.pdf`

The system will automatically detect:
- **Grade/Class** from numbers (6-12)
- **Subject** from keywords (Physics, Chemistry, Biology, Science)
- **Chapter hints** from keywords (Light, Motion, Force, etc.)

## Processing Results

After processing, the system will:
1. **Extract text** from PDF files
2. **Detect chapters and sections** automatically
3. **Create content chunks** (200-300 words with overlap)
4. **Generate embeddings** using OpenAI
5. **Build vector database** for semantic search

## File Size Recommendations

- **Individual files**: Up to 50MB recommended
- **Total content**: Start with 1-2 textbooks for testing
- **Expansion**: Add more content after verifying the pipeline works

## Troubleshooting

### PDF Text Extraction Issues
- Ensure PDFs contain selectable text (not just images)
- Try different PDF versions if extraction fails
- Check PDF file integrity

### Processing Errors
- Verify OpenAI API key is set in `.env` file
- Check available API quota
- Review logs for specific error messages

### Performance
- Large PDFs may take several minutes to process
- Embedding generation requires API calls (costs apply)
- Vector database building is automatic

## Current Status

- ✅ **PDF Processing**: Ready
- ✅ **Text Extraction**: PyPDF2 + pdfplumber fallback
- ✅ **Chapter Detection**: Automatic pattern matching
- ✅ **Content Chunking**: 200-300 words with 50-word overlap
- ✅ **Embedding Generation**: OpenAI text-embedding-3-small
- ✅ **Vector Database**: FAISS with cosine similarity

## Next Steps

1. **Add your NCERT PDF files** to this directory
2. **Run the processing script** to build the knowledge base
3. **Test semantic search** with sample questions
4. **Integrate with RAG engine** for the IVR system

For questions or issues, check the main project documentation or logs.