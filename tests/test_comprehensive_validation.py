"""
COMPREHENSIVE SYSTEM VALIDATION
Tests all 6 phases of the ML Dataset Factory roadmap.
"""

import asyncio
import logging
from pathlib import Path
from src.orchestrator_v2 import OrchestratorV2

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def test_phase_1_hf_kaggle():
    """Phase 1: Test HuggingFace & Kaggle Search"""
    print("\n" + "="*80)
    print("PHASE 1: HuggingFace & Kaggle Search")
    print("="*80)
    
    orchestrator = OrchestratorV2(use_local_llm=False)
    
    # Test with a known dataset
    results = await orchestrator.intelligent_search("iris", limit=5, expand_query=False)
    
    print(f"✓ Found {len(results)} candidates")
    if results:
        print(f"✓ Top result: {results[0].source_id} (Score: {results[0].compliance_score:.2f})")
        print(f"✓ Source: {results[0].source_type}")
    
    await orchestrator.close()
    return len(results) > 0

async def test_phase_2_web_fallback():
    """Phase 2: Test Web Scraper Fallback"""
    print("\n" + "="*80)
    print("PHASE 2: Web Scraper Fallback (Real World)")
    print("="*80)
    
    orchestrator = OrchestratorV2(use_local_llm=False)
    
    # Force web scraping by mocking HF/Kaggle to return nothing
    from unittest.mock import AsyncMock
    orchestrator.searcher.hf.search_datasets = AsyncMock(return_value=[])
    orchestrator.searcher.kaggle.search_datasets = AsyncMock(return_value=[])
    
    # Mock web search to return real GitHub URL
    from src.schemas import SourceType
    orchestrator.searcher.web.fallback_search = AsyncMock(return_value=[{
        "url": "https://github.com/mwaskom/seaborn-data",
        "title": "Seaborn Data",
        "snippet": "Example datasets"
    }])
    
    results = await orchestrator.intelligent_search("rare_dataset_xyz", limit=5, expand_query=False)
    
    print(f"✓ Found {len(results)} web candidates")
    if results and results[0].source_type == SourceType.WEB_SCRAPE:
        print(f"✓ Web fallback activated: {results[0].url}")
        success = True
    else:
        print("✗ Web fallback FAILED")
        success = False
    
    await orchestrator.close()
    return success

async def test_phase_3_circuit_breaker():
    """Phase 3: Test Circuit Breaker"""
    print("\n" + "="*80)
    print("PHASE 3: Circuit Breaker")
    print("="*80)
    
    from src.scraper.circuit_breaker import CircuitBreaker
    
    # Use smaller window to make test faster
    breaker = CircuitBreaker(failure_threshold=0.5, window_size=5)
    
    # Test normal operation
    assert breaker.can_request("example.com"), "Should allow initial request"
    print("✓ Initial request allowed")
    
    # Simulate failures - need 5 failures (window_size) with >50% failure rate
    # Recording 5 consecutive failures = 100% failure rate > 50% threshold
    for i in range(5):
        breaker.record_failure("example.com")
    
    # Should now block
    blocked = not breaker.can_request("example.com")
    print(f"✓ Circuit breaker {'OPEN (blocking)' if blocked else 'FAILED - still closed'}")
    
    return blocked

async def test_phase_4_ai_cleaning():
    """Phase 4: Test AI Cleaning & Compliance"""
    print("\n" + "="*80)
    print("PHASE 4: AI Cleaning & Compliance Scoring")
    print("="*80)
    
    import polars as pl
    from src.analysis.profiler import DatasetProfiler
    from src.analysis.ai_decision import AIDecisionMaker
    from src.processing.compliance_scorer import ComplianceScorer
    from src.schemas import DatasetCandidate, SourceType
    from pydantic import HttpUrl
    
    # Test Compliance Scorer
    scorer = ComplianceScorer()
    test_candidate = DatasetCandidate(
        source_id="test/dataset",
        source_type=SourceType.HUGGINGFACE,
        url=HttpUrl("https://example.com"),
        is_downloadable=True,
        file_metadata={"size_mb": 10},
        compliance_score=0.0
    )
    
    score = scorer.calculate_score(test_candidate)
    print(f"✓ Compliance score calculated: {score:.2f}")
    
    # Test AI Decision Maker (with fallback)
    ai = AIDecisionMaker(use_local_llm=False)
    dummy_df = pl.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
    profiler = DatasetProfiler()
    profile = profiler.generate_profile(dummy_df)
    
    recipe = await ai.get_cleaning_recipe(profile)
    print(f"✓ AI recipe generated: {recipe.impute_strategy}")
    
    await ai.close()
    return score > 0 and recipe is not None

