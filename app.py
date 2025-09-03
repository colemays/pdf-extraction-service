from flask import Flask, request, jsonify
import PyPDF2
import base64
from io import BytesIO
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "PDF Text Extraction Service",
        "version": "1.0.0"
    })

@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    try:
        # Get JSON data from request
        data = request.json
        
        if not data or 'fileBuffer' not in data:
            return jsonify({
                "error": "Missing fileBuffer in request", 
                "status": "error"
            }), 400
        
        # Decode base64 PDF
        logger.info("Processing PDF extraction request")
        file_buffer = base64.b64decode(data['fileBuffer'])
        pdf_file = BytesIO(file_buffer)
        
        # Extract text using PyPDF2
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
        extracted_text = ""
        
        logger.info(f"PDF has {total_pages} pages")
        
        # Process each page
        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    extracted_text += f"\n=== Page {page_num} ===\n"
                    extracted_text += page_text.strip()
                    extracted_text += "\n\n"
                
                # Log progress for large PDFs
                if page_num % 20 == 0:
                    logger.info(f"Processed {page_num}/{total_pages} pages")
                    
            except Exception as page_error:
                logger.warning(f"Error processing page {page_num}: {str(page_error)}")
                continue
        
        # Calculate some basic stats
        word_count = len(extracted_text.split()) if extracted_text else 0
        char_count = len(extracted_text)
        
        logger.info(f"Extraction complete: {total_pages} pages, {word_count} words, {char_count} characters")
        
        return jsonify({
            "extractedText": extracted_text,
            "totalPages": total_pages,
            "wordCount": word_count,
            "characterCount": char_count,
            "fileName": data.get('fileName', 'unknown.pdf'),
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return jsonify({
            "error": f"PDF processing failed: {str(e)}", 
            "status": "error"
        }), 500

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    try:
        data = request.json
        return jsonify({
            "received_keys": list(data.keys()) if data else [],
            "content_length": len(data.get('fileBuffer', '')) if data and 'fileBuffer' in data else 0,
            "status": "test_success"
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "test_error"}), 500

if __name__ == '__main__':
    # Use environment port or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)