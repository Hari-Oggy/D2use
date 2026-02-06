#!/usr/bin/env python3
"""
ML Dataset Factory CLI v2 - REFACTORED

Now uses OrchestratorV2 (same as API).
This ensures 100% logic parity between CLI and Web API.
"""
import asyncio
import sys
import argparse
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator_v2 import OrchestratorV2

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(
        description="ML Dataset Factory CLI (Powered by OrchestratorV2)"
    )
    parser.add_argument("query", type=str, help="Dataset query")
    parser.add_argument("--max-rows", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=3)
    
    args = parser.parse_args()
    
    # Init Unified Brain
    orchestrator = OrchestratorV2(
        output_dir=Path("output/cli_v2"),
        use_local_llm=True
    )
    
    print(f"\n🚀 ML DATASET FACTORY")
    print(f"Goal: '{args.query}' -> Production ML Data\n")
    
    try:
        # Phase 1: Search
        print("🔍 Searching...")
        candidates = await orchestrator.intelligent_search(
            args.query, 
            limit=args.limit
        )
        
        if not candidates:
            print("❌ No datasets found.")
            return
            
        print(f"✅ Found {len(candidates)} candidates:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c.source_id} (Score: {c.compliance_score:.2f})")
            
        # Select Best
        best = candidates[0]
        print(f"\n🏆 Selected: {best.source_id}")
        
        # Phase 2: Process
        print("\n⚙️  Processing...")
        safe_name = f"{args.query.replace(' ', '_')}_best"
        
        result = await orchestrator.process_dataset(
            candidate_or_id=best,
            dataset_name=safe_name,
            max_rows=args.max_rows
        )
        
        if result:
            print("\n🎉 SUCCESS!")
            print(f"Stats: {result['train_rows']} samples generated")
            print(f"Output: {Path('output/cli_v2') / safe_name}")
        else:
            print("\n❌ FAILED to process dataset.")
            
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
