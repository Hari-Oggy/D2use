"""Quick test of Phase 3 and Phase 5 fixes"""
import asyncio
import polars as pl
from src.scraper.circuit_breaker import CircuitBreaker
from src.export.split_strategy import DataSplitter

async def main():
    print("\n" + "="*60)
    print("TESTING PHASE 3 & 5 FIXES")
    print("="*60)
    
    # Phase 3: Circuit Breaker
    print("\n[Phase 3] Circuit Breaker Test:")
    breaker = CircuitBreaker(failure_threshold=0.5, window_size=5)
    
    # Record 5 consecutive failures
    for i in range(5):
        breaker.record_failure("example.com")
    
    # Check if it's blocking
    can_request =breaker.can_request("example.com")
    state = breaker.get_state("example.com")
    
    print(f"  After 5 failures:")
    print(f"    State: {state}")
    print(f"    Can request: {can_request}")
    print(f"    Expected: OPEN, False")
    
    if state.value == "open" and not can_request:
        print("  ✅ PASS")
    else:
        print("  ❌ FAIL")
    
    # Phase 5: Stratified Split
    print("\n[Phase 5] Stratified Split Test:")
    
    df = pl.DataFrame({
        "feature1": list(range(100)),
        "feature2": list(range(100, 200)),
        "target": [0, 1] * 50
    })
    
    splitter = DataSplitter()
    
    try:
        # Test with STRING (the bug scenario)
        train, test, val = splitter.split(df, strategy="STRATIFIED", target_column="target")
        print(f"  Split successful: {len(train)} train, {len(test)} test")
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
