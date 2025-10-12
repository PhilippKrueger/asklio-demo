# Complete Implementation Plan - Procurement Request System

## Project Structure
```
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings (OpenAI key, DB path)
│   │   ├── database.py                # SQLAlchemy setup
│   │   ├── models.py                  # DB models (SQLAlchemy)
│   │   ├── schemas.py                 # Pydantic schemas (API contracts)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── requests.py            # Request endpoints
│   │   │   └── commodity_groups.py    # Commodity group endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_extractor.py       # LangChain PDF extraction
│   │   │   ├── commodity_classifier.py # OpenAI classification
│   │   │   └── request_service.py     # Business logic
│   │   └── uploads/                   # PDF storage directory
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_extraction.py
│   │   └── test_api.py
│   ├── pyproject.toml                 # uv project file
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                    # Shadcn components
│   │   │   ├── RequestForm.tsx
│   │   │   ├── RequestList.tsx
│   │   │   └── PDFUpload.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client
│   │   │   └── utils.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Technology Stack (Finalized)

### Backend
- **Language**: Python 3.11+
- **Package Manager**: uv
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **PDF Processing**: LangChain with PyPDFLoader
- **AI**: OpenAI GPT-4 (via LangChain)
- **Validation**: Pydantic v2
- **File Upload**: FastAPI UploadFile with filesystem storage

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Components**: Shadcn/ui
- **HTTP Client**: Axios or Fetch API
- **Routing**: React Router (if needed)

## Database Schema (Final)

```sql
-- Commodity Groups (pre-populated from README)
CREATE TABLE commodity_groups (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL
);

-- Procurement Requests
CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requestor_name TEXT NOT NULL,
    title TEXT NOT NULL,
    vendor_name TEXT NOT NULL,
    vat_id TEXT,
    commodity_group_id INTEGER,
    commodity_group_confidence REAL,  -- 0.0 to 1.0
    department TEXT,
    total_cost REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Open',  -- Open, In Progress, Closed
    pdf_path TEXT,
    pdf_filename TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (commodity_group_id) REFERENCES commodity_groups(id)
);

-- Order Lines (line items from vendor offers)
CREATE TABLE order_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    position_description TEXT NOT NULL,
    unit_price REAL NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);

-- Status History (audit trail for status changes)
CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);
```

## API Endpoints (RESTful)

### Requests
- `POST /api/requests` - Create request (manual input)
- `POST /api/requests/upload` - Upload PDF and extract data
- `GET /api/requests` - List all requests (with filtering)
- `GET /api/requests/{id}` - Get single request with order lines
- `PATCH /api/requests/{id}/status` - Update status
- `PUT /api/requests/{id}` - Update entire request
- `DELETE /api/requests/{id}` - Delete request

### Commodity Groups
- `GET /api/commodity-groups` - List all commodity groups
- `GET /api/commodity-groups/search?q={query}` - Search commodity groups
- `POST /api/commodity-groups/classify` - Classify text into commodity group

### Utility
- `GET /api/uploads/{filename}` - Serve uploaded PDFs

## Pydantic Schemas (API Contracts)

```python
# Request Schemas
class OrderLineBase(BaseModel):
    position_description: str
    unit_price: float
    amount: float
    unit: str
    total_price: float

class OrderLineCreate(OrderLineBase):
    pass

class OrderLine(OrderLineBase):
    id: int
    request_id: int

    class Config:
        from_attributes = True

class RequestBase(BaseModel):
    requestor_name: str
    title: str
    vendor_name: str
    vat_id: Optional[str] = None
    department: Optional[str] = None
    total_cost: float

class RequestCreate(RequestBase):
    order_lines: List[OrderLineCreate]
    commodity_group_id: Optional[int] = None

class RequestUpdate(BaseModel):
    requestor_name: Optional[str] = None
    title: Optional[str] = None
    vendor_name: Optional[str] = None
    vat_id: Optional[str] = None
    department: Optional[str] = None
    total_cost: Optional[float] = None
    commodity_group_id: Optional[int] = None

