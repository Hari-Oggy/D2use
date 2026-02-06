import polars as pl
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class FormatConverter:
    """
    Export datasets to multiple formats.
    
    DESIGN DECISIONS (Senior Engineer Review):
    1. Support common ML formats: JSONL (LLM training), Parquet (analytics), CSV (Excel)
    2. Preserve train/test split information in filenames
    3. Compression for large files (Parquet has built-in compression)
    4. Validation: Check file was written successfully
    """
    
    def __init__(self, output_dir: Path = Path("output")):
        """
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def to_jsonl(
        self,
        df: pl.DataFrame,
        filename: str,
        split_name: Optional[str] = None
    ) -> Path:
        """
        Export to JSONL (JSON Lines) format.
        Popular for LLM training (GPT, Claude, etc.)
        
        Args:
            df: Polars DataFrame
            filename: Base filename (without extension)
            split_name: Optional split identifier (train/test/val)
            
        Returns:
            Path to saved file
        """
        if split_name:
            output_path = self.output_dir / f"{filename}_{split_name}.jsonl"
        else:
            output_path = self.output_dir / f"{filename}.jsonl"
        
        logger.info(f"Exporting to JSONL: {output_path}")
        
        # Write JSONL (one JSON object per line)
        df.write_ndjson(output_path)
        
        # Validate
        if not output_path.exists():
            raise IOError(f"Failed to write JSONL file: {output_path}")
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ JSONL exported: {len(df)} rows, {file_size_mb:.2f}MB")
        
        return output_path
    
    def to_parquet(
        self,
        df: pl.DataFrame,
        filename: str,
        split_name: Optional[str] = None,
        compression: str = "snappy"
    ) -> Path:
        """
        Export to Parquet format.
        Popular for analytics (Spark, Pandas, DuckDB, etc.)
        
        Args:
            df: Polars DataFrame
            filename: Base filename (without extension)
            split_name: Optional split identifier (train/test/val)
            compression: Compression algorithm (snappy, gzip, zstd)
            
        Returns:
            Path to saved file
        """
        if split_name:
            output_path = self.output_dir / f"{filename}_{split_name}.parquet"
        else:
            output_path = self.output_dir / f"{filename}.parquet"
        
        logger.info(f"Exporting to Parquet: {output_path}")
        
        # Write Parquet with compression
        df.write_parquet(output_path, compression=compression)
        
        # Validate
        if not output_path.exists():
            raise IOError(f"Failed to write Parquet file: {output_path}")
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Parquet exported: {len(df)} rows, {file_size_mb:.2f}MB (compressed)")
        
        return output_path
    
    def to_csv(
        self,
        df: pl.DataFrame,
        filename: str,
        split_name: Optional[str] = None
    ) -> Path:
        """
        Export to CSV format.
        Popular for Excel, Google Sheets, general use
        
        Args:
            df: Polars DataFrame
            filename: Base filename (without extension)
            split_name: Optional split identifier (train/test/val)
            
        Returns:
            Path to saved file
        """
        if split_name:
            output_path = self.output_dir / f"{filename}_{split_name}.csv"
        else:
            output_path = self.output_dir / f"{filename}.csv"
        
        logger.info(f"Exporting to CSV: {output_path}")
        
        # Write CSV
        df.write_csv(output_path)
        
        # Validate
        if not output_path.exists():
            raise IOError(f"Failed to write CSV file: {output_path}")
        
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ CSV exported: {len(df)} rows, {file_size_mb:.2f}MB")
        
        return output_path
    
    def export_split(
        self,
        train_df: pl.DataFrame,
        test_df: pl.DataFrame,
        val_df: Optional[pl.DataFrame],
        dataset_name: str,
        formats: list = ["jsonl", "parquet", "csv"]
    ) -> Dict[str, Dict[str, Path]]:
        """
        Export train/test/val splits to multiple formats.
        
        Args:
            train_df: Training set
            test_df: Test set
            val_df: Validation set (optional)
            dataset_name: Base name for files
            formats: List of formats to export (jsonl, parquet, csv)
            
        Returns:
            Dict mapping format -> split -> path
        """
        logger.info(f"Exporting dataset '{dataset_name}' to {len(formats)} formats")
        
        results = {}
        
        for fmt in formats:
            results[fmt] = {}
            
            if fmt == "jsonl":
                results[fmt]["train"] = self.to_jsonl(train_df, dataset_name, "train")
                results[fmt]["test"] = self.to_jsonl(test_df, dataset_name, "test")
                if val_df is not None:
                    results[fmt]["val"] = self.to_jsonl(val_df, dataset_name, "val")
            
            elif fmt == "parquet":
                results[fmt]["train"] = self.to_parquet(train_df, dataset_name, "train")
                results[fmt]["test"] = self.to_parquet(test_df, dataset_name, "test")
                if val_df is not None:
                    results[fmt]["val"] = self.to_parquet(val_df, dataset_name, "val")
            
            elif fmt == "csv":
                results[fmt]["train"] = self.to_csv(train_df, dataset_name, "train")
                results[fmt]["test"] = self.to_csv(test_df, dataset_name, "test")
                if val_df is not None:
                    results[fmt]["val"] = self.to_csv(val_df, dataset_name, "val")
            
            else:
                logger.warning(f"Unknown format: {fmt}")
        
        logger.info(f"✅ Export complete: {len(results)} formats")
        return results


# Test function
def test_format_converter():
    """Test format converter with sample data"""
    # Create sample split
    train_df = pl.DataFrame({
        "feature1": range(100),
        "feature2": ["A", "B"] * 50,
        "label": [0, 1] * 50
    })
    
    test_df = pl.DataFrame({
        "feature1": range(100, 120),
        "feature2": ["A", "B"] * 10,
        "label": [0, 1] * 10
    })
    
    print(f"\n{'='*60}")
    print("Format Converter Test")
    print(f"{'='*60}\n")
    
    converter = FormatConverter(output_dir=Path("output/test"))
    
    # Export to all formats
    results = converter.export_split(
        train_df=train_df,
        test_df=test_df,
        val_df=None,
        dataset_name="sample_dataset",
        formats=["jsonl", "parquet", "csv"]
    )
    
    print(f"\nExported Files:")
    for fmt, splits in results.items():
        print(f"\n  {fmt.upper()}:")
        for split, path in splits.items():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"    {split}: {path.name} ({size_mb:.2f}MB)")
    
    print(f"\n{'='*60}")
    print("✅ Format converter working!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_format_converter()
