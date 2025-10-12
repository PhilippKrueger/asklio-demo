"""API endpoints for procurement requests."""
from typing import List, Optional
from pathlib import Path
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new procurement request (manual input).

    Args:
        request_data: Request data
        db: Database session

    Returns:
        Created request with ID
    """
    try:
        request = request_service.create_request(
            request_data=request_data,
            db=db,
            auto_classify=True
        )
        return request
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_model=PDFUploadResponse, status_code=200)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF and extract procurement information.

    This endpoint extracts data from the PDF but does NOT create a request.
    The extracted data is returned to the client for review and editing.

    Args:
        file: PDF file upload
        db: Database session

    Returns:
        Extracted data from PDF
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Create temporary storage for PDF
    temp_dir = settings.upload_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file_path = temp_dir / file.filename

    try:
        # Save uploaded file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract data from PDF
        extracted_data = pdf_extractor.extract_from_pdf(str(temp_file_path))

        return PDFUploadResponse(
            extracted_data=extracted_data,
            message="PDF processed successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()


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
