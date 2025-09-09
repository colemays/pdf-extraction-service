from flask import Flask, request, jsonify
import PyPDF2
import pdfplumber
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
            logger.error("Missing fileBuffer in request")
            return jsonify({
                "error": "Missing fileBuffer in request", 
                "status": "error"
            }), 400
        
        file_name = data.get('fileName', 'unknown.pdf')
        logger.info(f"Processing PDF extraction request for: {file_name}")
        
        # Validate and decode base64 PDF
        try:
            file_buffer = base64.b64decode(data['fileBuffer'])
            logger.info(f"Decoded base64 buffer, size: {len(file_buffer)} bytes")
        except Exception as decode_error:
            logger.error(f"Failed to decode base64: {str(decode_error)}")
            return jsonify({
                "error": f"Invalid base64 data: {str(decode_error)}", 
                "status": "error"
            }), 400
        
        # Validate PDF header
        if len(file_buffer) < 10:
            logger.error(f"File too small: {len(file_buffer)} bytes")
            return jsonify({
                "error": f"File too small: {len(file_buffer)} bytes", 
                "status": "error"
            }), 400
            
        header = file_buffer[:10].decode('ascii', errors='ignore')
        logger.info(f"PDF header: {repr(header)}")
        
        if not header.startswith('%PDF'):
            logger.error(f"Invalid PDF header: {repr(header)}")
            return jsonify({
                "error": f"Invalid PDF header: {repr(header)}", 
                "status": "error"
            }), 400
        
        # Create BytesIO object
        pdf_file = BytesIO(file_buffer)
        
        # Try PyPDF2 first, then pdfplumber as fallback
        extracted_text = ""
        total_pages = 0
        extraction_method = "unknown"
        
        # Reset file pointer
        pdf_file.seek(0)
        
        # Try PyPDF2 first
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PyPDF2: PDF loaded successfully, {total_pages} pages")
            extraction_method = "PyPDF2"
            
            # Process each page with PyPDF2
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
                    logger.warning(f"PyPDF2 error on page {page_num}: {str(page_error)}")
                    continue
                    
        except Exception as pypdf_error:
            logger.warning(f"PyPDF2 failed: {str(pypdf_error)}, trying pdfplumber...")
            
            # Reset file pointer for pdfplumber
            pdf_file.seek(0)
            
            try:
                # Try pdfplumber as fallback
                with pdfplumber.open(pdf_file) as pdf:
                    total_pages = len(pdf.pages)
                    logger.info(f"pdfplumber: PDF loaded successfully, {total_pages} pages")
                    extraction_method = "pdfplumber"
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                extracted_text += f"\n=== Page {page_num} ===\n"
                                extracted_text += page_text.strip()
                                extracted_text += "\n\n"
                            
                            # Log progress for large PDFs
                            if page_num % 20 == 0:
                                logger.info(f"Processed {page_num}/{total_pages} pages")
                                
                        except Exception as page_error:
                            logger.warning(f"pdfplumber error on page {page_num}: {str(page_error)}")
                            continue
                            
            except Exception as pdfplumber_error:
                logger.error(f"Both PyPDF2 and pdfplumber failed")
                logger.error(f"PyPDF2 error: {str(pypdf_error)}")
                logger.error(f"pdfplumber error: {str(pdfplumber_error)}")
                return jsonify({
                    "error": f"PDF reading failed with both libraries. PyPDF2: {str(pypdf_error)}. pdfplumber: {str(pdfplumber_error)}", 
                    "status": "error"
                }), 400
        
        # Calculate some basic stats
        word_count = len(extracted_text.split()) if extracted_text else 0
        char_count = len(extracted_text)
        
        logger.info(f"Extraction complete ({extraction_method}): {total_pages} pages, {word_count} words, {char_count} characters")
        
        return jsonify({
            "extractedText": extracted_text,
            "totalPages": total_pages,
            "wordCount": word_count,
            "characterCount": char_count,
            "fileName": file_name,
            "extractionMethod": extraction_method,
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {str(e)}")
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