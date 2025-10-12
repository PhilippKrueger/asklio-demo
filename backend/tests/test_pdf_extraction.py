"""Tests for PDF extraction functionality."""
import pytest
from pathlib import Path
from app.services.pdf_extractor import pdf_extractor


class TestPDFExtraction:
    """Test PDF extraction with real vendor offers."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_extract_angebot_a0492_moosbild(self, fixtures_dir):
        """
        Test extraction of AngebotA0492_23.Pdf - Complex German invoice for moss picture.

        This PDF is challenging because:
        - Long multi-line item descriptions
        - Alternative positions that should not be included
        - German-specific formatting
        - Complex product with detailed specifications
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"
        assert pdf_path.exists(), f"Test PDF not found at {pdf_path}"

        # Extract data
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        # Verify vendor information
        assert result.vendor_name == "Gärtner Gregg", \
            f"Expected 'Gärtner Gregg', got '{result.vendor_name}'"

        assert result.vat_id == "DE198570491", \
            f"Expected 'DE198570491', got '{result.vat_id}'"

        # Department may or may not be extracted (it's the customer in this case)
        # If extracted, it might be "Lio Technologies GmbH" or similar

        # Verify order lines
        # Expected: 2 main line items (position 1.1 and 1.2)
        # Positions 1.1a and 1.1b are alternatives and should ideally be excluded
        assert len(result.order_lines) >= 2, \
            f"Expected at least 2 order lines, got {len(result.order_lines)}"

        # Check for the main item (Moosbild)
        moosbild_line = None
        transport_line = None

        for line in result.order_lines:
            if "moosbild" in line.position_description.lower() and "70:30" in line.position_description:
                moosbild_line = line
            elif "transport" in line.position_description.lower():
                transport_line = line

        # Verify main Moosbild item (position 1.1)
        assert moosbild_line is not None, \
            "Main Moosbild item (position 1.1) not found in order lines"

        assert moosbild_line.amount == 1.0, \
            f"Expected amount 1.0 for Moosbild, got {moosbild_line.amount}"

        assert moosbild_line.unit_price == 1438.00, \
            f"Expected unit price 1438.00 for Moosbild, got {moosbild_line.unit_price}"

        assert moosbild_line.total_price == 1438.00, \
            f"Expected total 1438.00 for Moosbild, got {moosbild_line.total_price}"

        # Verify transport item (position 1.2)
        assert transport_line is not None, \
            "Transport item (position 1.2) not found in order lines"

        assert transport_line.amount == 1.0, \
            f"Expected amount 1.0 for Transport, got {transport_line.amount}"

        assert transport_line.unit_price == 320.00, \
            f"Expected unit price 320.00 for Transport, got {transport_line.unit_price}"

        assert transport_line.total_price == 320.00, \
            f"Expected total 320.00 for Transport, got {transport_line.total_price}"

        # Verify total cost (net total before tax)
        expected_total = 1758.00  # Nettosumme
        assert abs(result.total_cost - expected_total) < 1.0, \
            f"Expected total around {expected_total}, got {result.total_cost}"

        # Verify confidence score
        assert 0.0 <= result.confidence <= 1.0, \
            f"Confidence score should be between 0 and 1, got {result.confidence}"

        # For this complex PDF, we expect reasonable confidence (> 0.5)
        assert result.confidence >= 0.5, \
            f"Expected confidence >= 0.5 for successful extraction, got {result.confidence}"

        print(f"\n✓ PDF extraction successful!")
        print(f"  Vendor: {result.vendor_name}")
        print(f"  VAT ID: {result.vat_id}")
        print(f"  Order lines: {len(result.order_lines)}")
        print(f"  Total cost: €{result.total_cost:.2f}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"\n  Items extracted:")
        for i, line in enumerate(result.order_lines, 1):
            print(f"    {i}. {line.position_description[:60]}... - €{line.total_price:.2f}")


    def test_extract_angebot_a0492_detailed_validation(self, fixtures_dir):
        """
        Detailed validation of line item extraction for AngebotA0492_23.Pdf.

        This test focuses on ensuring the correct items are extracted and
        alternative positions are properly handled.
        """
        pdf_path = fixtures_dir / "AngebotA0492_23.Pdf"
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        # Calculate sum of order line totals
        calculated_sum = sum(line.total_price for line in result.order_lines)

        # The sum should be close to the net total (1758.00)
        assert abs(calculated_sum - 1758.00) < 50.0, \
            f"Sum of order lines ({calculated_sum:.2f}) differs significantly from expected total (1758.00)"

        # Check that alternative positions (1.1a, 1.1b) are not included
        # These would have prices of 1926.00 and 1685.00
        for line in result.order_lines:
            # Alternative positions should not be present
            assert line.unit_price != 1926.00, \
                "Alternative position 1.1a (1926.00) should not be included"
            assert line.unit_price != 1685.00, \
                "Alternative position 1.1b (1685.00) should not be included"

        # Verify unit types
        for line in result.order_lines:
            assert line.unit, f"Unit field should not be empty for line: {line.position_description[:30]}"

        print(f"\n✓ Detailed validation passed!")
        print(f"  Calculated sum of items: €{calculated_sum:.2f}")
        print(f"  Expected net total: €1758.00")
        print(f"  Difference: €{abs(calculated_sum - 1758.00):.2f}")
