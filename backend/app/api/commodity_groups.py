"""API endpoints for commodity groups."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import CommodityGroup as CommodityGroupSchema, CommodityClassification
from app.models import CommodityGroup
from app.services.commodity_classifier import commodity_classifier


router = APIRouter()


class ClassifyTextRequest(BaseModel):
    """Request body for text classification."""
    text: str


@router.get("", response_model=List[CommodityGroupSchema])
def list_commodity_groups(
    db: Session = Depends(get_db)
):
    """
    List all available commodity groups.

    Args:
        db: Database session

    Returns:
        List of all commodity groups
    """
    commodity_groups = db.query(CommodityGroup).order_by(
        CommodityGroup.category, CommodityGroup.name
    ).all()
    return commodity_groups


@router.get("/search", response_model=List[CommodityGroupSchema])
def search_commodity_groups(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db)
):
    """
    Search commodity groups by name or category.

    Args:
        q: Search query string
        db: Database session

    Returns:
        List of matching commodity groups
    """
    search_term = f"%{q}%"
    commodity_groups = db.query(CommodityGroup).filter(
        (CommodityGroup.name.ilike(search_term)) |
        (CommodityGroup.category.ilike(search_term))
    ).order_by(
        CommodityGroup.category, CommodityGroup.name
    ).all()

    return commodity_groups


@router.post("/classify", response_model=CommodityClassification)
def classify_text(
    request: ClassifyTextRequest,
    db: Session = Depends(get_db)
):
    """
    Classify arbitrary text into a commodity group.

    This endpoint uses AI to determine the most appropriate commodity group
    for the given text description.

    Args:
        request: Text to classify
        db: Database session

    Returns:
        Classification result with commodity group and confidence
    """
    try:
        # Get all commodity groups
        commodity_groups = db.query(CommodityGroup).all()

        # Classify the text
        classification = commodity_classifier.classify_text(
            text=request.text,
            commodity_groups=commodity_groups
        )

        return classification

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to classify text: {str(e)}"
        )


@router.get("/{commodity_group_id}", response_model=CommodityGroupSchema)
def get_commodity_group(
    commodity_group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single commodity group by ID.

    Args:
        commodity_group_id: ID of the commodity group
        db: Database session

    Returns:
        Commodity group details
    """
    commodity_group = db.query(CommodityGroup).filter(
        CommodityGroup.id == commodity_group_id
    ).first()

    if not commodity_group:
        raise HTTPException(status_code=404, detail="Commodity group not found")

    return commodity_group
