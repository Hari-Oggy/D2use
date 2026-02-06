import polars as pl
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatasetProfiler:
    """
    Statistical profiler for datasets using Polars.
    
    DESIGN DECISIONS (Senior Engineer Review):
    1. Memory Safety: Sample large datasets (>1M rows) to avoid OOM
    2. Robust Stats: Use percentiles + IQR (handles non-normal distributions)
    3. Zero-Division Guards: All calculations protected
    4. Domain Hints: Extract from column names (age, price, date, etc.)
    """
    
    def __init__(self, sample_size: int = 100000):
        """
        Args:
            sample_size: Max rows to analyze (memory safety)
        """
        self.sample_size = sample_size
    
    def generate_profile(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive statistical profile.
        
        Args:
            df: Polars DataFrame to profile
            
        Returns:
            Dict with dataset-level and column-level statistics
        """
        logger.info(f"Profiling dataset: {df.shape[0]} rows × {df.shape[1]} columns")
        
        # Memory safety: Sample if too large
        if df.shape[0] > self.sample_size:
            logger.warning(f"Dataset too large, sampling {self.sample_size} rows")
            df_sample = df.sample(n=self.sample_size, seed=42)
        else:
            df_sample = df
        
        profile = {
            "dataset_info": {
                "total_rows": df.shape[0],
                "total_columns": df.shape[1],
                "sampled": df.shape[0] > self.sample_size,
                "sample_size": df_sample.shape[0]
            },
            "columns": {}
        }
        
        # Profile each column
        for col in df_sample.columns:
            profile["columns"][col] = self._profile_column(df_sample, col)
        
        # Dataset-level insights
        profile["insights"] = self._generate_insights(profile["columns"])
        
        return profile
    
    def _profile_column(self, df: pl.DataFrame, col: str) -> Dict[str, Any]:
        """Profile a single column with robust statistics"""
        col_data = df[col]
        
        # Basic info
        dtype = str(col_data.dtype)
        null_count = col_data.null_count()
        total_count = len(col_data)
        null_pct = (null_count / total_count * 100) if total_count > 0 else 0
        
        profile = {
            "dtype": dtype,
            "null_count": null_count,
            "null_percentage": round(null_pct, 2),
            "unique_count": col_data.n_unique(),
            "domain_hint": self._detect_domain(col)
        }
        
        # Type-specific statistics
        if dtype in ["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float32", "Float64"]:
            profile.update(self._profile_numeric(col_data))
        elif dtype in ["Utf8", "Categorical"]:
            profile.update(self._profile_categorical(col_data))
        elif dtype == "Date" or dtype == "Datetime":
            profile.update(self._profile_temporal(col_data))
        
        return profile
    
    def _profile_numeric(self, col: pl.Series) -> Dict[str, Any]:
        """Profile numeric column with robust outlier detection"""
        # Remove nulls for stats
        col_clean = col.drop_nulls()
        
        if len(col_clean) == 0:
            return {"type": "numeric", "all_null": True}
        
        # Basic stats
        stats = {
            "type": "numeric",
            "min": float(col_clean.min()),
            "max": float(col_clean.max()),
            "mean": float(col_clean.mean()),
            "median": float(col_clean.median()),
            "std": float(col_clean.std()) if len(col_clean) > 1 else 0.0
        }
        
        # Percentiles for robust outlier detection
        try:
            q1 = float(col_clean.quantile(0.25))
            q3 = float(col_clean.quantile(0.75))
            iqr = q3 - q1
            
            # Outlier bounds (Tukey's fences)
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = col_clean.filter((col_clean < lower_bound) | (col_clean > upper_bound))
            outlier_count = len(outliers)
            outlier_pct = (outlier_count / len(col_clean) * 100) if len(col_clean) > 0 else 0
            
            stats.update({
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "outlier_count": outlier_count,
                "outlier_percentage": round(outlier_pct, 2),
                "outlier_bounds": {"lower": lower_bound, "upper": upper_bound}
            })
        except Exception as e:
            logger.warning(f"Could not calculate percentiles: {e}")
            stats["outlier_count"] = 0
        
        # Skewness (with zero-division guard)
        if stats["std"] > 0:
            skew = (stats["mean"] - stats["median"]) / stats["std"]
            stats["skewness"] = round(skew, 3)
            stats["is_skewed"] = abs(skew) > 1.0
        else:
            stats["skewness"] = 0.0
            stats["is_skewed"] = False
        
        return stats
    
    def _profile_categorical(self, col: pl.Series) -> Dict[str, Any]:
        """Profile categorical/string column"""
        col_clean = col.drop_nulls()
        
        if len(col_clean) == 0:
            return {"type": "categorical", "all_null": True}
        
        value_counts = col_clean.value_counts()
        unique_count = len(value_counts)
        
        # Check if it's high cardinality (likely ID or free text)
        is_high_cardinality = unique_count > len(col_clean) * 0.5
        
        # Top values
        top_values = value_counts.head(5).to_dicts()
        
        return {
            "type": "categorical",
            "unique_count": unique_count,
            "is_high_cardinality": is_high_cardinality,
            "top_values": top_values,
            "cardinality_ratio": round(unique_count / len(col_clean), 3)
        }
    
    def _profile_temporal(self, col: pl.Series) -> Dict[str, Any]:
        """Profile date/datetime column"""
        col_clean = col.drop_nulls()
        
        if len(col_clean) == 0:
            return {"type": "temporal", "all_null": True}
        
        return {
            "type": "temporal",
            "min_date": str(col_clean.min()),
            "max_date": str(col_clean.max()),
            "is_monotonic": col_clean.is_sorted()
        }
    
    def _detect_domain(self, col_name: str) -> Optional[str]:
        """Detect domain from column name (heuristic)"""
        col_lower = col_name.lower()
        
        # Common patterns
        if any(x in col_lower for x in ["age", "year", "born"]):
            return "age"
        elif any(x in col_lower for x in ["price", "cost", "amount", "salary", "revenue"]):
            return "price"
        elif any(x in col_lower for x in ["date", "time", "timestamp"]):
            return "temporal"
        elif any(x in col_lower for x in ["id", "key", "uuid"]):
            return "identifier"
        elif any(x in col_lower for x in ["name", "title", "description"]):
            return "text"
        
        return None
    
    def _generate_insights(self, columns: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate dataset-level insights"""
        total_cols = len(columns)
        
        # Count by type
        numeric_cols = [c for c, p in columns.items() if p.get("type") == "numeric"]
        categorical_cols = [c for c, p in columns.items() if p.get("type") == "categorical"]
        temporal_cols = [c for c, p in columns.items() if p.get("type") == "temporal"]
        
        # Find potential target column (for ML)
        target_candidates = []
        for col, profile in columns.items():
            # Low cardinality categorical = likely target
            if (profile.get("type") == "categorical" and 
                not profile.get("is_high_cardinality") and
                profile.get("unique_count", 0) < 50):
                target_candidates.append(col)
        
        # Find columns with high missingness
        high_missing = [
            c for c, p in columns.items() 
            if p.get("null_percentage", 0) > 50
        ]
        
        return {
            "total_columns": total_cols,
            "numeric_columns": len(numeric_cols),
            "categorical_columns": len(categorical_cols),
            "temporal_columns": len(temporal_cols),
            "target_candidates": target_candidates,
            "high_missing_columns": high_missing,
            "has_temporal": len(temporal_cols) > 0
        }


# Test function
def test_profiler():
    """Test profiler with sample data"""
    # Create sample dataset with 1000 rows
    n_rows = 1000
    
    df = pl.DataFrame({
        "user_id": range(n_rows),
        "age": [25, 30, 35, 40, 150, 28, 32, 29, 31, 33] * (n_rows // 10),  # 150 is outlier
        "income": [50000, 60000, 70000, 80000, 1000000, 55000, 65000, 58000, 62000, 68000] * (n_rows // 10),  # 1M is outlier
        "city": ["NYC", "LA", "SF", "NYC", "LA", "SF", "NYC", "LA", "SF", "NYC"] * (n_rows // 10),
    })
    
    # Add date column separately (easier to control length)
    df = df.with_columns(
        pl.date_range(pl.date(2020, 1, 1), pl.date(2022, 9, 27), "1d", eager=True).head(n_rows).alias("signup_date")
    )
    
    print(f"\n{'='*60}")
    print("Dataset Profiler Test")
    print(f"{'='*60}\n")
    
    profiler = DatasetProfiler()
    profile = profiler.generate_profile(df)
    
    print(f"Dataset Info:")
    print(f"  Rows: {profile['dataset_info']['total_rows']}")
    print(f"  Columns: {profile['dataset_info']['total_columns']}\n")
    
    print(f"Column Profiles:")
    for col, stats in profile["columns"].items():
        print(f"\n  {col}:")
        print(f"    Type: {stats.get('type', 'unknown')}")
        print(f"    Nulls: {stats.get('null_percentage', 0)}%")
        
        if stats.get("type") == "numeric":
            print(f"    Range: [{stats.get('min')}, {stats.get('max')}]")
            print(f"    Outliers: {stats.get('outlier_count', 0)} ({stats.get('outlier_percentage', 0)}%)")
            print(f"    Skewed: {stats.get('is_skewed', False)}")
    
    print(f"\nInsights:")
    print(f"  Target candidates: {profile['insights']['target_candidates']}")
    print(f"  Has temporal data: {profile['insights']['has_temporal']}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    test_profiler()
