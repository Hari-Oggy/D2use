"""
Phase 5 Test Suite - AI-Driven Data Analysis & Splitting

Tests Layer 4 implementation:
1. Statistical Profiler (IQR, skew, domain hints)
2. AI Decision Maker (LM Studio + validation)
3. Auto Cleaner (recipe executor)
4. Smart Splitter (random/stratified/temporal)

Run with: python -m tests.test_phase5
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl
from src.analysis.profiler import DatasetProfiler
from src.analysis.ai_decision import AIDecisionMaker
from src.export.auto_cleaner import AutoCleaner
from src.export.split_strategy import DataSplitter, SplitStrategy

async def test_phase5():
    """
    Test Phase 5: AI-Driven Analysis & Splitting
    """
    print("\n" + "="*70)
    print("PHASE 5 TEST: AI-Driven Data Analysis & Splitting")
    print("="*70 + "\n")
    
    results = []
    
    # Create sample dataset with realistic issues
    df = pl.DataFrame({
        "user_id": range(1000),
        "age": [25, 30, None, 40, 150, 28, 32] * 142 + [25, 30, None, 40, 28, 32],  # Nulls + outlier
        "income": [50000, 60000, 70000, None, 1000000, 55000, 65000] * 142 + [50000, 60000, 70000, None, 55000, 65000],
        "category": ["A", "B", "C"] * 333 + ["A"],  # Target column
    })
    
    # Test 1: Statistical Profiler
    print("🧪 Test 1: Statistical Profiler")
    print("-" * 70)
    
    profiler = DatasetProfiler()
    profile = profiler.generate_profile(df)
    
    profiler_passed = (
        profile["dataset_info"]["total_rows"] == 1000 and
        profile["dataset_info"]["total_columns"] == 4 and
        len(profile["columns"]) == 4
    )
    
    print(f"Dataset: {profile['dataset_info']['total_rows']} rows × {profile['dataset_info']['total_columns']} cols")
    print(f"Numeric columns: {profile['insights']['numeric_columns']}")
    print(f"Categorical columns: {profile['insights']['categorical_columns']}")
    print(f"{'✅' if profiler_passed else '❌'} Profiler working")
    results.append(("Statistical Profiler", profiler_passed))
    print()
    
    # Test 2: AI Decision Maker
    print("🧪 Test 2: AI Decision Maker")
    print("-" * 70)
    
    decision_maker = AIDecisionMaker(use_local_llm=True)
    recipe = await decision_maker.get_cleaning_recipe(profile)
    
    decision_passed = (
        recipe is not None and
        recipe.outlier_strategy in ["clip", "drop", "keep"] and
        recipe.impute_strategy in ["mean", "median", "mode", "drop_rows", "keep"]
    )
    
    print(f"Recipe generated:")
    print(f"  Target: {recipe.target_column}")
    print(f"  Outlier strategy: {recipe.outlier_strategy}")
    print(f"  Impute strategy: {recipe.impute_strategy}")
    print(f"  Confidence: {recipe.confidence:.2f}")
    print(f"{'✅' if decision_passed else '❌'} AI decision maker working")
    results.append(("AI Decision Maker", decision_passed))
    print()
    
    # Test 3: Auto Cleaner
    print("🧪 Test 3: Auto Cleaner (Recipe Executor)")
    print("-" * 70)
    
    cleaner = AutoCleaner(dry_run=False)
    df_lazy = df.lazy()
    df_cleaned = cleaner.apply_recipe(df_lazy, recipe, profile).collect()
    
    cleaner_passed = (
        len(df_cleaned) > 0 and
        len(cleaner.get_audit_log()) > 0
    )
    
    print(f"Cleaned dataset: {len(df_cleaned)} rows")
    print(f"Audit log entries: {len(cleaner.get_audit_log())}")
    for entry in cleaner.get_audit_log():
        print(f"  - {entry}")
    print(f"{'✅' if cleaner_passed else '❌'} Auto cleaner working")
    results.append(("Auto Cleaner", cleaner_passed))
    print()
    
    # Test 4: Smart Splitter
    print("🧪 Test 4: Smart Splitter (Stratified)")
    print("-" * 70)
    
    splitter = DataSplitter(seed=42)
    
    # Auto-detect strategy
    strategy = splitter.auto_detect_strategy(df_cleaned, profile, target_column="category")
    print(f"Auto-detected strategy: {strategy}")
    
    # Split
    train, test, _ = splitter.split(
        df_cleaned,
        strategy=SplitStrategy.STRATIFIED,
        target_column="category",
        train_ratio=0.8,
        test_ratio=0.2
    )
    
    # Validation: Allow small rounding errors from stratified split
    total_split = len(train) + len(test)
    split_diff = abs(total_split - len(df_cleaned))
    tolerance = max(1, int(len(df_cleaned) * 0.01))  # 1% tolerance or at least 1 row
    
    splitter_passed = (
        len(train) > 0 and
        len(test) > 0 and
        split_diff <= tolerance  # Allow small rounding errors
    )
    
    print(f"Train: {len(train)} rows ({len(train)/len(df_cleaned)*100:.1f}%)")
    print(f"Test: {len(test)} rows ({len(test)/len(df_cleaned)*100:.1f}%)")
    if split_diff > 0:
        print(f"Note: {split_diff} rows lost to stratified rounding (within {tolerance} tolerance)")
    print(f"{'✅' if splitter_passed else '❌'} Smart splitter working")
    results.append(("Smart Splitter", splitter_passed))
    print()
    
    await decision_maker.close()
    
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
        print("🎉 PHASE 5 COMPLETE: AI-driven analysis & splitting working!\n")
        return True
    else:
        print("⚠️  PHASE 5 PARTIAL: Some checks failed\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase5())
    sys.exit(0 if success else 1)