class StatusUpdate(BaseModel):
    status: Literal["Open", "In Progress", "Closed"]

class Request(RequestBase):
    id: int
    commodity_group_id: Optional[int]
    commodity_group_confidence: Optional[float]
    status: str
    pdf_path: Optional[str]
    pdf_filename: Optional[str]
    created_at: datetime
    updated_at: datetime
    order_lines: List[OrderLine]

    class Config:
        from_attributes = True

# Extraction Schema (from PDF)
class ExtractedData(BaseModel):
    vendor_name: str
    vat_id: Optional[str] = None
    department: Optional[str] = None
    order_lines: List[OrderLineCreate]
    total_cost: float
    confidence: float  # Overall extraction confidence

# Commodity Classification
class CommodityClassification(BaseModel):
    commodity_group_id: int
    commodity_group_name: str
    confidence: float
    reasoning: Optional[str] = None
```

## LangChain PDF Extraction Strategy

### Approach: Structured Output with Pydantic
```python
from langchain.document_loaders import PyPDFLoader
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate

# 1. Load PDF
loader = PyPDFLoader(pdf_path)
documents = loader.load()
text = "\n".join([doc.page_content for doc in documents])

# 2. Create structured parser
parser = PydanticOutputParser(pydantic_object=ExtractedData)

