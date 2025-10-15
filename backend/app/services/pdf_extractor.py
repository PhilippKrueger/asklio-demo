# following https://python.langchain.com/docs/how_to/structured_output/
import re
import base64
import logging
from pathlib import Path
from typing import Optional, List, Literal
from io import BytesIO
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pdf2image import convert_from_path
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas import ExtractedData, OrderLineCreate
from app.services.commodity_classifier import commodity_classifier

EXTRACTION_MODEL = "gpt-4o-mini"
VISION_MODEL = "gpt-4o-mini"

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Base exception for extraction errors."""
    pass


class VendorNotFoundError(ExtractionError):
    """Raised when vendor cannot be identified."""
    pass


class RawPDFContent(BaseModel):
    """Raw content extracted from PDF."""
    text: str
    image_text: str = ""
    has_images: bool = False
    page_count: int


class CompanyEntity(BaseModel):
    """Represents a company entity in the document."""
    name: str
    vat_id: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    department: Optional[str] = None
    role: Literal["vendor", "requestor", "unknown"]


class OrderLineDetailed(BaseModel):
    """Detailed order line from document analysis."""
    description: str
    unit_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    unit: str
    total_price: float = Field(..., gt=0)


class FullDocumentStructure(BaseModel):
    """Complete document structure with all entities."""
    vendor: CompanyEntity
    requestor: CompanyEntity
    order_lines: List[OrderLineDetailed]
    document_type: Literal["quote", "offer", "invoice", "order"]
    document_title: Optional[str] = Field(None, description="Short descriptive title for the document/request")
    document_date: Optional[str] = None
    document_number: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    currency: str = Field(..., description="Currency code (EUR, USD, etc.)")
    total_net: float
    tax_amount: Optional[float] = None
    total_gross: float
    confidence: float = Field(..., ge=0.0, le=1.0)


class PDFExtractor:
    """Enhanced multi-step PDF extraction service."""

    def __init__(self):
        """Initialize the enhanced PDF extractor."""
        self.llm = ChatOpenAI(
            model=EXTRACTION_MODEL,
            temperature=0,
            api_key=settings.openai_api_key
        )
        self.openai_client = OpenAI(api_key=settings.openai_api_key)

    def extract_from_pdf(self, pdf_path: str) -> ExtractedData:
        """
        Multi-step extraction pipeline.
        
        Steps:
        1. Extract raw content (text + images)
        2. Extract structured entities with vendor/requestor separation
        3. Extract target data
        4. Classify commodity group
        """
        try:
            # Step 1: Raw extraction
            raw_content = self._extract_raw_content(pdf_path)
            
            # Step 2: Structured extraction
            full_structure = self._extract_structured_entities(raw_content)
            
            # Step 3: Target extraction
            extracted_data = self._extract_target_data(full_structure)
            
            # Step 4: Commodity group classification
            product_descriptions = [line.description for line in full_structure.order_lines]
            commodity_group = commodity_classifier.classify_pdf_products(product_descriptions)
            extracted_data.commodity_group = commodity_group
            
            return extracted_data
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract data from PDF: {str(e)}")

    def _extract_raw_content(self, pdf_path: str) -> RawPDFContent:
        """Extract all raw content from PDF using PyPDF + Vision."""
        
        # Text Extraction
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_content = "\n".join([doc.page_content for doc in documents])
        
        # Extract embedded images from PDF
        embedded_images = self._extract_embedded_images(pdf_path)
        has_images = len(embedded_images) > 0
        
        # Save images to local folder for inspection
        if has_images:
            print(f"Saving {len(embedded_images)} images for inspection")
            # self._save_images_for_inspection(embedded_images, pdf_path)
        else:
            print("No images to save")
        
        # Image-based Text Extraction (only for embedded images)
        image_text = ""
        if has_images:
            image_text = self._extract_text_from_images(embedded_images)
        
        return RawPDFContent(
            text=text_content,
            image_text=image_text,
            has_images=has_images,
            page_count=len(documents)
        )

    def _extract_raw_content_original(self, pdf_path: str) -> RawPDFContent:
        """Extract all raw content from PDF using original method."""
        
        # Text Extraction
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_content = "\n".join([doc.page_content for doc in documents])
        
        # Image Detection and Extraction
        images = convert_from_path(pdf_path, dpi=150)
        has_images = len(images) > 0
        
        # Image-based Text Extraction (if images present)
        image_text = ""
        if has_images:
            image_text = self._extract_text_from_images(images)
        
        return RawPDFContent(
            text=text_content,
            image_text=image_text,
            has_images=has_images,
            page_count=len(documents)
        )

    def _extract_text_from_images(self, images: List) -> str:
        """Extract text from images using Vision API."""
        try:
            if not images:
                return ""
                
            # Prepare images for API (first 2 pages for efficiency)
            image_contents = []
            for image in images[:2]:
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

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract all text from these document images, focusing on:
                            - Company names and contact information
                            - VAT IDs and registration numbers
                            - Addresses and contact details
                            - Product/service descriptions
                            - Prices and quantities
                            - Headers and footers
                            
                            Return the text exactly as it appears, maintaining structure."""
                        }
                    ] + image_contents
                }
            ]

            response = self.openai_client.chat.completions.create(
                model=VISION_MODEL,
                messages=messages,
                max_completion_tokens=2000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            error_msg = f"Image text extraction failed: {str(e)}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)

    def _save_images_for_inspection(self, images: List, pdf_path: str) -> None:
        """Save embedded images to local folder for inspection."""
        try:
            from pathlib import Path
            
            # Create output directory
            output_dir = Path("./pdf_images")
            output_dir.mkdir(exist_ok=True)
            
            # Get PDF filename without extension
            pdf_name = Path(pdf_path).stem
            
            # Save each embedded image
            for img_num, image in enumerate(images):
                image_filename = f"{pdf_name}_image_{img_num + 1}.png"
                image_path = output_dir / image_filename
                image.save(image_path, "PNG")
                print(f"Saved embedded image: {image_path}")
                
        except Exception as e:
            error_msg = f"Failed to save images: {str(e)}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)

    def _extract_embedded_images(self, pdf_path: str) -> List:
        """Extract only embedded images from PDF, not full page renders."""
        try:
            import fitz  # PyMuPDF
            
            images = []
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    print(f"Processing image {img_index + 1} on page {page_num + 1}")
                    processed_image = self._process_embedded_image(img, page, page_num, doc)
                    if processed_image:
                        images.append(processed_image)
                        print(f"Successfully added image {img_index + 1}")
                    else:
                        print(f"Failed to process image {img_index + 1}")
            
            doc.close()
            return images
            
        except Exception as e:
            error_msg = f"Failed to extract embedded images: {str(e)}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)
    
    def _process_embedded_image(self, img, page, page_num: int, doc):
        """Process a single embedded image with size filtering and resizing."""
        try:
            # Check if image area exceeds 1/3 of page first
            if self._image_exceeds_page_threshold_pdf(img, page, doc):
                print(f"Large image detected on page {page_num + 1}, extracting footer area only")
                pil_image = self._extract_pil_image_from_pdf(img, doc)
                if not pil_image:
                    return None
                # Crop to bottom 20% (footer area) for large background images
                return self._crop_to_footer_area(pil_image, page_num)
            else:
                print(f"Skipping small image on page {page_num + 1} (only processing large image footers)")
                return None
            
        except Exception as e:
            error_msg = f"Failed to process image on page {page_num + 1}: {str(e)}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)
    
    def _extract_pil_image_from_pdf(self, img, doc):
        """Extract PIL image from PDF image reference."""
        from PIL import Image
        from io import BytesIO
        
        try:
            import fitz
            # Extract image data
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            
            # Convert to PIL Image
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_data = pix.tobytes("png")
                pil_image = Image.open(BytesIO(img_data))
                pix = None  # Free memory
                return pil_image
            
            pix = None  # Free memory
            return None
            
        except Exception as e:
            error_msg = f"Error extracting PIL image: {e}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)
    
    def _image_exceeds_page_threshold_pdf(self, img, page, doc) -> bool:
        """Check if image area exceeds 1/8 of page area using PDF coordinates."""
        try:
            # Get page dimensions in PDF points
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height
            max_image_area = page_area / 3
            
            # Get image dimensions in PDF coordinates
            xref = img[0]
            image_rect = page.get_image_rects(xref)
            
            if image_rect:
                # Use first occurrence of this image on the page
                img_rect = image_rect[0]
                image_area = img_rect.width * img_rect.height
                exceeds = image_area > max_image_area
                print(f"Image area check: {image_area:.1f} vs max {max_image_area:.1f} (page: {page_area:.1f}) -> {'DISCARD' if exceeds else 'KEEP'}")
                return exceeds
            
            # Fallback: if we can't get image rect, allow the image
            print("Could not get image rect, allowing image")
            return False
            
        except Exception as e:
            error_msg = f"Exception in image threshold check: {e}"
            print(f"Warning: {error_msg}")
            raise ExtractionError(error_msg)
    
    def _crop_to_footer_area(self, pil_image, page_num: int):
        """Crop large background image to footer area (bottom 20%)."""
        width, height = pil_image.size
        
        # Crop to bottom 20% of image (footer area)
        footer_height = int(height * 0.2)
        top = height - footer_height
        
        footer_image = pil_image.crop((0, top, width, height))
        
        # Scale to 150 DPI
        resized_footer = self._resize_image_to_dpi(footer_image, page_num)
        print(f"Cropped large image to footer area on page {page_num + 1}: {pil_image.size} -> {footer_image.size}")
        return resized_footer
    
    def _resize_image_to_dpi(self, pil_image, page_num: int):
        """Resize image to 150 DPI equivalent if needed."""
        from PIL import Image
        
        original_size = pil_image.size
        max_dimension = 1500  # Approximate 150 DPI for typical document sizes
        
        if max(original_size) > max_dimension:
            # Calculate scaling factor to maintain aspect ratio
            scale_factor = max_dimension / max(original_size)
            new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
            resized_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"Found embedded image on page {page_num + 1}: {original_size} -> {new_size} (150 DPI)")
            return resized_image
        else:
            print(f"Found embedded image on page {page_num + 1}: {original_size} (kept original)")
            return pil_image

    def _extract_structured_entities(self, raw_content: RawPDFContent) -> FullDocumentStructure:
        """Extract all entities with proper vendor/requestor separation."""
        
        structured_llm = self.llm.with_structured_output(FullDocumentStructure)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing procurement documents.
            
            TITLE EXTRACTION:
            - Generate a concise, descriptive title (3-6 words) for this procurement request
            - Base the title on the main products/services being procured
            - Examples: "Software Development Services", "Office Equipment", "IT Infrastructure Upgrade"
            - Focus on what is being procured, not the vendor name
            
            CRITICAL DISTINCTION - Identify the roles:
            
            VENDOR (Seller/Supplier) - THE DOCUMENT ISSUER:
            - Company that created and sent this document
            - PRIORITIZE FOOTER TEXT: Vendor name is most commonly found in the document footer/signature area
            - Footer typically contains: vendor name, VAT ID, address, contact info
            - Look for company name near VAT ID in footer/bottom of page
            - Uses phrases: "we offer", "our quote", "our products", "our services"
            - Bank details belong to this company
            - Issues invoices, quotes, offers
            - "Bearbeiter" or "Sachbearbeiter" is the vendor's employee processing the document, NOT the requestor
            
            REQUESTOR (Buyer/Customer) - THE DOCUMENT RECIPIENT:
            - CRITICAL: The requestor is the RECIPIENT of the quote/offer, NOT the "Bearbeiter"
            - Appears in the ADDRESS BLOCK on the LEFT side of the document header
            - Look for the name/company after "An:", "To:", "Kunde:", "Customer:", "Auftraggeber:"
            - The person's name in the recipient address block
            - This is who the document is addressed TO, not who created it
            - IMPORTANT: Extract department/division information (e.g., "IT Department", "Procurement", "Finance")
            - Department often appears on line below company name or with person's title
            - Look for words like "Abteilung", "Department", "Division", "Team", "Unit"
            - If no explicit department, use job title or role if available
            - Receiving/buying party who RECEIVES the quote
            - DO NOT confuse with "Bearbeiter" (processor) who works for the vendor
            - Extract both the contact person name AND department - both are important
            
            VENDOR NAME EXTRACTION RULES (PRIORITY ORDER):
            1. HIGHEST PRIORITY: Check document footer/bottom for company name near VAT ID
            2. Check terms/legal section for parent company
            3. Look for email domain - vendor employees have company email
            4. Look for contact person details - their company is the vendor
            5. LOWEST PRIORITY: Check letterhead/header area only if above unclear
            
            CRITICAL VENDOR IDENTIFICATION RULES:
            - The vendor is the company that created and sent this document
            - Footer/signature area has highest priority for vendor identification
            - Header/top of document often contains customer information, not vendor
            - Look for who is "offering" or "quoting" - that company is the vendor
            
            NAME FORMATTING:
            - Extract base company name but include legal entities (GmbH, AG, Ltd)
            - Remove ownership details like "(Inh. Name)" but keep legal structure
            
            CURRENCY EXTRACTION:
            - Look for currency symbols (€, $, £) or codes (EUR, USD, GBP)
            - Currency usually appears with prices or in document footer
            - Extract the main document currency (not exchange rates)
            
            QUANTITY EXTRACTION RULES:
            - When extracting quantity, ensure it is the numeric value found directly in the 'Menge' (Quantity) column for each order line
            - DO NOT confuse quantity with the 'Pos.' (Position) number or line number
            - The 'Menge' column is for the count of items for that specific line, not the line number itself
            - Common German terms for quantity: 'Menge', 'Qty', 'Anzahl', 'Stk', 'Stück'
            - Parse German decimal notation (1,00 = 1.0, 2,50 = 2.5)
            
            ALTERNATIVE/VARIATION LINE ITEMS:
            - When you encounter 'Alternativ zu vorstehender Position' followed by sub-items (e.g., '1.1a', '1.1b') that have their own description, quantity, unit price, and total price, treat each sub-item as a separate and distinct OrderLineDetailed entry
            - These are not just descriptions of the parent item but represent distinct product options or configurations
            - Any line with a distinct unit_price and total_price should be extracted as a separate OrderLineDetailed
            - Items like '1.1', '1.1a', '1.1b', '1.2' are all separate order lines
            - Do not skip alternative items - they are valid order lines
            
            For order lines, extract:
            - description: CONCISE item/service description (use main product name only, avoid detailed specifications)
            - unit_price: Price per unit (numeric only)
            - quantity: Amount ordered (numeric only, from Menge column)
            - unit: Unit of measure
            - total_price: Total for this line (numeric only)
            
            Ensure vendor role is "vendor" and requestor role is "requestor"."""),
            ("user", "Analyze this document:\n\n{text}")
        ])
        
        chain = prompt | structured_llm
        
        # Combine text sources
        full_text = raw_content.text
        if raw_content.image_text:
            full_text += "\n\n[Extracted from images:]\n" + raw_content.image_text
        
        result = chain.invoke({"text": full_text})
        
        # Debug logging to see what LLM returns
        logger.debug("=== LLM EXTRACTION RESULT ===")
        logger.debug("Vendor: %s | VAT: %s | Role: %s", result.vendor.name, result.vendor.vat_id, result.vendor.role)
        logger.debug("Requestor: %s | Dept: %s | Contact: %s | Role: %s", 
                    result.requestor.name, result.requestor.department, result.requestor.contact_person, result.requestor.role)
        logger.debug("Order lines count: %d", len(result.order_lines))
        for i, line in enumerate(result.order_lines):
            logger.debug("  Line %d: %s... | qty:%s | unit_price:%s | total:%s", 
                        i+1, line.description[:50], line.quantity, line.unit_price, line.total_price)
        logger.debug("Full structure JSON:")
        logger.debug(result.model_dump_json(indent=2))
        logger.debug("=== END DEBUG ===")
        
        # Validate vendor/requestor roles
        if result.vendor.role != "vendor":
            raise VendorNotFoundError("Could not properly identify vendor in document")
            
        return result

    def _extract_target_data(self, full_structure: FullDocumentStructure) -> ExtractedData:
        """Extract only the required data for our system."""
        
        # Map comprehensive order lines to our schema
        order_lines = [
            OrderLineCreate(
                position_description=line.description,
                unit_price=line.unit_price,
                amount=line.quantity,
                unit=line.unit,
                total_price=line.total_price
            )
            for line in full_structure.order_lines
        ]
        
        return ExtractedData(
            vendor_name=full_structure.vendor.name,
            vat_id=full_structure.vendor.vat_id,
            requestor_name=full_structure.requestor.contact_person or full_structure.requestor.name,
            requestor_department=full_structure.requestor.department,
            title=full_structure.document_title,
            order_lines=order_lines,
            total_cost=full_structure.total_gross,
            currency=full_structure.currency,
            confidence=full_structure.confidence
        )




pdf_extractor = PDFExtractor()