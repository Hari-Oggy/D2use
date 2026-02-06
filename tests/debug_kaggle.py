"""Debug script to test Kaggle dataset download"""
import asyncio
from src.orchestrator_v2 import OrchestratorV2
from pathlib import Path

async def test():
    orch = OrchestratorV2(output_dir=Path("output/debug"), use_local_llm=False)
    
    print("Testing Kaggle dataset: ankitverma2010/ecommerce-customer-churn-analysis-and-prediction")
    
    try:
        result = await orch.process_dataset(
            candidate_or_id="ankitverma2010/ecommerce-customer-churn-analysis-and-prediction",
            dataset_name="ecommerce_test",
            max_rows=100
        )
        
        if result:
            print(f"\n✅ SUCCESS!")
            print(f"Rows: {result['original_rows']} -> {result['cleaned_rows']}")
        else:
            print("\n❌ FAILED: process_dataset returned None")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    await orch.close()

if __name__ == "__main__":
    asyncio.run(test())
