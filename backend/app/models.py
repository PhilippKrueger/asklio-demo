"""SQLAlchemy database models."""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    LargeBinary
)
from sqlalchemy.orm import relationship

from app.database import Base


class CommodityGroup(Base):
    """Commodity group classification (pre-populated from README)."""

    __tablename__ = "commodity_groups"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Text, nullable=False)
    name = Column(Text, nullable=False)

    requests = relationship("Request", back_populates="commodity_group")

    def __repr__(self):
        return f"<CommodityGroup(id={self.id}, category='{self.category}', name='{self.name}')>"


class Request(Base):
    """Procurement request with vendor information and status tracking."""

    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    requestor_name = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    vendor_name = Column(Text, nullable=False)
    vat_id = Column(Text, nullable=True)
    commodity_group_id = Column(Integer, ForeignKey("commodity_groups.id"), nullable=True)
    commodity_group_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    department = Column(Text, nullable=True)
    total_cost = Column(Float, nullable=False)
    status = Column(Text, nullable=False, default="Open")  # Open, In Progress, Closed
    pdf_path = Column(Text, nullable=True)
    pdf_filename = Column(Text, nullable=True)
    pdf_content = Column(LargeBinary, nullable=True)  # Store PDF binary data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    commodity_group = relationship("CommodityGroup", back_populates="requests")
    order_lines = relationship("OrderLine", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Request(id={self.id}, title='{self.title}', status='{self.status}')>"


class OrderLine(Base):
    """Line items from vendor offers."""

    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    position_description = Column(Text, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    unit = Column(Text, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationship
    request = relationship("Request", back_populates="order_lines")

    def __repr__(self):
        return f"<OrderLine(id={self.id}, description='{self.position_description[:30]}...')>"


class StatusHistory(Base):
    """Audit trail for request status changes."""

    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(Text, nullable=True)
    new_status = Column(Text, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    request = relationship("Request", back_populates="status_history")

    def __repr__(self):
        return f"<StatusHistory(id={self.id}, request_id={self.request_id}, {self.old_status} -> {self.new_status})>"
