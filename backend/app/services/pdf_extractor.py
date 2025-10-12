"""PDF extraction service using LangChain and OpenAI."""
import re
import base64
from pathlib import Path
from typing import Optional
from io import BytesIO
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pdf2image import convert_from_path
from openai import OpenAI

from app.config import settings
from app.schemas import ExtractedData, OrderLineCreate


class PDFExtractor:
    """Service for extracting procurement information from PDF files."""

    def __init__(self):
        """Initialize the PDF extractor with OpenAI model."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.openai_api_key
        )
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def extract_from_pdf(self, pdf_path: str) -> ExtractedData:
        """
        Extract procurement information from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractedData: Extracted procurement information with confidence score

        Raises:
            Exception: If extraction fails
        """
        # Load PDF and extract text
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        # Create extraction prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting procurement information from vendor offers.
Extract the following information accurately from the provided text:
- Vendor name
- VAT ID (Umsatzsteuer-Identifikationsnummer, usually in format DE followed by 9 digits)
- Department (if mentioned, the department that requested or will use the items)
- All order line items with:
  - position_description: Clear description of the item/service
  - unit_price: Price per unit (numeric value only, no currency symbols)
  - amount: Quantity being ordered (numeric value)
  - unit: Unit of measure (e.g., "licenses", "pieces", "hours", "Stück")
  - total_price: Total price for this line item (numeric value only)
- Total cost: Overall total cost of all items

Return a JSON object with this exact structure:
{{
  "vendor_name": "string",
  "vat_id": "string or null",
  "department": "string or null",
  "order_lines": [
    {{
      "position_description": "string",
      "unit_price": number,
      "amount": number,
      "unit": "string",
      "total_price": number
    }}
  ],
  "total_cost": number,
  "confidence": number (0.0 to 1.0, your confidence in the extraction)
}}

IMPORTANT:
- Extract all numeric values WITHOUT currency symbols (€, EUR, etc.)
- If a field cannot be found, use null for optional fields
- Calculate confidence based on how complete and clear the extraction was
- Ensure order_lines has at least one item if this is a valid offer
"""),
            ("user", "Extract information from this vendor offer:\n\n{text}")
        ])

        # Create chain with JSON output parser
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser

        try:
            # Execute extraction
            result = chain.invoke({"text": text})

            # Validate and convert to ExtractedData
            order_lines = [
                OrderLineCreate(**line) for line in result.get("order_lines", [])
            ]

            # Vision fallback for VAT ID if needed
            vat_id = result.get("vat_id")
            used_vision_fallback = False
            if not vat_id or not re.match(r"^DE\d{9}$", vat_id):
                print("VAT ID missing or invalid in text extraction, trying Vision fallback...")
                vision_vat = self._extract_vat_with_vision(pdf_path)
                if vision_vat:
                    result["vat_id"] = vision_vat
                    used_vision_fallback = True
                    print(f"Vision fallback successful: extracted VAT ID {vision_vat}")
                else:
                    print("Vision fallback did not find VAT ID")

            # Calculate confidence based on completeness
            confidence = self._calculate_confidence(result, order_lines)
            result["confidence"] = min(confidence, result.get("confidence", 1.0))

            # Slightly reduce confidence if Vision fallback was used (it's less reliable)
            if used_vision_fallback:
                result["confidence"] *= 0.95

            extracted_data = ExtractedData(
                vendor_name=result["vendor_name"],
                vat_id=result.get("vat_id"),
                department=result.get("department"),
                order_lines=order_lines,
                total_cost=result["total_cost"],
                confidence=result["confidence"]
            )

            return extracted_data

        except Exception as e:
            raise Exception(f"Failed to extract data from PDF: {str(e)}")

    def _calculate_confidence(self, result: dict, order_lines: list) -> float:
        """
        Calculate extraction confidence based on data completeness.

        Args:
            result: Raw extraction result
            order_lines: Parsed order lines

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        confidence_factors = []

        # Check if vendor name exists and is meaningful
        if result.get("vendor_name") and len(result["vendor_name"]) > 2:
            confidence_factors.append(1.0)
        else:
            confidence_factors.append(0.0)

        # Check if VAT ID is in valid format
        vat_id = result.get("vat_id")
        if vat_id and re.match(r"^DE\d{9}$", vat_id):
            confidence_factors.append(1.0)
        elif vat_id:
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.7)  # VAT ID is optional

        # Check if we have order lines
        if len(order_lines) > 0:
            confidence_factors.append(1.0)
        else:
            confidence_factors.append(0.0)

        # Check if total cost is reasonable
        if result.get("total_cost", 0) > 0:
            confidence_factors.append(1.0)
        else:
            confidence_factors.append(0.0)

        # Check if order line totals match or are close to the total cost
        if order_lines:
            calculated_total = sum(line.total_price for line in order_lines)
            total_cost = result.get("total_cost", 0)
            if total_cost > 0:
                diff_percentage = abs(calculated_total - total_cost) / total_cost
                if diff_percentage < 0.01:  # Less than 1% difference
                    confidence_factors.append(1.0)
                elif diff_percentage < 0.05:  # Less than 5% difference
                    confidence_factors.append(0.8)
                else:
                    confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.5)

        # Return average confidence
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

    def _extract_vat_with_vision(self, pdf_path: str) -> Optional[str]:
        """
        Extract VAT ID from PDF using GPT-4 Vision.

        This method is used as a fallback when text extraction fails to find VAT ID,
        particularly useful for image-based footers or scanned documents.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            str or None: Extracted VAT ID if found, otherwise None
        """
        try:
            # Convert first 2 pages to images (VAT ID usually in header/footer)
            images = convert_from_path(pdf_path, first_page=1, last_page=2, dpi=150)

            # Prepare images for API
            image_contents = []
            for image in images:
                # Convert PIL Image to base64
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_base64}",
                        "detail": "high"
                    }
                })

            # Create message with images
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze these document images and extract the VAT ID (Umsatzsteuer-Identifikationsnummer).

VAT ID formats to look for:
- Usually starts with "DE" followed by 9 digits (e.g., DE123456789)
- May be labeled as: "USt-IdNr", "USt-ID", "VAT ID", "Umsatzsteuer-ID", "UID"
- Often found in headers, footers, or company information sections
- May appear as an image or printed text

IMPORTANT:
- Return ONLY the VAT ID in format "DE" followed by exactly 9 digits
- If you find multiple VAT IDs, return the one that appears in the vendor/sender information
- If no VAT ID is found, return the text "NOT_FOUND"
- Do not include any other text, labels, or explanations"""
                        }
                    ] + image_contents
                }
            ]

            # Call GPT-4 Vision
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=100,
                temperature=0
            )

            # Extract VAT ID from response
            vat_id = response.choices[0].message.content.strip()

            # Validate format
            if vat_id and vat_id != "NOT_FOUND" and re.match(r"^DE\d{9}$", vat_id):
                return vat_id

            return None

        except Exception as e:
            print(f"Warning: Vision-based VAT extraction failed: {str(e)}")
            return None


# Singleton instance
pdf_extractor = PDFExtractor()
