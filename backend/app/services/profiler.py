import cProfile
import time
from pathlib import Path
from app.services.pdf_extractor import PDFExtractor

def profile_extraction_methods():
    """Profile both extraction methods to identify bottlenecks."""
    
    extractor = PDFExtractor()
    fixtures_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures"
    test_pdf = next(fixtures_dir.glob("*.pdf"))  # Just test one PDF
    
    print(f"Profiling extraction methods on: {test_pdf.name}")
    
    # Profile unstructured method (new default)
    print("\n=== PROFILING UNSTRUCTURED METHOD ===")
    pr = cProfile.Profile()
    pr.enable()
    
    start_time = time.time()
    unstructured_result = extractor._extract_raw_content(str(test_pdf))
    unstructured_time = time.time() - start_time
    
    pr.disable()
    pr.print_stats(sort='cumulative')
    
    print(f"\nUnstructured total time: {unstructured_time:.2f}s")
    print(f"Unstructured extracted: {len(unstructured_result.text)} chars")
    
    # Profile original method (PyPDF + GPT-4o vision)
    print("\n=== PROFILING ORIGINAL METHOD (PyPDF + GPT-4o) ===")
    pr2 = cProfile.Profile()
    pr2.enable()
    
    start_time = time.time()
    original_result = extractor._extract_raw_content_original(str(test_pdf))
    original_time = time.time() - start_time
    
    pr2.disable()
    pr2.print_stats(sort='cumulative')
    
    print(f"\nOriginal total time: {original_time:.2f}s")
    print(f"Original extracted: {len(original_result.text)} chars")
    
    print(f"\n=== COMPARISON ===")
    print(f"Unstructured: {unstructured_time:.2f}s")
    print(f"Original (PyPDF + GPT-4o): {original_time:.2f}s")
    
    if unstructured_time > 0 and original_time > 0:
        if unstructured_time < original_time:
            print(f"Unstructured is {original_time/unstructured_time:.1f}x faster")
        else:
            print(f"Original is {unstructured_time/original_time:.1f}x faster")
    
    # Text comparison
    print(f"\nText length comparison:")
    print(f"  Unstructured: {len(unstructured_result.text)} characters")
    print(f"  Original: {len(original_result.text)} characters")
    print(f"  Ratio: {len(unstructured_result.text)/len(original_result.text):.2f}x")

if __name__ == "__main__":
    profile_extraction_methods()