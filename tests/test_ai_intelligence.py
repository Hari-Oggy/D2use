"""
Test AI Decision Maker with LM Studio
"""
import asyncio
from src.analysis.ai_decision import AIDecisionMaker
from src.analysis.profiler import DatasetProfiler
import polars as pl

async def test_ai():
    print("\n" + "="*60)
    print("AI INTELLIGENCE TEST")
    print("="*60)
    
    # Create messy data
    df = pl.DataFrame({
        "id": list(range(100)),  # Useless column
        "age": [25, 30, None, 1000, 35] * 20,  # Has nulls and outlier
        "salary": [50000, 60000, None, 75000, 80000] * 20,
        "category": ["A", "B", "C"] * 33 + ["A"]
    })
    
    # Profile it
    profiler = DatasetProfiler()
    profile = profiler.generate_profile(df)
    
    # Test AI
    ai = AIDecisionMaker(use_local_llm=True)
    
    print("\n🤖 Asking AI to analyze this messy dataset...")
    print("   (This will fail if LM Studio server is not running)\n")
    
    try:
        recipe = await ai.get_cleaning_recipe(profile)
        
        print("✅ AI IS WORKING!")
        print(f"\nAI Recipe:")
        print(f"  - Drop columns: {recipe.drop_columns}")
        print(f"  - Impute strategy: {recipe.impute_strategy}")
        print(f"  - Outlier strategy: {recipe.outlier_strategy}")
        print(f"  - Target column: {recipe.target_column}")
        print(f"  - Confidence: {recipe.confidence:.2f}")
        print(f"\n💡 AI Reasoning:")
        print(f"  {recipe.reasoning}")
        
    except Exception as e:
        print(f"❌ AI FAILED: {e}")
        print("\n📌 Make sure:")
        print("   1. LM Studio server is RUNNING (click Start Server)")
        print("   2. Model is loaded (qwen2.5-7b-instruct)")
        print("   3. Server is on http://localhost:1234")
    
    await ai.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_ai())
