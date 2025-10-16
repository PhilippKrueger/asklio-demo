"""API endpoints for procurement requests."""
from typing import List, Optional
import shutil
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Form, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    Request as RequestSchema,
    RequestCreate,
    RequestUpdate,
    StatusUpdate,
    MessageResponse,
    PDFUploadResponse,
    ExtractedData
)
from app.services.request_service import request_service
from app.services.pdf_extractor import pdf_extractor
from app.config import settings


router = APIRouter()


@router.post("", response_model=RequestSchema, status_code=201)
async def create_request(
    request_data: RequestCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create a new procurement request (JSON only).

    Args:
        request_data: Request data as JSON
        db: Database session

    Returns:
        Created request with ID
    """
    try:
        request = request_service.create_request(
            request_data=request_data,
            db=db
        )
        return request
    except Exception as e:
        print(f"Error creating request: {str(e)}")
        print(f"Request data: {request_data}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/with-pdf", response_model=RequestSchema, status_code=201)
async def create_request_with_pdf(
    request_data: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a new procurement request with PDF upload.

    Args:
        request_data: Request data as JSON string
        file: PDF file upload
        db: Database session

    Returns:
        Created request with ID
    """
    # Parse request data from form field
    try:
        request_obj = RequestCreate(**json.loads(request_data))
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {str(e)}")
    
    # Validate and read PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    pdf_content = await file.read()
    pdf_filename = file.filename
    
    try:
        request = request_service.create_request(
            request_data=request_obj,
            db=db,
            pdf_filename=pdf_filename,
            pdf_content=pdf_content
        )
        return request
    except Exception as e:
        print(f"Error creating request: {str(e)}")
        print(f"Request data: {request_obj}")
        raise HTTPException(status_code=400, detail=str(e))



@router.get("", response_model=List[RequestSchema])
def list_requests(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all procurement requests with optional filtering.

    Args:
        status: Optional status filter (Open, In Progress, Closed)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of requests
    """
    requests = request_service.list_requests(
        db=db,
        status=status,
        skip=skip,
        limit=limit
    )
    return requests


@router.get("/{request_id}", response_model=RequestSchema)
def get_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single request by ID.

    Args:
        request_id: ID of the request
        db: Database session

    Returns:
        Request details with order lines
    """
    request = request_service.get_request(request_id, db)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.put("/{request_id}", response_model=RequestSchema)
def update_request(
    request_id: int,
    update_data: RequestUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a request.

    Args:
        request_id: ID of the request to update
        update_data: Fields to update
        db: Database session

    Returns:
        Updated request
    """
    request = request_service.update_request(request_id, update_data, db)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.patch("/{request_id}/status", response_model=RequestSchema)
def update_status(
    request_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the status of a request.

    Args:
        request_id: ID of the request
        status_update: New status
        db: Database session

    Returns:
        Updated request
    """
    request = request_service.update_status(request_id, status_update, db)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.post("/extract", response_model=PDFUploadResponse, status_code=200)
async def extract_pdf_data(
    file: UploadFile = File(...),
    save_pdf: bool = True
):
    """
    Extract data from PDF without creating a request.

    Args:
        file: PDF file upload
        save_pdf: Whether to include PDF content in response for later storage

    Returns:
        Extracted data from PDF with optional PDF content
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Read PDF content once
    pdf_content = await file.read()
    
    # Create storage directories
    temp_dir = settings.upload_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file_path = temp_dir / file.filename

    try:
        # Save uploaded file temporarily for extraction
        with open(temp_file_path, "wb") as buffer:
            buffer.write(pdf_content)

        # Extract data from PDF (includes commodity classification)
        extracted_data = pdf_extractor.extract_from_pdf(str(temp_file_path))

        # Clean up temporary file
        temp_file_path.unlink()
        
        # Add PDF metadata to response
        response_data = PDFUploadResponse(extracted_data=extracted_data)
        
        # Store PDF content and filename in extracted_data for frontend to send back when creating request
        if save_pdf:
            extracted_data.pdf_filename = file.filename
            # Note: We'll handle the actual PDF content storage when the request is created

        return response_data

    except Exception as e:
        # Clean up file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract data from PDF: {str(e)}"
        )



@router.get("/{request_id}/download-pdf", response_class=Response)
def download_pdf(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Download the PDF associated with a request.

    Args:
        request_id: ID of the request
        db: Database session

    Returns:
        PDF file as binary response
    """
    request = request_service.get_request(request_id, db)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if not request.pdf_content:
        raise HTTPException(status_code=404, detail="No PDF associated with this request")
    
    pdf_filename = request.pdf_filename or f"request_{request_id}.pdf"
    
    return Response(
        content=request.pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={pdf_filename}"
        }
    )


@router.delete("/{request_id}", response_model=MessageResponse)
def delete_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a request.

    Args:
        request_id: ID of the request to delete
        db: Database session

    Returns:
        Success message
    """
    success = request_service.delete_request(request_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return MessageResponse(message="Request deleted successfully")
