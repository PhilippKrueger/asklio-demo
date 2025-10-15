"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class CommodityGroupBase(BaseModel):
    """Base commodity group schema."""
    category: str
    name: str


class CommodityGroup(CommodityGroupBase):
    """Commodity group with ID for responses."""
    id: int

    model_config = {"from_attributes": True}


class CommodityClassification(BaseModel):
    """Result of commodity group classification."""
    commodity_group_id: int
    commodity_group_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class OrderLineBase(BaseModel):
    """Base order line schema."""
    position_description: str
    unit_price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    unit: str
    total_price: float = Field(..., gt=0)


class OrderLineCreate(OrderLineBase):
    """Schema for creating an order line."""
    pass


class OrderLine(OrderLineBase):
    """Order line with ID for responses."""
    id: int
    request_id: int

    model_config = {"from_attributes": True}


class RequestBase(BaseModel):
    """Base request schema with common fields."""
    requestor_name: str
    title: str
    vendor_name: str
    vat_id: Optional[str] = None
    department: Optional[str] = None
    total_cost: float = Field(..., gt=0)


class RequestCreate(RequestBase):
    """Schema for creating a request."""
    order_lines: List[OrderLineCreate]
    commodity_group_id: Optional[int] = None


class RequestUpdate(BaseModel):
    """Schema for updating a request (all fields optional)."""
    requestor_name: Optional[str] = None
    title: Optional[str] = None
    vendor_name: Optional[str] = None
    vat_id: Optional[str] = None
    department: Optional[str] = None
    total_cost: Optional[float] = Field(None, gt=0)
    commodity_group_id: Optional[int] = None


class StatusUpdate(BaseModel):
    """Schema for updating request status."""
    status: Literal["Open", "In Progress", "Closed"]


class Request(RequestBase):
    """Complete request schema for responses."""
    id: int
    commodity_group_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
    order_lines: List[OrderLine] = []

    model_config = {"from_attributes": True}


class ExtractedData(BaseModel):
    """Data extracted from uploaded PDF."""
    vendor_name: str
    vat_id: Optional[str] = None
    requestor_name: Optional[str] = None
    requestor_department: Optional[str] = None
    title: Optional[str] = None
    order_lines: List[OrderLineCreate]
    total_cost: float = Field(..., gt=0)
    currency: str = Field(default="EUR", description="Currency code (EUR, USD, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")
    commodity_group: Optional[int] = None


class PDFUploadResponse(BaseModel):
    """Response after PDF upload with extracted data."""
    extracted_data: ExtractedData
    message: str = "PDF processed successfully"


class StatusHistoryBase(BaseModel):
    """Base status history schema."""
    old_status: Optional[str] = None
    new_status: str
    changed_at: datetime


class StatusHistory(StatusHistoryBase):
    """Status history with ID for responses."""
    id: int
    request_id: int

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Standard error response format."""
    detail: str
    error_code: Optional[str] = None
    field: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