# 3. Prompt engineering
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at extracting procurement information from vendor offers.
    Extract the following information accurately:
    - Vendor name and VAT ID
    - Department (if mentioned)
    - All order line items (description, unit price, amount, unit, total)
    - Total cost

    {format_instructions}
    """),
    ("user", "Extract information from this vendor offer:\n\n{text}")
])

# 4. Execute extraction
llm = ChatOpenAI(model="gpt-4", temperature=0)
chain = prompt | llm | parser
result = chain.invoke({
    "text": text,
    "format_instructions": parser.get_format_instructions()
})
```

### Confidence Scoring
- Use OpenAI function calling with confidence scoring
- Calculate based on:
  - Number of fields successfully extracted
  - Presence of validation markers (currency symbols, VAT ID format)
  - GPT-4's internal confidence (if available via logprobs)
  - Simple heuristic: `confidence = fields_extracted / total_required_fields`

## Commodity Group Classification (Option B)

### Strategy: Direct GPT Classification
```python
def classify_commodity_group(request_data: RequestCreate) -> CommodityClassification:
    """
    Send request context to GPT with all 50 commodity groups.
    Ask it to pick the most relevant one.
    """

    # Load all commodity groups from DB
    commodity_groups = get_all_commodity_groups()

    # Format for prompt
    groups_text = "\n".join([
        f"{g.id}: {g.category} - {g.name}"
        for g in commodity_groups
    ])

    prompt = f"""
    Based on the following procurement request, select the SINGLE most appropriate commodity group.

    Request Information:
    - Title: {request_data.title}
    - Vendor: {request_data.vendor_name}
    - Items: {[line.position_description for line in request_data.order_lines]}

    Available Commodity Groups:
    {groups_text}

    Return ONLY the commodity group ID and your confidence (0.0 to 1.0).
    Also provide a brief reasoning.
    """

    # Use structured output
    response = llm.invoke(prompt)
    return CommodityClassification(...)
```

## Document Storage Implementation

### Approach: Filesystem + Path in DB
```python
UPLOAD_DIR = Path("backend/app/uploads")

async def save_upload_file(upload_file: UploadFile, request_id: int) -> str:
    """
    Save uploaded PDF to: backend/app/uploads/{request_id}/{filename}
    Returns: Relative path stored in DB
    """
    request_dir = UPLOAD_DIR / str(request_id)
    request_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_filename = secure_filename(upload_file.filename)
    file_path = request_dir / safe_filename

    # Save file
    with open(file_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)

    # Return relative path for DB storage
    return f"uploads/{request_id}/{safe_filename}"
```

## Implementation Phases

### Phase 1: Backend Foundation (Days 1-2)
1. Initialize backend with `uv init`
2. Set up FastAPI app structure
3. Configure SQLAlchemy + SQLite
4. Create database models
5. Write migration/seed script for commodity groups
6. Create Pydantic schemas

### Phase 2: PDF Extraction (Days 2-3)
1. Set up LangChain with OpenAI
2. Implement PDF extraction service
3. Test with 3 example PDFs
4. Add confidence scoring
5. Handle extraction errors gracefully

### Phase 3: API Endpoints (Days 3-4)
1. Implement request CRUD endpoints
2. Add PDF upload endpoint with extraction
3. Implement commodity group endpoints
4. Add status update endpoint
5. Test all endpoints with realistic data

### Phase 4: Commodity Classification (Day 4)
1. Implement GPT-based classification
2. Add override capability (manual selection)
3. Store confidence scores
4. Test classification accuracy

### Phase 5: Frontend Minimal (Days 5-6)
1. Initialize React + Vite + TypeScript
2. Set up Tailwind + Shadcn/ui
3. Create PDF upload component
4. Create request form (with extracted data preview)
5. Create request list view with status updates
6. Show confidence scores in UI

### Phase 6: Testing & Refinement (Day 7)
1. Integration testing
2. Error handling improvements
3. UI polish
4. Documentation
5. Local deployment verification

## Configuration

### Environment Variables (.env)
```bash
# OpenAI
OPENAI_API_KEY=sk-proj-...

# Database
DATABASE_URL=sqlite:///./procurement.db

# File Upload
UPLOAD_DIR=./app/uploads
MAX_UPLOAD_SIZE_MB=10

# API
API_PREFIX=/api
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### FastAPI Configuration
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str = "sqlite:///./procurement.db"
    upload_dir: Path = Path("./app/uploads")
    max_upload_size_mb: int = 10

    class Config:
        env_file = ".env"

settings = Settings()
```

## Validation & Error Handling

### Key Validations
1. **PDF Upload**: File type (only .pdf), size limit (10MB)
2. **VAT ID**: German format `DE[0-9]{9}` (regex validation)
3. **Total Cost**: Must match sum of order line totals (tolerance: 0.01)
4. **Status Transitions**: Only allow valid transitions (Open → In Progress → Closed)
5. **Confidence Score**: Always 0.0 ≤ confidence ≤ 1.0

### Error Responses
```python
# Standard error format
{
    "detail": "Human readable error message",
    "error_code": "INVALID_VAT_ID",
    "field": "vat_id"  # if field-specific
}
```

## Testing Strategy

### Backend Tests
1. **Unit Tests**: PDF extraction, commodity classification
2. **Integration Tests**: API endpoints with test DB
3. **Test Data**: Use the 3 provided PDFs

### Frontend Tests
- Manual testing initially (MVP phase)
- Focus on extraction preview and confidence score display

## Deployment (Local)

### Backend
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

### Access
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

---

## Decision Summary

| Decision Point | Choice | Rationale |
|---------------|--------|-----------|
| Backend Framework | FastAPI | Modern, async, auto-docs, type hints |
| Database | SQLite + SQLAlchemy | Simple deployment, production-ready ORM |
| Database Schema | Normalized (3 tables) | Queryable, maintainable, audit trail |
| PDF Extraction | LangChain + PyPDFLoader + GPT-4 | Text-based PDFs, structured output |
| Commodity Classification | Direct GPT classification (Option B) | Simple, accurate, no vector DB needed |
| Document Storage | Filesystem + path in DB | Industry standard, debuggable |
| Confidence Scoring | Field-based + GPT metadata | Transparent, helps users validate |
| Authentication | None | Not required per specs |
| API Style | REST + OpenAPI | FastAPI default, well-documented |
| Frontend Components | Shadcn/ui | Modern, customizable, TypeScript |

---

## Ready to Build!

All architectural decisions are finalized. The implementation can proceed phase by phase, starting with the backend foundation.
