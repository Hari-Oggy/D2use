"""Test Kaggle API directly"""
import asyncio
from src.adapters.kaggle import KaggleAdapter

async def test():
    kaggle = KaggleAdapter()
    
    print("Searching for ecommerce churn datasets...")
    results = await kaggle.search_datasets("ecommerce customer churn", limit=5)
    
    print(f"\nFound {len(results)} datasets:")
    for r in results:
        print(f"  - {r.source_id}")
        print(f"    URL: {r.url}")
        print(f"    Downloadable: {r.is_downloadable}")
    
    # Try the specific one
    target = "ankitverma2010/ecommerce-customer-churn-analysis-and-prediction"
    print(f"\n\nAttempting to download: {target}")
    
    try:
        import kaggle
        kaggle.api.dataset_download_files(target, path="output/kaggle_test", unzip=True)
        print("✅ Downloaded successfully!")
        
        # List files
        from pathlib import Path
        files = list(Path("output/kaggle_test").glob("*"))
        print(f"Files: {files}")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
