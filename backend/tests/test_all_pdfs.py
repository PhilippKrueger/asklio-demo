"""Comprehensive tests for all provided PDF documents."""
import pytest
from pathlib import Path
from app.services.pdf_extractor import pdf_extractor


class TestAllPDFs:
    """Test extraction on all provided vendor offer PDFs."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent / "fixtures"

    def test_all_pdfs_basic_extraction(self, fixtures_dir):
        """
        Test basic extraction on all 4 provided PDFs.

        This test verifies that extraction completes successfully
        and produces reasonable results for all documents.
        """
        pdf_files = [
            "AngebotA0492_23.Pdf",
            "AN-4120-Kdnr-14918.pdf",
            "AN-OF2312380-Kdnr-57692.pdf",
            "Quote_1__Lio_Technologies_GmbH__1x_MBA___2212618452.pdf"
        ]

        print("\n" + "="*80)
        print("TESTING ALL PROVIDED PDFs")
        print("="*80)

        results = []

        for pdf_file in pdf_files:
            pdf_path = fixtures_dir / pdf_file
            assert pdf_path.exists(), f"PDF not found: {pdf_file}"

            print(f"\n📄 Testing: {pdf_file}")
            print("-" * 80)

            try:
                result = pdf_extractor.extract_from_pdf(str(pdf_path))

                # Basic validation
                assert result.vendor_name, "Vendor name should not be empty"
                assert len(result.vendor_name) > 2, "Vendor name too short"

                assert result.total_cost > 0, "Total cost should be positive"

                assert len(result.order_lines) > 0, "Should extract at least one order line"

                assert 0.0 <= result.confidence <= 1.0, "Confidence should be between 0 and 1"

                # Calculate sum
                calculated_sum = sum(line.total_price for line in result.order_lines)

                results.append({
                    "file": pdf_file,
                    "vendor": result.vendor_name,
                    "vat_id": result.vat_id or "N/A",
                    "lines": len(result.order_lines),
                    "total": result.total_cost,
                    "confidence": result.confidence,
                    "sum_match": abs(calculated_sum - result.total_cost) / result.total_cost if result.total_cost > 0 else 1.0
                })

                print(f"  ✓ Extraction successful")
                print(f"    Vendor: {result.vendor_name}")
                print(f"    VAT ID: {result.vat_id or 'N/A'}")
                print(f"    Order lines: {len(result.order_lines)}")
                print(f"    Total: €{result.total_cost:.2f}")
                print(f"    Confidence: {result.confidence:.1%}")
                print(f"    Sum match: {(1 - results[-1]['sum_match']):.1%} accurate")

            except Exception as e:
                print(f"  ✗ Extraction failed: {str(e)}")
                pytest.fail(f"Extraction failed for {pdf_file}: {str(e)}")

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)

        for r in results:
            status = "✓" if r["confidence"] >= 0.7 else "⚠️ "
            print(f"\n{status} {r['file']}")
            print(f"    Vendor: {r['vendor']}")
            print(f"    Lines: {r['lines']}, Total: €{r['total']:.2f}, Confidence: {r['confidence']:.1%}")

        print(f"\n✅ All {len(pdf_files)} PDFs processed successfully")

        # Overall stats
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        print(f"\n📊 Average confidence: {avg_confidence:.1%}")

    def test_quote_1_macbook(self, fixtures_dir):
        """
        Test Quote_1__Lio_Technologies_GmbH__1x_MBA___2212618452.pdf
        This is the Apple MacBook quote we tested earlier.
        """
        pdf_path = fixtures_dir / "Quote_1__Lio_Technologies_GmbH__1x_MBA___2212618452.pdf"
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        print(f"\n" + "="*80)
        print("APPLE MACBOOK QUOTE DETAILED TEST")
        print("="*80)

        print(f"\nVendor: {result.vendor_name}")
        print(f"VAT ID: {result.vat_id}")
        print(f"Department: {result.department}")
        print(f"Total: €{result.total_cost:.2f}")
        print(f"Confidence: {result.confidence:.1%}")

        # Should extract Apple as vendor
        assert "apple" in result.vendor_name.lower(), \
            f"Expected 'Apple' in vendor name, got '{result.vendor_name}'"

        # Should have VAT ID
        assert result.vat_id, "VAT ID should be extracted"

        # Should have at least the MacBook item
        assert len(result.order_lines) >= 1, "Should have at least 1 order line"

        # Check for MacBook in order lines
        has_macbook = any("macbook" in line.position_description.lower()
                         for line in result.order_lines)
        assert has_macbook, "Should extract MacBook item"

        print(f"\n📦 Order lines:")
        for i, line in enumerate(result.order_lines, 1):
            print(f"  {i}. {line.position_description[:60]}... - €{line.total_price:.2f}")

        print(f"\n✅ MacBook quote test passed")

    def test_an_4120_extraction(self, fixtures_dir):
        """
        Test AN-4120-Kdnr-14918.pdf extraction.
        """
        pdf_path = fixtures_dir / "AN-4120-Kdnr-14918.pdf"
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        print(f"\n" + "="*80)
        print("AN-4120 DOCUMENT TEST")
        print("="*80)

        print(f"\nVendor: {result.vendor_name}")
        print(f"VAT ID: {result.vat_id}")
        print(f"Order lines: {len(result.order_lines)}")
        print(f"Total: €{result.total_cost:.2f}")
        print(f"Confidence: {result.confidence:.1%}")

        # Basic validation
        assert result.vendor_name, "Vendor name should be extracted"
        assert len(result.order_lines) > 0, "Should have order lines"
        assert result.total_cost > 0, "Total should be positive"

        print(f"\n📦 Order lines:")
        for i, line in enumerate(result.order_lines, 1):
            print(f"  {i}. {line.position_description[:60]}... - €{line.total_price:.2f}")

        print(f"\n✅ AN-4120 test passed")

    def test_an_of2312380_extraction(self, fixtures_dir):
        """
        Test AN-OF2312380-Kdnr-57692.pdf extraction.
        """
        pdf_path = fixtures_dir / "AN-OF2312380-Kdnr-57692.pdf"
        result = pdf_extractor.extract_from_pdf(str(pdf_path))

        print(f"\n" + "="*80)
        print("AN-OF2312380 DOCUMENT TEST")
        print("="*80)

        print(f"\nVendor: {result.vendor_name}")
        print(f"VAT ID: {result.vat_id}")
        print(f"Order lines: {len(result.order_lines)}")
        print(f"Total: €{result.total_cost:.2f}")
        print(f"Confidence: {result.confidence:.1%}")

        # Basic validation
        assert result.vendor_name, "Vendor name should be extracted"
        assert len(result.order_lines) > 0, "Should have order lines"
        assert result.total_cost > 0, "Total should be positive"

        print(f"\n📦 Order lines:")
        for i, line in enumerate(result.order_lines, 1):
            print(f"  {i}. {line.position_description[:60]}... - €{line.total_price:.2f}")

        print(f"\n✅ AN-OF2312380 test passed")

    def test_confidence_scores_comparison(self, fixtures_dir):
        """
        Compare confidence scores across all PDFs to identify
        which documents are easier or harder to extract.
        """
        pdf_files = [
            "AngebotA0492_23.Pdf",
            "AN-4120-Kdnr-14918.pdf",
            "AN-OF2312380-Kdnr-57692.pdf",
            "Quote_1__Lio_Technologies_GmbH__1x_MBA___2212618452.pdf"
        ]

        print(f"\n" + "="*80)
        print("CONFIDENCE SCORES COMPARISON")
        print("="*80)

        scores = []

        for pdf_file in pdf_files:
            pdf_path = fixtures_dir / pdf_file
            result = pdf_extractor.extract_from_pdf(str(pdf_path))

            scores.append({
                "file": pdf_file,
                "confidence": result.confidence,
                "lines": len(result.order_lines),
                "has_vat": bool(result.vat_id),
                "has_dept": bool(result.department)
            })

        # Sort by confidence
        scores.sort(key=lambda x: x["confidence"], reverse=True)

        print(f"\nRanked by confidence (highest first):")
        for i, score in enumerate(scores, 1):
            status = "🟢" if score["confidence"] >= 0.8 else "🟡" if score["confidence"] >= 0.6 else "🔴"
            print(f"\n  {i}. {status} {score['file']}")
            print(f"      Confidence: {score['confidence']:.1%}")
            print(f"      Lines: {score['lines']}")
            print(f"      Has VAT ID: {'✓' if score['has_vat'] else '✗'}")
            print(f"      Has Department: {'✓' if score['has_dept'] else '✗'}")

        print(f"\n✅ Confidence comparison complete")
