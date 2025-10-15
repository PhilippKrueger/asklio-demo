"""Commodity group classification service using OpenAI."""
from typing import List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel

from app.config import settings


class CategoryClassification(BaseModel):
    """Result of category classification."""
    category: str
    confidence: float
    reasoning: str


class PDFCommodityClassification(BaseModel):
    """Result of commodity group classification for PDF extraction."""
    commodity_group_id: int
    commodity_group_name: str
    category: str
    confidence: float
    reasoning: str


class CommodityClassifier:
    """Service for classifying procurement requests into commodity groups."""

    COMMODITY_GROUPS = {
        "General Services": {
            1: "Accommodation Rentals",
            2: "Membership Fees", 
            3: "Workplace Safety",
            4: "Consulting",
            5: "Financial Services",
            6: "Fleet Management",
            7: "Recruitment Services",
            8: "Professional Development",
            9: "Miscellaneous Services",
            10: "Insurance"
        },
        "Facility Management": {
            11: "Electrical Engineering",
            12: "Facility Management Services",
            13: "Security",
            14: "Renovations",
            15: "Office Equipment",
            16: "Energy Management",
            17: "Maintenance",
            18: "Cafeteria and Kitchenettes",
            19: "Cleaning"
        },
        "Publishing Production": {
            20: "Audio and Visual Production",
            21: "Books/Videos/CDs",
            22: "Printing Costs",
            23: "Software Development for Publishing",
            24: "Material Costs",
            25: "Shipping for Production",
            26: "Digital Product Development",
            27: "Pre-production",
            28: "Post-production Costs"
        },
        "Information Technology": {
            29: "Hardware",
            30: "IT Services",
            31: "Software"
        },
        "Logistics": {
            32: "Courier, Express, and Postal Services",
            33: "Warehousing and Material Handling",
            34: "Transportation Logistics",
            35: "Delivery Services"
        },
        "Marketing & Advertising": {
            36: "Advertising",
            37: "Outdoor Advertising",
            38: "Marketing Agencies",
            39: "Direct Mail",
            40: "Customer Communication",
            41: "Online Marketing",
            42: "Events",
            43: "Promotional Materials"
        },
        "Production": {
            44: "Warehouse and Operational Equipment",
            45: "Production Machinery",
            46: "Spare Parts",
            47: "Internal Transportation",
            48: "Production Materials",
            49: "Consumables",
            50: "Maintenance and Repairs"
        }
    }

    def __init__(self):
        """Initialize the classifier with OpenAI model."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=settings.openai_api_key
        )


    def classify_pdf_products(self, product_descriptions: List[str]) -> Optional[int]:
        """
        Two-step classification for PDF extraction: first category, then specific commodity group.
        
        Args:
            product_descriptions: List of product/service descriptions
            
        Returns:
            Commodity group ID or None if classification fails
        """
        try:
            # Step 1: Classify category
            category_result = self._classify_category(product_descriptions)
            if not category_result:
                return None
                
            # Step 2: Classify specific commodity group within category
            commodity_result = self._classify_commodity_group(
                product_descriptions, 
                category_result.category
            )
            
            if commodity_result:
                return commodity_result.commodity_group_id
            return None
            
        except Exception as e:
            print(f"Warning: PDF commodity classification failed: {str(e)}")
            return None

    def _classify_category(self, product_descriptions: List[str]) -> Optional[CategoryClassification]:
        """Step 1: Classify into main category."""
        
        categories = list(self.COMMODITY_GROUPS.keys())
        categories_text = "\n".join([f"- {cat}" for cat in categories])
        products_text = "\n".join([f"- {desc}" for desc in product_descriptions])
        
        category_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at categorizing procurement items.
            
            Analyze the following products/services and classify them into ONE of these main categories:
            
            {categories_text}
            
            Category Definitions:
            - General Services: Consulting, professional services, memberships, insurance
            - Facility Management: Building maintenance, office equipment, security, cleaning
            - Publishing Production: Content creation, printing, media production
            - Information Technology: Hardware, software, IT services
            - Logistics: Shipping, warehousing, transportation
            - Marketing & Advertising: Promotional materials, events, marketing services
            - Production: Manufacturing equipment, materials, operational tools
            
            Rules:
            - Consider ALL products to determine the dominant category
            - If products span multiple categories, choose the one representing the majority of value/items
            - Provide clear reasoning for your choice
            
            Return your response as:
            Category: [CATEGORY_NAME]
            Confidence: [0.0-1.0]
            Reasoning: [Brief explanation]"""),
            ("user", f"Classify these products:\n{products_text}")
        ])
        
        try:
            response = self.llm.invoke(category_prompt.format_messages())
            response_text = response.content.strip()
            
            # Parse response
            lines = response_text.split('\n')
            category = None
            confidence = 0.0
            reasoning = ""
            
            for line in lines:
                if line.startswith('Category:'):
                    category = line.split(':', 1)[1].strip()
                elif line.startswith('Confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
                elif line.startswith('Reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            if category and category in self.COMMODITY_GROUPS:
                return CategoryClassification(
                    category=category,
                    confidence=confidence,
                    reasoning=reasoning
                )
                
            return None
            
        except Exception as e:
            print(f"Warning: Category classification failed: {str(e)}")
            return None

    def _classify_commodity_group(self, product_descriptions: List[str], category: str) -> Optional[PDFCommodityClassification]:
        """Step 2: Classify into specific commodity group within category."""
        
        if category not in self.COMMODITY_GROUPS:
            return None
            
        commodity_groups = self.COMMODITY_GROUPS[category]
        groups_text = "\n".join([f"{id}: {name}" for id, name in commodity_groups.items()])
        products_text = "\n".join([f"- {desc}" for desc in product_descriptions])
        
        commodity_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at classifying products into specific commodity groups.
            
            The products have already been classified into the "{category}" category.
            Now classify them into the most appropriate specific commodity group:
            
            {groups_text}
            
            Rules:
            - Consider ALL products to find the best fitting commodity group
            - If products could fit multiple groups, choose the most specific/relevant one
            - Provide clear reasoning for your choice
            
            Return your response as:
            ID: [GROUP_ID]
            Confidence: [0.0-1.0]
            Reasoning: [Brief explanation]"""),
            ("user", f"Classify these products:\n{products_text}")
        ])
        
        try:
            response = self.llm.invoke(commodity_prompt.format_messages())
            response_text = response.content.strip()
            
            # Parse response
            lines = response_text.split('\n')
            group_id = None
            confidence = 0.0
            reasoning = ""
            
            for line in lines:
                if line.startswith('ID:'):
                    try:
                        group_id = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        continue
                elif line.startswith('Confidence:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
                elif line.startswith('Reasoning:'):
                    reasoning = line.split(':', 1)[1].strip()
            
            if group_id and group_id in commodity_groups:
                return PDFCommodityClassification(
                    commodity_group_id=group_id,
                    commodity_group_name=commodity_groups[group_id],
                    category=category,
                    confidence=confidence,
                    reasoning=reasoning
                )
                
            return None
            
        except Exception as e:
            print(f"Warning: Commodity group classification failed: {str(e)}")
            return None


# Singleton instance
commodity_classifier = CommodityClassifier()
