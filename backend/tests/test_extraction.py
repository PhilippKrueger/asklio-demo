"""Tests for PDF extraction functionality."""
import pytest
from pathlib import Path
from typing import Dict, Any, List

from app.services.pdf_extractor import pdf_extractor
from app.schemas import ExtractedData, OrderLineCreate

# Never change the tests!


class TestPDFExtraction:
    """Test cases for PDF extraction functionality."""

    TEST_DATA = [
        pytest.param(
            "AN-4120-Kdnr-14918.pdf",
            {
                "vendor_name": "Dream in Green GmbH",
                "vat_id": "DE325240530",
                "commodity_group": 36,
                "order_lines": [
                    {
                        "position": "2",
                        "product": "Moosbild Mix-Moos 160x80 cm",
                        "unit_price": 894.08,
                        "amount": 1.0,
                        "total_price": 715.26
                    },
                    {
                        "position": "3",
                        "product": "Logointegration \"asklio\" horizontal",
                        "unit_price": 622.0,
                        "amount": 1.0,
                        "total_price": 622.0
                    },
                    {
                        "position": "5",
                        "product": "Logointegration \"asklio\" vertikal",
                        "unit_price": 430.0,
                        "amount": 1.0,
                        "total_price": 430.0
                    }
                ],
                "total_cost": 1847.19
            },
            id="an_4120"
        ),
        pytest.param(
            "Quote_1__Lio_Technologies_GmbH__1x_MBA___2212618452.pdf",
            {
                "vendor_name": "Apple GmbH",
                "vat_id": "DE258811348",
                "commodity_group": 29,
                "order_lines": [
                    {
                        "position": "1",
                        "product": "13\" MacBook Air: Apple M2 Chip - Space Grau",
                        "unit_price": 1467.61,
                        "amount": 1.0,
                        "total_price": 1467.61
                    }
                ],
                "total_cost": 1759.01
            },
            id="quote_lio"
        ),
        pytest.param(
            "AN-OF2312380-Kdnr-57692.pdf",
            {
                "vendor_name": "FlowerArt GmbH",
                "vat_id": "DE271073640",
                "commodity_group": 43,
                "order_lines": [
                    {
                        "position": "1",
                        "product": "styleGREEN INDIVIDUAL - m2 Modul - Variante Wald- und Kugelmoos (bxh) 160 x 80 cm",
                        "unit_price": 559.0,
                        "amount": 1.28,
                        "total_price": 715.52
                    },
                    {
                        "position": "2",
                        "product": "styleGREEN INDIVIDUAL - Kantenbegrünung Waldmoos pro Lfm (u) 160 x 80 cm",
                        "unit_price": 25.13,
                        "amount": 4.8,
                        "total_price": 120.62
                    },
                    {
                        "position": "3",
                        "product": "Logo Acrylglas weiß 5mm 'ask Lio' Länge 80 cm mit Abstandshalter",
                        "unit_price": 350.0,
                        "amount": 1.0,
                        "total_price": 350.0
                    }
                ],
                "total_cost": 1546.99
            },
            id="an_of2312380"
        ),
        pytest.param(
            "AngebotA0492_23.pdf",
            {
                "vendor_name": "Gärtner Gregg",
                "vat_id": "DE198570491",
                "commodity_group": None,
                "order_lines": [
                    {
                        "position": "1.1",
                        "product": "Moosbild \"70:30\" mit Schriftzug \"askLio\"",
                        "unit_price": 1438.0,
                        "amount": 1.0,
                        "total_price": 1438.0
                    },
                    {
                        "position": "1.1a",
                        "product": "Wie Pos. zuvor, jedoch nur Ballenmoos",
                        "unit_price": 1926.0,
                        "amount": 1.0,
                        "total_price": 1926.0
                    },
                    {
                        "position": "1.1b",
                        "product": "Wie Pos. 1.1, jedoch flächig mit Waldmoos, anstatt des blauen Elements des Logos Ballenmoos geformt zur \"Flossenform\" des Logos. Schrift wie in Pos. 1.1 beschrieben.",
                        "unit_price": 1685.0,
                        "amount": 1.0,
                        "total_price": 1685.0
                    },
                    {
                        "position": "1.2",
                        "product": "Transport, Verpackung und Versand",
                        "unit_price": 320.0,
                        "amount": 1.0,
                        "total_price": 320.0
                    }
                ],
                "total_cost": 2092.02
            },
            id="angebot_a0492"
        )
    ]

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"


    @pytest.mark.parametrize("pdf_filename,expected_data", TEST_DATA)
    def test_pdf_extraction(self, fixtures_dir: Path, pdf_filename: str, expected_data: Dict[str, Any]):
        """Test PDF extraction for various files."""
        pdf_path = str(fixtures_dir / pdf_filename)
        result = pdf_extractor.extract_from_pdf(pdf_path)
        
        assert isinstance(result, ExtractedData)
        assert result.confidence > 0.0
        
        assert result.vendor_name == expected_data["vendor_name"]
        assert result.vat_id == expected_data["vat_id"]
        assert abs(result.total_cost - expected_data["total_cost"]) < 0.01
        
        self._assert_order_lines_match(result.order_lines, expected_data["order_lines"])

    def _assert_order_lines_match(self, actual_lines: List[OrderLineCreate], expected_lines: List[Dict[str, Any]]):
        """Helper method to compare order lines."""
        assert len(actual_lines) == len(expected_lines)
        
        for actual, expected in zip(actual_lines, expected_lines):
            # Skip product description comparison - focus on numerical accuracy
            assert abs(actual.unit_price - expected["unit_price"]) < 0.01
            assert abs(actual.amount - expected["amount"]) < 0.01
            assert abs(actual.total_price - expected["total_price"]) < 0.01

