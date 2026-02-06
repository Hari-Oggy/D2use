"""
RIGOROUS VALIDATION SUITE - UPDATED

Tests each component with the CORRECT APIs.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_3_license_detector():
    """Test 3: License Detector - FIXED"""
    print("\n" + "="*70)
    print("TEST 3: License Detector (Production Grade)")
    print("="*70 + "\n")
    
    from src.processing.license_detector import LicenseDetector
    
    detector = LicenseDetector()
    
    test_cases = [
        ("This dataset is CC0 1.0 Public Domain", "CC0-1.0"),
        ("MIT License", "MIT"),
        ("Apache 2.0", "Apache-2.0"),
        ({"license": "MIT"}, "MIT"),  # Dict input
        ("No license info", "UNKNOWN")
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = detector.detect(text)  # NEW API
        status = "✅" if result.license_type == expected else "❌"
        print(f"{status} Input: {str(text)[:40]}")
        print(f"   Expected: {expected}, Got: {result.license_type} (conf: {result.confidence:.2f})")
        if result.license_type == expected:
            passed += 1
    
    print(f"\n  Score: {passed}/{len(test_cases)}")
    
    if passed == len(test_cases):
        print("  🎉 LICENSE DETECTOR IS PRODUCTION-READY!")
        return True
    else:
        print(f"  ⚠️  {len(test_cases) - passed} tests failed")
        return False


async def main():
    """Quick test of fixed license detector"""
    print("\n" + "="*70)
    print("🔬 LICENSE DETECTOR VALIDATION")
    print("="*70)
    
    success = await test_3_license_detector()
    
    print("\n" + "="*70)
    if success:
        print("✅ LICENSE DETECTOR FIXED AND VALIDATED!")
    else:
        print("❌ LICENSE DETECTOR STILL HAS ISSUES")
    print("="*70 + "\n")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
