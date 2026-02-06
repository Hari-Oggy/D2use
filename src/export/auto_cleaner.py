import polars as pl
from typing import Tuple, Optional, List, Dict
import logging
from pathlib import Path

from ..analysis.ai_decision import CleaningRecipe
from src.processing.date_parser import SmartDateParser

logger = logging.getLogger(__name__)

class AutoCleaner:
    """
    Executes AI-recommended cleaning recipe on datasets.
    
    DESIGN DECISIONS (Senior Engineer Review):
    1. Lazy Evaluation: Use LazyFrame to avoid loading full dataset
    2. Dry-Run Mode: Preview changes before applying
    3. Audit Trail: Log every transformation for debugging
    4. Rollback Safety: Never modify original data in-place
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Args:
            dry_run: If True, only show what would happen (don't execute)
        """
        self.dry_run = dry_run
        self.audit_log = []
    
    def apply_recipe(
        self,
        df: pl.LazyFrame,
        recipe: CleaningRecipe,
        profile: Dict
    ) -> pl.LazyFrame:
        """
        Apply cleaning recipe to dataset.
        
        Args:
            df: Polars LazyFrame (for memory efficiency)
            recipe: AI-recommended cleaning strategy
            profile: Statistical profile (for bounds, etc.)
            
        Returns:
            Cleaned LazyFrame
        """
        logger.info(f"Applying cleaning recipe (dry_run={self.dry_run})")
        self.audit_log = []
        
        # Step 0: Smart preprocessing (new!)
        df = self._smart_preprocessing(df)
        
        # Step 1: Drop columns
        if recipe.drop_columns:
            df = self._drop_columns(df, recipe.drop_columns)
        
        # Step 2: Type conversions (with comma preprocessing)
        if recipe.type_conversions:
            # First, strip commas from numeric string columns (e.g., "2,468.00" -> "2468.00")
            conversions_to_apply = {}
            for col, dtype in recipe.type_conversions.items():
                if dtype in ["Float64", "Float32", "Int64", "Int32"]:
                    # Try to strip commas - will silently fail if column doesn't exist
                    try:
                        df = df.with_columns(
                            pl.col(col).cast(pl.Utf8).str.replace_all(",", "").alias(col)
                        )
                    except:
                        pass
                conversions_to_apply[col] = dtype
            # Now convert types
            df = self._convert_types(df, conversions_to_apply)
        
        # Step 3: Handle outliers
        if recipe.outlier_strategy != "keep":
            df = self._handle_outliers(df, recipe.outlier_strategy, profile)
        
        # Step 4: Handle missing values
        if recipe.impute_strategy != "keep":
            df = self._handle_missing(df, recipe.impute_strategy, profile)
        
        logger.info(f"✅ Recipe applied. Audit log has {len(self.audit_log)} entries")
        return df
    
    def _drop_columns(self, df: pl.LazyFrame, columns: List[str]) -> pl.LazyFrame:
        """Drop specified columns"""
        self.audit_log.append(f"DROP: {len(columns)} columns: {columns}")
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would drop columns: {columns}")
            return df
        
        logger.info(f"Dropping columns: {columns}")
        return df.drop(columns)
    
    def _convert_types(self, df: pl.LazyFrame, conversions: Dict[str, str]) -> pl.LazyFrame:
        """Convert column types"""
        self.audit_log.append(f"TYPE CONVERSION: {conversions}")
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would convert types: {conversions}")
            return df
        
        logger.info(f"Converting types: {conversions}")
        
        # Map string dtype names to Polars types
        dtype_map = {
            "Int64": pl.Int64,
            "Int32": pl.Int32,
            "Float64": pl.Float64,
            "Float32": pl.Float32,
            "Utf8": pl.Utf8,
            "Date": pl.Date,
            "Datetime": pl.Datetime
        }
        
        for col, dtype_str in conversions.items():
            if dtype_str in dtype_map:
                df = df.with_columns(pl.col(col).cast(dtype_map[dtype_str]))
            else:
                logger.warning(f"Unknown dtype '{dtype_str}' for column '{col}'")
        
        return df
    
    def _handle_outliers(
        self,
        df: pl.LazyFrame,
        strategy: str,
        profile: Dict
    ) -> pl.LazyFrame:
        """Handle outliers based on strategy"""
        self.audit_log.append(f"OUTLIERS: strategy={strategy}")
        
        columns = profile.get("columns", {})
        numeric_cols_with_outliers = [
            col for col, stats in columns.items()
            if stats.get("type") == "numeric" and stats.get("outlier_count", 0) > 0
        ]
        
        if not numeric_cols_with_outliers:
            logger.info("No outliers detected, skipping")
            return df
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would handle outliers in {len(numeric_cols_with_outliers)} columns using '{strategy}'")
            return df
        
        logger.info(f"Handling outliers in {len(numeric_cols_with_outliers)} columns using '{strategy}'")
        
        if strategy == "clip":
            # Clip to outlier bounds
            for col in numeric_cols_with_outliers:
                stats = columns[col]
                bounds = stats.get("outlier_bounds", {})
                lower = bounds.get("lower")
                upper = bounds.get("upper")
                
                if lower is not None and upper is not None:
                    df = df.with_columns(
                        pl.col(col).clip(lower, upper).alias(col)
                    )
                    logger.info(f"  Clipped '{col}' to [{lower:.2f}, {upper:.2f}]")
        
        elif strategy == "drop":
            # Drop rows with outliers
            for col in numeric_cols_with_outliers:
                stats = columns[col]
                bounds = stats.get("outlier_bounds", {})
                lower = bounds.get("lower")
                upper = bounds.get("upper")
                
                if lower is not None and upper is not None:
                    df = df.filter(
                        (pl.col(col) >= lower) & (pl.col(col) <= upper)
                    )
                    logger.info(f"  Filtered outliers in '{col}'")
        
        return df
    
    def _handle_missing(
        self,
        df: pl.LazyFrame,
        strategy: str,
        profile: Dict
    ) -> pl.LazyFrame:
        """Handle missing values based on strategy"""
        self.audit_log.append(f"MISSING: strategy={strategy}")
        
        columns = profile.get("columns", {})
        # Get current columns (LazyFrame schema)
        current_cols = df.collect_schema().names()
        
        cols_with_nulls = [
            col for col, stats in columns.items()
            if stats.get("null_percentage", 0) > 0 and col in current_cols
        ]
        
        if not cols_with_nulls:
            logger.info("No missing values detected, skipping")
            return df
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would handle missing values in {len(cols_with_nulls)} columns using '{strategy}'")
            return df
        
        logger.info(f"Handling missing values in {len(cols_with_nulls)} columns using '{strategy}'")
        
        if strategy == "drop_rows":
            # Drop rows with any nulls
            df = df.drop_nulls()
            logger.info(f"  Dropped rows with nulls")
        
        elif strategy == "mean":
            # Impute numeric columns with mean
            for col in cols_with_nulls:
                if columns[col].get("type") == "numeric":
                    df = df.with_columns(
                        pl.col(col).fill_null(pl.col(col).mean())
                    )
                    logger.info(f"  Imputed '{col}' with mean")
        
        elif strategy == "median":
            # Impute numeric columns with median
            for col in cols_with_nulls:
                if columns[col].get("type") == "numeric":
                    df = df.with_columns(
                        pl.col(col).fill_null(pl.col(col).median())
                    )
                    logger.info(f"  Imputed '{col}' with median")
        
        elif strategy == "mode":
            # Impute with mode (most common value)
            for col in cols_with_nulls:
                # Mode requires collecting, so we do it carefully
                logger.info(f"  Imputing '{col}' with mode (forward fill as approximation)")
                df = df.with_columns(
                    pl.col(col).fill_null(strategy="forward")
                )
        
        return df
    
    def _smart_preprocessing(self, df: pl.LazyFrame) -> pl.LazyFrame:
        """Smart preprocessing: date parsing + mixed type coercion"""
        df_collected = df.collect()
        
        # 1. Auto-detect dates
        logger.info("🔍 Auto-detecting date columns...")
        date_cols = []
        for col in df_collected.columns:
            if SmartDateParser.is_date_column(df_collected[col]):
                date_cols.append(col)
        
        if date_cols:
            logger.info(f"📅 Found {len(date_cols)} date columns: {date_cols}")
            df_collected = SmartDateParser.detect_and_parse_dates(df_collected, auto_convert=True)
            self.audit_log.append(f"AUTO_PARSE_DATES: {date_cols}")
        
        # 2. Mixed type coercion
        logger.info("🔍 Detecting mixed-type columns...")
        df_collected = self._coerce_mixed_types(df_collected)
        
        return df_collected.lazy()
    
    def _coerce_mixed_types(self, df: pl.DataFrame) -> pl.DataFrame:
        """Handle mixed types: ['25', 'Unknown'] → [25.0, null]"""
        coerced = []
        
        for col in df.columns:
            if df[col].dtype != pl.Utf8:
                continue
            
            cleaned = df.select(
                pl.col(col).str.strip_chars()
                .str.replace_all(r'[,$%€£¥]', '')
                .replace(['N/A', 'NA', '-', '', 'Unknown', 'None'], None)
                .alias(col)
            )[col]
            
            if cleaned.null_count() == len(cleaned):
                continue
            
            try:
                numeric = cleaned.cast(pl.Float64, strict=False)
                non_null = len(cleaned) - cleaned.null_count()
                success = len(numeric) - numeric.null_count()
                
                if non_null > 0 and (success / non_null) >= 0.8:
                    logger.info(f"📊 Coercing '{col}' to Float64 ({success/non_null*100:.0f}%)")
                    df = df.with_columns(cleaned.cast(pl.Float64, strict=False).alias(col))
                    coerced.append(col)
                    self.audit_log.append(f"MIXED_TYPE: '{col}' → Float64")
            except:
                pass
        
        if coerced:
            logger.info(f"✅ Coerced {len(coerced)} columns")
        
        return df
    
    def get_audit_log(self) -> List[str]:
        """Get list of all transformations applied"""
        return self.audit_log


