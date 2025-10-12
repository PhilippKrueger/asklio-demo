"""Detailed unit tests to trace PDF extraction process step by step."""
import pytest
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


class TestPDFExtractionDetailed:
    """Detailed tests to identify where information gets lost."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_pdf_text_extraction_raw(self, fixtures_dir):
        """
        Test raw PDF text extraction without any processing.

        This verifies that PyPDFLoader can extract text from the PDF.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"

        # Load PDF
        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        print(f"\n" + "="*80)
        print("RAW PDF TEXT EXTRACTION")
        print("="*80)
        print(f"Number of pages: {len(documents)}")
        print(f"Total text length: {len(text)} characters")
        print(f"\nFirst 500 characters:")
        print(text[:500])
        print(f"\n... (truncated)")

        # Verify critical information is present in raw text
        assert "Gärtner Gregg" in text, "Vendor name not found in raw text"
        assert "DE198570491" in text or "DE 198 570 491" in text, "VAT ID not found in raw text"
        assert "Moosbild" in text, "Main product not found in raw text"
        assert "1.438,00" in text or "1438" in text, "Main price not found in raw text"
        assert "Transport" in text, "Transport item not found in raw text"
        assert "320,00" in text or "320" in text, "Transport price not found in raw text"

        # Check for problematic patterns
        if "Alternativ" in text:
            print(f"\n⚠️  Warning: 'Alternativ' found in text - alternative positions present")

        print(f"\n✓ Raw text extraction successful")
        print(f"  All critical information present in raw text")

    def test_pdf_table_structure_detection(self, fixtures_dir):
        """
        Test detection of table structure in the PDF.

        This helps identify if the tabular data is being extracted correctly.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"

        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        print(f"\n" + "="*80)
        print("TABLE STRUCTURE ANALYSIS")
        print("="*80)

        # Look for table headers
        table_indicators = [
            "Pos.",
            "Menge",
            "Artikel-Nr",
            "Bezeichnung",
            "Einzelpreis",
            "Gesamtpreis"
        ]

        found_indicators = []
        for indicator in table_indicators:
            if indicator in text:
                found_indicators.append(indicator)
                print(f"✓ Found table header: '{indicator}'")
            else:
                print(f"✗ Missing table header: '{indicator}'")

        assert len(found_indicators) >= 4, \
            f"Expected at least 4 table headers, found only {len(found_indicators)}"

        # Look for position markers
        positions = ["1.1", "1.2", "1.1a", "1.1b"]
        found_positions = []
        for pos in positions:
            if pos in text:
                found_positions.append(pos)
                print(f"  Position {pos} found")

        print(f"\n✓ Table structure detection successful")
        print(f"  Found {len(found_indicators)}/6 table headers")
        print(f"  Found {len(found_positions)} position markers")

    def test_price_format_detection(self, fixtures_dir):
        """
        Test detection of different price formats in the PDF.

        German PDFs use comma as decimal separator which can cause issues.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"

        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        print(f"\n" + "="*80)
        print("PRICE FORMAT ANALYSIS")
        print("="*80)

        # Look for various price formats
        import re

        # German format: 1.438,00 €
        german_prices = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}\s*€?', text)
        print(f"\nGerman format prices (1.234,56 €): {len(german_prices)}")
        for price in german_prices[:5]:
            print(f"  - {price}")

        # Simple format: 1438.00 or 1438,00
        simple_prices = re.findall(r'\d{1,5}[.,]\d{2}', text)
        print(f"\nSimple format prices: {len(simple_prices)}")
        for price in simple_prices[:5]:
            print(f"  - {price}")

        # Check for expected prices
        expected_prices = ["1.438,00", "320,00", "1.758,00", "2.092,02"]
        found_prices = []
        for price in expected_prices:
            if price in text:
                found_prices.append(price)
                print(f"\n✓ Found expected price: {price}")
            else:
                print(f"\n✗ Missing expected price: {price}")

        assert len(found_prices) >= 3, \
            f"Expected at least 3 key prices, found only {len(found_prices)}"

        print(f"\n✓ Price format detection successful")

    def test_multiline_description_handling(self, fixtures_dir):
        """
        Test handling of multi-line item descriptions.

        The Moosbild item has a very long description spanning many lines.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"

        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        print(f"\n" + "="*80)
        print("MULTI-LINE DESCRIPTION ANALYSIS")
        print("="*80)

        # Find the Moosbild description
        moosbild_start = text.find('Moosbild "70:30"')
        if moosbild_start == -1:
            pytest.fail("Moosbild description not found in text")

        # Extract a reasonable chunk around it
        chunk = text[moosbild_start:moosbild_start+500]

        print(f"\nMoosbild description excerpt:")
        print(chunk)

        # Check for key description elements
        description_elements = [
            "askLio",
            "Waldmoos",
            "Ballenmoos",
            "160x80",
            "MDF",
            "Acryl"
        ]

        found_elements = []
        for element in description_elements:
            if element in text:
                found_elements.append(element)
                print(f"✓ Description element found: {element}")
            else:
                print(f"✗ Description element missing: {element}")

        print(f"\n✓ Multi-line description handling check complete")
        print(f"  Found {len(found_elements)}/{len(description_elements)} key elements")

    def test_alternative_positions_detection(self, fixtures_dir):
        """
        Test detection of alternative positions that should not be included.

        Positions 1.1a and 1.1b are alternatives to 1.1.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"

        loader = PyPDFLoader(str(pdf_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])

        print(f"\n" + "="*80)
        print("ALTERNATIVE POSITIONS ANALYSIS")
        print("="*80)

        # Check for alternative position markers
        alt_markers = [
            "Alternativ zu vorstehender Position",
            "Alternativ",
            "1.1a",
            "1.1b"
        ]

        for marker in alt_markers:
            if marker in text:
                print(f"⚠️  Found alternative marker: '{marker}'")
                # Find context
                idx = text.find(marker)
                context = text[max(0, idx-50):min(len(text), idx+200)]
                print(f"   Context: ...{context}...")
            else:
                print(f"   No '{marker}' found")

        # Check for alternative prices
        alt_prices = ["1.926,00", "1.685,00"]
        for price in alt_prices:
            if price in text:
                print(f"\n⚠️  Found alternative position price: {price}")
            else:
                print(f"\n✓ Alternative price {price} handled correctly (not present)")

        print(f"\n✓ Alternative positions analysis complete")

    def test_confidence_calculation_factors(self, fixtures_dir):
        """
        Test the factors that contribute to confidence score calculation.
        """
        from app.services.pdf_extractor import pdf_extractor

        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        print(f"\n" + "="*80)
        print("CONFIDENCE CALCULATION ANALYSIS")
        print("="*80)
        print(f"\nOverall confidence: {result.confidence:.2%}")

        # Check individual factors
        print(f"\nVendor name: '{result.vendor_name}'")
        print(f"  Length check: {len(result.vendor_name) > 2} ({'✓' if len(result.vendor_name) > 2 else '✗'})")

        print(f"\nVAT ID: '{result.vat_id}'")
        import re
        vat_valid = bool(re.match(r"^DE\d{9}$", result.vat_id)) if result.vat_id else False
        print(f"  Format check (DE + 9 digits): {vat_valid} ({'✓' if vat_valid else '✗'})")

        print(f"\nOrder lines: {len(result.order_lines)}")
        print(f"  Has lines: {len(result.order_lines) > 0} ({'✓' if len(result.order_lines) > 0 else '✗'})")

        print(f"\nTotal cost: €{result.total_cost:.2f}")
        print(f"  Is positive: {result.total_cost > 0} ({'✓' if result.total_cost > 0 else '✗'})")

        # Check sum match
        calculated_sum = sum(line.total_price for line in result.order_lines)
        diff_percentage = abs(calculated_sum - result.total_cost) / result.total_cost if result.total_cost > 0 else 1.0
        print(f"\nSum validation:")
        print(f"  Calculated sum: €{calculated_sum:.2f}")
        print(f"  Declared total: €{result.total_cost:.2f}")
        print(f"  Difference: {diff_percentage:.2%}")
        print(f"  Match quality: {'✓ Excellent' if diff_percentage < 0.01 else '✓ Good' if diff_percentage < 0.05 else '⚠️  Poor'}")

        print(f"\n✓ Confidence calculation analysis complete")
