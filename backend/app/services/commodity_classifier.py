"""Commodity group classification service using OpenAI."""
from typing import List
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.config import settings
from app.models import CommodityGroup
from app.schemas import CommodityClassification, RequestCreate


class CommodityClassifier:
    """Service for classifying procurement requests into commodity groups."""

    def __init__(self):
        """Initialize the classifier with OpenAI model."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.openai_api_key
        )

    def classify_request(
        self,
        request_data: RequestCreate,
        commodity_groups: List[CommodityGroup],
        db: Session
    ) -> CommodityClassification:
        """
        Classify a procurement request into the most appropriate commodity group.

        Args:
            request_data: The request data to classify
            commodity_groups: List of available commodity groups
            db: Database session (unused but kept for consistency)

        Returns:
            CommodityClassification: Classification result with confidence

        Raises:
            Exception: If classification fails
        """
        # Format commodity groups for the prompt
        groups_text = "\n".join([
            f"{g.id}: {g.category} - {g.name}"
            for g in commodity_groups
        ])

        # Format order line descriptions
        order_descriptions = [
            line.position_description for line in request_data.order_lines
        ]

        # Create classification prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert procurement specialist who can accurately classify purchase requests into commodity groups.

Available Commodity Groups:
{commodity_groups}

Based on the request information provided, select the SINGLE most appropriate commodity group ID.

Consider:
- The nature of the items/services being requested
- The vendor type
- The descriptions of order line items
- The overall purpose of the request

Return a JSON object with this exact structure:
{{
  "commodity_group_id": number (the ID from the list above),
  "confidence": number (0.0 to 1.0, your confidence in this classification),
  "reasoning": "string (brief explanation of why this group was chosen)"
}}

IMPORTANT:
- You MUST select one of the commodity group IDs from the list above
- If uncertain between multiple groups, choose the most specific/relevant one
- Confidence should reflect how well the request matches the chosen group
"""),
            ("user", """Please classify this procurement request:

Title: {title}
Vendor: {vendor_name}
Department: {department}

Order Items:
{order_items}

Total Cost: €{total_cost}
""")
        ])

        # Prepare input data
        order_items_text = "\n".join([
            f"- {desc}" for desc in order_descriptions
        ])

        try:
            # Create chain with JSON output parser
            parser = JsonOutputParser()
            chain = prompt | self.llm | parser

            # Execute classification
            result = chain.invoke({
                "commodity_groups": groups_text,
                "title": request_data.title,
                "vendor_name": request_data.vendor_name,
                "department": request_data.department or "Not specified",
                "order_items": order_items_text,
                "total_cost": request_data.total_cost
            })

            # Find the commodity group to get its name
            commodity_group_id = result["commodity_group_id"]
            commodity_group = next(
                (g for g in commodity_groups if g.id == commodity_group_id),
                None
            )

            if not commodity_group:
                raise ValueError(f"Invalid commodity group ID: {commodity_group_id}")

            classification = CommodityClassification(
                commodity_group_id=commodity_group_id,
                commodity_group_name=f"{commodity_group.category} - {commodity_group.name}",
                confidence=result["confidence"],
                reasoning=result.get("reasoning")
            )

            return classification

        except Exception as e:
            raise Exception(f"Failed to classify commodity group: {str(e)}")

    def classify_text(
        self,
        text: str,
        commodity_groups: List[CommodityGroup]
    ) -> CommodityClassification:
        """
        Classify arbitrary text into a commodity group.

        Args:
            text: Text to classify
            commodity_groups: List of available commodity groups

        Returns:
            CommodityClassification: Classification result with confidence
        """
        # Format commodity groups for the prompt
        groups_text = "\n".join([
            f"{g.id}: {g.category} - {g.name}"
            for g in commodity_groups
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert procurement specialist who can accurately classify descriptions into commodity groups.

Available Commodity Groups:
{commodity_groups}

Based on the text provided, select the SINGLE most appropriate commodity group ID.

Return a JSON object with this exact structure:
{{
  "commodity_group_id": number (the ID from the list above),
  "confidence": number (0.0 to 1.0, your confidence in this classification),
  "reasoning": "string (brief explanation of why this group was chosen)"
}}
"""),
            ("user", "Classify this text: {text}")
        ])

        try:
            parser = JsonOutputParser()
            chain = prompt | self.llm | parser

            result = chain.invoke({
                "commodity_groups": groups_text,
                "text": text
            })

            commodity_group_id = result["commodity_group_id"]
            commodity_group = next(
                (g for g in commodity_groups if g.id == commodity_group_id),
                None
            )

            if not commodity_group:
                raise ValueError(f"Invalid commodity group ID: {commodity_group_id}")

            return CommodityClassification(
                commodity_group_id=commodity_group_id,
                commodity_group_name=f"{commodity_group.category} - {commodity_group.name}",
                confidence=result["confidence"],
                reasoning=result.get("reasoning")
            )

        except Exception as e:
            raise Exception(f"Failed to classify text: {str(e)}")


# Singleton instance
commodity_classifier = CommodityClassifier()