async def test_phase_5_splitting():
    """Phase 5: Test Data Splitting & Export"""
    print("\n" + "="*80)
    print("PHASE 5: Data Splitting & Export")
    print("="*80)
    
    import polars as pl
    from src.export.split_strategy import DataSplitter
    from src.export.format_converter import FormatConverter
    
    # Create test data
    df = pl.DataFrame({
        "feature1": list(range(100)),
        "feature2": list(range(100, 200)),
        "target": [0, 1] * 50
    })
    
    # Test splitting
    splitter = DataSplitter()
    train, test, val = splitter.split(df, strategy="STRATIFIED", target_column="target")
    
    print(f"✓ Split successful: {len(train)} train, {len(test)} test, {len(val)} val")
    
    # Test export
    converter = FormatConverter(output_dir=Path("output/test_validation"))
    paths = converter.export_split(train, test, val, "test_export", ["csv"])
    
    print(f"✓ Exported to: {paths}")
    
    return len(train) > 0 and paths

async def test_phase_6_end_to_end():
    """Phase 6: End-to-End Pipeline Test"""
    print("\n" + "="*80)
    print("PHASE 6: End-to-End Pipeline (Real Dataset)")
    print("="*80)
    
    orchestrator = OrchestratorV2(use_local_llm=False)
    
    # Search
    print("→ Searching for 'iris'...")
    candidates = await orchestrator.intelligent_search("iris", limit=3, expand_query=False)
    
    if not candidates:
        print("✗ No candidates found")
        await orchestrator.close()
        return False
    
    # Process
    print(f"→ Processing: {candidates[0].source_id}")
    result = await orchestrator.process_dataset(
        candidate_or_id=candidates[0],
        dataset_name="validation_test",
        max_rows=100
    )
    
    if result:
        print(f"✓ Pipeline complete:")
        print(f"  - Original rows: {result['original_rows']}")
        print(f"  - Cleaned rows: {result['cleaned_rows']}")
        print(f"  - Train samples: {result['train_rows']}")
        success = True
    else:
        print("✗ Pipeline FAILED")
        success = False
    
    await orchestrator.close()
    return success

async def main():
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE SYSTEM VALIDATION")
    print("Testing all 6 phases of the ML Dataset Factory")
    print("="*80)
    
    results = {}
    
    try:
        results["Phase 1"] = await test_phase_1_hf_kaggle()
    except Exception as e:
        print(f"✗ Phase 1 ERROR: {e}")
        results["Phase 1"] = False
    
    try:
        results["Phase 2"] = await test_phase_2_web_fallback()
    except Exception as e:
        print(f"✗ Phase 2 ERROR: {e}")
        results["Phase 2"] = False
    
    try:
        results["Phase 3"] = await test_phase_3_circuit_breaker()
    except Exception as e:
        print(f"✗ Phase 3 ERROR: {e}")
        results["Phase 3"] = False
    
    try:
        results["Phase 4"] = await test_phase_4_ai_cleaning()
    except Exception as e:
        print(f"✗ Phase 4 ERROR: {e}")
        results["Phase 4"] = False
    
    try:
        results["Phase 5"] = await test_phase_5_splitting()
    except Exception as e:
        print(f"✗ Phase 5 ERROR: {e}")
        results["Phase 5"] = False
    
    try:
        results["Phase 6"] = await test_phase_6_end_to_end()
    except Exception as e:
        print(f"✗ Phase 6 ERROR: {e}")
        results["Phase 6"] = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 VALIDATION SUMMARY")
    print("="*80)
    
    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {phase}")
    
    total = sum(results.values())
    print(f"\nOverall: {total}/{len(results)} phases passed")
    
    if total == len(results):
        print("\n🎉 ALL SYSTEMS OPERATIONAL!")
    else:
        print(f"\n⚠️  {len(results) - total} phases need attention")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
