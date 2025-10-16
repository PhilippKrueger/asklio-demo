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

### Backend
```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

- `OPENAI_API_KEY`: Required for PDF extraction and commodity classification features

## Features

- PDF data extraction for procurement requests
- Request management with status tracking
- Order line item management
- Commodity group classification
- Request validation and form management