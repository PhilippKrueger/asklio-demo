# Asklio Procurement Request Management System

## Quick Start with Docker

1. **Set up environment variables:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your OpenAI API key
   ```

2. **Start the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the applications:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development Setup

Both Docker and development environments use the same URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Backend
```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing

### Running Tests

The backend includes pytest tests for core functionality. To run the tests:

```bash
cd backend
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run a specific test file:
```bash
uv run pytest tests/test_extraction.py
```

Run tests with coverage:
```bash
uv run pytest --cov=. --cov-report=html
```

## Environment Variables

- `OPENAI_API_KEY`: Required for PDF extraction and commodity classification features

## Features

- PDF data extraction for procurement requests
- Request management with status tracking
- Order line item management
- Commodity group classification
- Request validation and form management