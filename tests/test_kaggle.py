"""
Quick test to verify Kaggle API is working
"""
import asyncio
from src.adapters.kaggle import KaggleAdapter

async def test_kaggle():
    print("Testing Kaggle API...")
    adapter = KaggleAdapter()
    
    try:
        results = await adapter.search_datasets("cancer", limit=5)
        print(f"\n✅ Success! Found {len(results)} datasets from Kaggle\n")
        
        for i, dataset in enumerate(results, 1):
            print(f"{i}. {dataset.source_id}")
            print(f"   Downloads: {dataset.file_metadata.get('downloads', 0)}")
            print(f"   Votes: {dataset.file_metadata.get('votes', 0)}")
            print()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kaggle())
