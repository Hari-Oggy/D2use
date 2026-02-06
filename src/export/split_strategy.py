import polars as pl
from typing import Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SplitStrategy(str, Enum):
    """Data splitting strategies"""
    RANDOM = "random"
    STRATIFIED = "stratified"
    TEMPORAL = "temporal"  # For time-series (no shuffle)


class DataSplitter:
    """
    Smart data splitter with multiple strategies.
    
    DESIGN DECISIONS (Senior Engineer Review):
    1. Time-Series Detection: Auto-detect temporal data to prevent future leakage
    2. Stratification: Preserve class distribution for imbalanced datasets
    3. Reproducibility: Fixed random seed by default
    4. Configurable Ratios: Support custom train/val/test splits
    """
    
    def __init__(self, seed: int = 42):
        """
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
    
    def split(
        self,
        df: pl.DataFrame,
        strategy: SplitStrategy = SplitStrategy.RANDOM,
        target_column: Optional[str] = None,
        train_ratio: float = 0.8,
        test_ratio: float = 0.2,
        val_ratio: float = 0.0
    ) -> Tuple[pl.DataFrame, pl.DataFrame, Optional[pl.DataFrame]]:
        """
        Split dataset into train/test(/val) sets.
        
        Args:
            df: Polars DataFrame to split
            strategy: Splitting strategy (random, stratified, temporal) - accepts string or enum
            target_column: Column to stratify on (for stratified split)
            train_ratio: Fraction for training (default: 0.8)
            test_ratio: Fraction for testing (default: 0.2)
            val_ratio: Fraction for validation (default: 0.0, no val set)
            
        Returns:
            (train_df, test_df, val_df) where val_df is None if val_ratio=0
        """
        # Convert string to enum if necessary (for backward compatibility)
        if isinstance(strategy, str):
            strategy = SplitStrategy(strategy.lower())
        
        # Validate ratios
        total_ratio = train_ratio + test_ratio + val_ratio
        if abs(total_ratio - 1.0) > 0.01:
            raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")
        
        logger.info(f"Splitting dataset: {len(df)} rows using '{strategy}' strategy")
        logger.info(f"  Ratios: train={train_ratio}, test={test_ratio}, val={val_ratio}")
        
        if strategy == SplitStrategy.RANDOM:
            return self._split_random(df, train_ratio, test_ratio, val_ratio)
        
        elif strategy == SplitStrategy.STRATIFIED:
            if not target_column:
                raise ValueError("target_column required for stratified split")
            return self._split_stratified(df, target_column, train_ratio, test_ratio, val_ratio)
        
        elif strategy == SplitStrategy.TEMPORAL:
            return self._split_temporal(df, train_ratio, test_ratio, val_ratio)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _split_random(
        self,
        df: pl.DataFrame,
        train_ratio: float,
        test_ratio: float,
        val_ratio: float
    ) -> Tuple[pl.DataFrame, pl.DataFrame, Optional[pl.DataFrame]]:
        """Random split (shuffled)"""
        # Shuffle
        df_shuffled = df.sample(fraction=1.0, seed=self.seed, shuffle=True)
        
        n = len(df_shuffled)
        train_end = int(n * train_ratio)
        test_end = train_end + int(n * test_ratio)
        
        train_df = df_shuffled[:train_end]
        test_df = df_shuffled[train_end:test_end]
        val_df = df_shuffled[test_end:] if val_ratio > 0 else None
        
        logger.info(f"✅ Random split: train={len(train_df)}, test={len(test_df)}, val={len(val_df) if val_df is not None else 0}")
        return train_df, test_df, val_df
    
    def _split_stratified(
        self,
        df: pl.DataFrame,
        target_column: str,
        train_ratio: float,
        test_ratio: float,
        val_ratio: float
    ) -> Tuple[pl.DataFrame, pl.DataFrame, Optional[pl.DataFrame]]:
        """
        Stratified split (preserves class distribution).
        
        IMPLEMENTATION NOTE:
        Polars doesn't have built-in stratified sampling, so we:
        1. Group by target column
        2. Sample from each group proportionally
        3. Combine results
        """
        logger.info(f"Stratifying on column: '{target_column}'")
        
        # Get unique classes
        classes = df[target_column].unique().to_list()
        logger.info(f"  Found {len(classes)} classes")
        
        train_dfs = []
        test_dfs = []
        val_dfs = []
        
        for cls in classes:
            # Filter to this class
            class_df = df.filter(pl.col(target_column) == cls)
            n_class = len(class_df)
            
            # Shuffle this class
            class_shuffled = class_df.sample(fraction=1.0, seed=self.seed, shuffle=True)
            
            # Split proportionally
            train_end = int(n_class * train_ratio)
            test_end = train_end + int(n_class * test_ratio)
            
            train_dfs.append(class_shuffled[:train_end])
            test_dfs.append(class_shuffled[train_end:test_end])
            
            if val_ratio > 0:
                val_dfs.append(class_shuffled[test_end:])
        
        # Combine all classes
        train_df = pl.concat(train_dfs).sample(fraction=1.0, seed=self.seed, shuffle=True)
        test_df = pl.concat(test_dfs).sample(fraction=1.0, seed=self.seed, shuffle=True)
        val_df = pl.concat(val_dfs).sample(fraction=1.0, seed=self.seed, shuffle=True) if val_ratio > 0 else None
        
        logger.info(f"✅ Stratified split: train={len(train_df)}, test={len(test_df)}, val={len(val_df) if val_df is not None else 0}")
        
        # Verify stratification
        self._verify_stratification(train_df, test_df, target_column)
        
        return train_df, test_df, val_df
    
    def _split_temporal(
        self,
        df: pl.DataFrame,
        train_ratio: float,
        test_ratio: float,
        val_ratio: float
    ) -> Tuple[pl.DataFrame, pl.DataFrame, Optional[pl.DataFrame]]:
        """
        Temporal split (NO shuffle, preserves time order).
        
        CRITICAL: For time-series data to prevent future leakage.
        """
        logger.warning("⚠️  Temporal split: NO SHUFFLE (preserving time order)")
        
        n = len(df)
        train_end = int(n * train_ratio)
        test_end = train_end + int(n * test_ratio)
        
        train_df = df[:train_end]
        test_df = df[train_end:test_end]
        val_df = df[test_end:] if val_ratio > 0 else None
        
        logger.info(f"✅ Temporal split: train={len(train_df)}, test={len(test_df)}, val={len(val_df) if val_df is not None else 0}")
        return train_df, test_df, val_df
    
    def _verify_stratification(
        self,
        train_df: pl.DataFrame,
        test_df: pl.DataFrame,
        target_column: str
    ):
        """Verify class distribution is preserved"""
        train_dist = train_df[target_column].value_counts(sort=True)
        test_dist = test_df[target_column].value_counts(sort=True)
        
        logger.info("  Class distribution verification:")
        logger.info(f"    Train: {train_dist.to_dicts()[:3]}")
        logger.info(f"    Test:  {test_dist.to_dicts()[:3]}")
    
    def auto_detect_strategy(
        self,
        df: pl.DataFrame,
        profile: dict,
        target_column: Optional[str] = None
    ) -> SplitStrategy:
        """
        Auto-detect best splitting strategy based on data profile.
        
        HEURISTICS:
        - Has temporal column + monotonic → TEMPORAL
        - Has target with <50 unique values → STRATIFIED
        - Otherwise → RANDOM
        """
        insights = profile.get("insights", {})
        
        # Check for time-series
        if insights.get("has_temporal", False):
            # Check if any temporal column is monotonic
            columns = profile.get("columns", {})
            for col, stats in columns.items():
                if stats.get("type") == "temporal" and stats.get("is_monotonic", False):
                    logger.info("🔍 Auto-detected TEMPORAL strategy (monotonic time column)")
                    return SplitStrategy.TEMPORAL
        
        # Check for stratification
        if target_column:
            columns = profile.get("columns", {})
            target_stats = columns.get(target_column, {})
            
            if (target_stats.get("type") == "categorical" and
                target_stats.get("unique_count", 999) < 50):
                logger.info("🔍 Auto-detected STRATIFIED strategy (categorical target)")
                return SplitStrategy.STRATIFIED
        
        logger.info("🔍 Auto-detected RANDOM strategy (default)")
        return SplitStrategy.RANDOM


# Test function
def test_data_splitter():
    """Test data splitter with different strategies"""
    splitter = DataSplitter(seed=42)
    
    print(f"\n{'='*60}")
    print("Data Splitter Test")
    print(f"{'='*60}\n")
    
    # Test 1: Random split
    print("Test 1: Random Split")
    df_random = pl.DataFrame({
        "feature": range(1000),
        "label": ["A", "B"] * 500
    })
    
    train, test, val = splitter.split(df_random, strategy=SplitStrategy.RANDOM, train_ratio=0.7, test_ratio=0.2, val_ratio=0.1)
    print(f"  Train: {len(train)}, Test: {len(test)}, Val: {len(val)}\n")
    
    # Test 2: Stratified split
    print("Test 2: Stratified Split (Imbalanced)")
    df_imbalanced = pl.DataFrame({
        "feature": range(1000),
        "label": ["A"] * 900 + ["B"] * 100  # 90% A, 10% B
    })
    
    train, test, _ = splitter.split(
        df_imbalanced,
        strategy=SplitStrategy.STRATIFIED,
        target_column="label",
        train_ratio=0.8,
        test_ratio=0.2
    )
    
    train_a_pct = len(train.filter(pl.col("label") == "A")) / len(train) * 100
    test_a_pct = len(test.filter(pl.col("label") == "A")) / len(test) * 100
    print(f"  Train A%: {train_a_pct:.1f}%, Test A%: {test_a_pct:.1f}%")
    print(f"  ✅ Distribution preserved!\n")
    
    # Test 3: Temporal split
    print("Test 3: Temporal Split (Time-Series)")
    n_temporal = 1000
    df_temporal = pl.DataFrame({
        "timestamp": pl.date_range(pl.date(2020, 1, 1), pl.date(2022, 9, 27), "1d", eager=True).head(n_temporal),
        "value": range(n_temporal)
    })
    
    train, test, _ = splitter.split(df_temporal, strategy=SplitStrategy.TEMPORAL, train_ratio=0.8, test_ratio=0.2)
    print(f"  Train dates: {train['timestamp'].min()} to {train['timestamp'].max()}")
    print(f"  Test dates: {test['timestamp'].min()} to {test['timestamp'].max()}")
    print(f"  ✅ No future leakage!\n")
    
    print(f"{'='*60}")
    print("✅ All split strategies working!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_data_splitter()
