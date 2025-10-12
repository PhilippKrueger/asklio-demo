"""Business logic for managing procurement requests."""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Request, OrderLine, StatusHistory, CommodityGroup
from app.schemas import RequestCreate, RequestUpdate, StatusUpdate
from app.services.commodity_classifier import commodity_classifier


class RequestService:
    """Service for handling procurement request operations."""

    def create_request(
        self,
        request_data: RequestCreate,
        db: Session,
        pdf_path: Optional[str] = None,
        pdf_filename: Optional[str] = None,
        auto_classify: bool = True
    ) -> Request:
        """
        Create a new procurement request.

        Args:
            request_data: Request data from API
            db: Database session
            pdf_path: Optional path to uploaded PDF
            pdf_filename: Optional original PDF filename
            auto_classify: Whether to automatically classify commodity group

        Returns:
            Request: Created request object

        Raises:
            ValueError: If validation fails
        """
        # Auto-classify commodity group if not provided
        commodity_group_id = request_data.commodity_group_id
        commodity_group_confidence = None

        if auto_classify and not commodity_group_id:
            commodity_groups = db.query(CommodityGroup).all()
            classification = commodity_classifier.classify_request(
                request_data, commodity_groups, db
            )
            commodity_group_id = classification.commodity_group_id
            commodity_group_confidence = classification.confidence

        # Create request object
        request = Request(
            requestor_name=request_data.requestor_name,
            title=request_data.title,
            vendor_name=request_data.vendor_name,
            vat_id=request_data.vat_id,
            commodity_group_id=commodity_group_id,
            commodity_group_confidence=commodity_group_confidence,
            department=request_data.department,
            total_cost=request_data.total_cost,
            status="Open",
            pdf_path=pdf_path,
            pdf_filename=pdf_filename
        )

        db.add(request)
        db.flush()  # Get request ID

        # Create order lines
        for line_data in request_data.order_lines:
            order_line = OrderLine(
                request_id=request.id,
                position_description=line_data.position_description,
                unit_price=line_data.unit_price,
                amount=line_data.amount,
                unit=line_data.unit,
                total_price=line_data.total_price
            )
            db.add(order_line)

        # Create initial status history
        status_history = StatusHistory(
            request_id=request.id,
            old_status=None,
            new_status="Open"
        )
        db.add(status_history)

        db.commit()
        db.refresh(request)

        return request

    def get_request(self, request_id: int, db: Session) -> Optional[Request]:
        """
        Get a single request by ID.

        Args:
            request_id: ID of the request
            db: Database session

        Returns:
            Request or None if not found
        """
        return db.query(Request).filter(Request.id == request_id).first()

    def list_requests(
        self,
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Request]:
        """
        List requests with optional filtering.

        Args:
            db: Database session
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of requests
        """
        query = db.query(Request)

        if status:
            query = query.filter(Request.status == status)

        return query.order_by(Request.created_at.desc()).offset(skip).limit(limit).all()

    def update_request(
        self,
        request_id: int,
        update_data: RequestUpdate,
        db: Session
    ) -> Optional[Request]:
        """
        Update a request.

        Args:
            request_id: ID of the request to update
            update_data: Fields to update
            db: Database session

        Returns:
            Updated request or None if not found
        """
        request = self.get_request(request_id, db)
        if not request:
            return None

        # Update fields that are provided
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(request, field, value)

        request.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(request)

        return request

    def update_status(
        self,
        request_id: int,
        status_update: StatusUpdate,
        db: Session
    ) -> Optional[Request]:
        """
        Update request status and record in history.

        Args:
            request_id: ID of the request
            status_update: New status
            db: Database session

        Returns:
            Updated request or None if not found
        """
        request = self.get_request(request_id, db)
        if not request:
            return None

        old_status = request.status
        new_status = status_update.status

        # Update status
        request.status = new_status
        request.updated_at = datetime.utcnow()

        # Record status change in history
        status_history = StatusHistory(
            request_id=request.id,
            old_status=old_status,
            new_status=new_status
        )
        db.add(status_history)

        db.commit()
        db.refresh(request)

        return request

    def delete_request(self, request_id: int, db: Session) -> bool:
        """
        Delete a request.

        Args:
            request_id: ID of the request to delete
            db: Database session

        Returns:
            True if deleted, False if not found
        """
        request = self.get_request(request_id, db)
        if not request:
            return False

        db.delete(request)
        db.commit()

        return True


# Singleton instance
request_service = RequestService()
