# PDF Text Extraction Service

A simple Flask service for extracting text from PDF files, designed for use with n8n workflows.

## Features

- Extract text from PDF files using PyPDF2
- RESTful API with JSON input/output
- Health check endpoint
- Error handling and logging
- Ready for deployment on free hosting platforms

## API Endpoints

### `GET /`
Health check endpoint
```json
{
  "status": "healthy",
  "service": "PDF Text Extraction Service",
  "version": "1.0.0"
}
```

### `POST /extract-pdf`
Extract text from a PDF file
```json
{
  "fileBuffer": "base64-encoded-pdf-content",
  "fileName": "document.pdf"
}
```

Response:
```json
{
  "extractedText": "Full text content...",
  "totalPages": 150,
  "wordCount": 45000,
  "characterCount": 250000,
  "fileName": "document.pdf",
  "status": "success"
}
```

### `POST /test`
Test endpoint for debugging

## Deployment

### Railway (Recommended - Free)
1. Push to GitHub repository
2. Connect to Railway
3. Deploy automatically

### Render (Free)
1. Push to GitHub repository  
2. Connect to Render
3. Deploy using render.yaml

### Docker
```bash
docker build -t pdf-service .
docker run -p 5000:5000 pdf-service
```

## Usage in n8n

Use HTTP Request node:
- **URL**: `https://your-service-url.com/extract-pdf`
- **Method**: POST
- **Body**: JSON with `fileBuffer` (base64) and `fileName`

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Service runs on http://localhost:5000# pdf-extraction-service