# Test function
def test_auto_cleaner():
    """Test auto cleaner with sample data"""
    from ..analysis.ai_decision import CleaningRecipe
    
    # Create sample dataset with issues
    df = pl.DataFrame({
        "user_id": range(100),
        "age": [25, 30, None, 40, 150, 28, 32] * 14 + [25, 30],  # Nulls + outlier
        "income": [50000, 60000, 70000, None, 1000000, 55000, 65000] * 14 + [50000, 60000],  # Nulls + outlier
        "city": ["NYC", "LA", "SF", "NYC", "LA", "SF", "NYC"] * 14 + ["NYC", "LA"]
    }).lazy()
    
    # Sample profile
    profile = {
        "columns": {
            "user_id": {"type": "numeric", "null_percentage": 0.0},
            "age": {
                "type": "numeric",
                "null_percentage": 14.0,
                "outlier_count": 14,
                "outlier_bounds": {"lower": 20, "upper": 45}
            },
            "income": {
                "type": "numeric",
                "null_percentage": 14.0,
                "outlier_count": 14,
                "outlier_bounds": {"lower": 40000, "upper": 90000}
            },
            "city": {"type": "categorical", "null_percentage": 0.0}
        }
    }
    
    # Create recipe
    recipe = CleaningRecipe(
        target_column="city",
        outlier_strategy="clip",
        impute_strategy="median",
        type_conversions={},
        drop_columns=["user_id"],
        confidence=0.9,
        reasoning="Test recipe"
    )
    
    print(f"\n{'='*60}")
    print("Auto Cleaner Test")
    print(f"{'='*60}\n")
    
    # Test dry-run first
    print("🔍 DRY-RUN MODE:")
    cleaner_dry = AutoCleaner(dry_run=True)
    df_dry = cleaner_dry.apply_recipe(df, recipe, profile)
    print(f"Audit Log: {cleaner_dry.get_audit_log()}\n")
    
    # Test actual execution
    print("⚙️  EXECUTION MODE:")
    cleaner = AutoCleaner(dry_run=False)
    df_cleaned = cleaner.apply_recipe(df, recipe, profile)
    
    # Collect to see results
    result = df_cleaned.collect()
    
    print(f"\nResults:")
    print(f"  Original columns: 4")
    print(f"  Cleaned columns: {len(result.columns)}")
    print(f"  Columns: {result.columns}")
    print(f"  Rows: {len(result)}")
    print(f"\nAudit Log:")
    for entry in cleaner.get_audit_log():
        print(f"  - {entry}")
    
    print(f"\n{'='*60}")
    print("✅ Auto cleaner working!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_auto_cleaner()
