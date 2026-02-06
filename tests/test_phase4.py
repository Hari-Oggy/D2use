"""
Phase 4 Test Suite - Compliance & AI Cleaning

Tests Layer 3 implementation:
1. License Detector (regex patterns)
2. Compliance Scorer (quality scoring)
3. Stream Downloader (memory bomb prevention)
4. Schema Standardizer (AI column cleaning with LM Studio)

Run with: python -m tests.test_phase4
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processing.license_detector import LicenseDetector
from src.processing.compliance_scorer import ComplianceScorer
from src.processing.stream_downloader import StreamDownloader
from src.processing.schema_standardizer import SchemaStandardizer
from src.schemas import DatasetCandidate, SourceType
from pydantic import HttpUrl

async def test_phase4():
    """
    Test Phase 4: Compliance & AI Cleaning
    """
    print("\n" + "="*70)
    print("PHASE 4 TEST: Compliance & AI Cleaning")
    print("="*70 + "\n")
    
    results = []
    
    # Test 1: License Detector
    print("🧪 Test 1: License Detector")
    print("-" * 70)
    
    detector = LicenseDetector()
    test_licenses = [
        ("Released under CC0 1.0", "CC0-1.0"),
        ("MIT License", "MIT"),
        ("Apache License 2.0", "Apache-2.0")
    ]
    
    license_passed = True
    for text, expected in test_licenses:
        result = detector.detect_license(text)
        if result == expected:
            print(f"✅ Detected: {expected}")
        else:
            print(f"❌ Failed: Expected {expected}, got {result}")
            license_passed = False
    
    results.append(("License Detector", license_passed))
    print()
    
    # Test 2: Compliance Scorer
    print("🧪 Test 2: Compliance Scorer")
    print("-" * 70)
    
    scorer = ComplianceScorer()
    
    good_dataset = DatasetCandidate(
        source_id="test/good",
        url=HttpUrl("https://example.com/good"),
        source_type=SourceType.WEB_SCRAPE,
        is_downloadable=True,
        file_metadata={
            "size_mb": 10.0,
            "file_extension": "csv",
            "license": "MIT"
        },
        compliance_score=0.0
    )
    
    score = scorer.calculate_score(good_dataset)
    compliance_passed = score >= 0.8
    
    print(f"Dataset Score: {score}")
    print(f"{'✅' if compliance_passed else '❌'} Compliance scoring working")
    results.append(("Compliance Scorer", compliance_passed))
    print()
    
    # Test 3: Stream Downloader
    print("🧪 Test 3: Stream Downloader (Memory Bomb Prevention)")
    print("-" * 70)
    
    downloader = StreamDownloader(max_file_size_mb=50)
    test_url = "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv"
    output_path = Path("downloads/test_phase4.csv")
    
    try:
        result = await downloader.download_chunked(test_url, output_path)
        download_passed = result is not None and result.exists()
        
        if download_passed:
            size_mb = result.stat().st_size / (1024 * 1024)
            print(f"✅ Downloaded: {size_mb:.2f}MB")
            print(f"   Memory safe: {size_mb < 50}")
        else:
            print(f"❌ Download failed")
        
        await downloader.close()
    except Exception as e:
        print(f"❌ Download error: {e}")
        download_passed = False
    
    results.append(("Stream Downloader", download_passed))
    print()
    
    # Test 4: Schema Standardizer
    print("🧪 Test 4: Schema Standardizer (AI Column Cleaning)")
    print("-" * 70)
    
    standardizer = SchemaStandardizer(use_local_llm=True)
    messy_columns = ["User ID", "First Name", "Email Address"]
    
    try:
        mapping = await standardizer.standardize_columns(messy_columns)
        
        # Check if all columns are standardized
        all_standardized = all(
            v.islower() and v.replace('_', '').isalnum()
            for v in mapping.values()
        )
        
        if all_standardized:
            print(f"✅ Standardized {len(messy_columns)} columns")
            for orig, std in mapping.items():
                print(f"   '{orig}' → '{std}'")
        else:
            print(f"❌ Standardization incomplete")
        
        schema_passed = all_standardized
        await standardizer.close()
    except Exception as e:
        print(f"❌ Schema standardization error: {e}")
        schema_passed = False
    
    results.append(("Schema Standardizer", schema_passed))
    print()
    
    # Summary
    print("="*70)
    print("📊 Test Summary")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n{'='*70}")
    print(f"📈 Test Score: {passed_count}/{total_count} checks passed")
    print(f"{'='*70}\n")
    
    if passed_count == total_count:
        print("🎉 PHASE 4 COMPLETE: All compliance & cleaning features working!\n")
        return True
    else:
        print("⚠️  PHASE 4 PARTIAL: Some checks failed\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase4())
    sys.exit(0 if success else 1)
