"""
FastAPI REST API for ML Dataset Factory - v2 (Production)

Uses OrchestratorV2 for unified, robust logic.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import asyncio

# Correct import for internal modules when running as -m src.api.main
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator_v2 import OrchestratorV2
from src.schemas import DatasetCandidate
from src.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Dataset Factory API",
    description="Production-grade Dataset Pipeline (v2)",
    version="2.0.0"
)

# Global Orchestrator (The Unified Brain)
# Initialized on startup
orchestrator = None

@app.on_event("startup")
async def startup_event():
    global orchestrator
    orchestrator = OrchestratorV2(
        output_dir=Path("output/api"),
        use_local_llm=settings.USE_LOCAL_LLM  # From config
    )
    logger.info("✅ OrchestratorV2 initialized")

@app.on_event("shutdown")
async def shutdown_event():
    if orchestrator:
        await orchestrator.close()
    logger.info("🛑 OrchestratorV2 closed")

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    expand_query: bool = True

class ProcessRequest(BaseModel):
    dataset_name: str # e.g. "iris" or "google/fcv-seeds"
    max_rows: int = 1000
    export_formats: List[str] = ["jsonl", "parquet", "csv"]
    
class ProcessResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "backend": "OrchestratorV2"}

@app.post("/search")
async def search(req: SearchRequest):
    """
    Intelligent Search (LLM-Expanded + Multi-Source)
    """
    if not orchestrator: raise HTTPException(503, "Initializing...")
    try:
        results = await orchestrator.intelligent_search(
            req.query, 
            req.limit, 
            req.expand_query
        )
        return {
            "query": req.query,
            "count": len(results),
            "results": [c.dict() for c in results]
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process", response_model=ProcessResponse)
async def process(req: ProcessRequest):
    """
    Download -> Clean -> Split -> Export
    Works for HuggingFace AND Direct URLs.
    """
    if not orchestrator: raise HTTPException(503, "Initializing...")
    try:
        # Sanitize name for folder creation
        safe_name = req.dataset_name.replace("/", "_").replace(" ", "_")
        
        result = await orchestrator.process_dataset(
            candidate_or_id=req.dataset_name,
            dataset_name=safe_name,
            max_rows=req.max_rows,
            formats=req.export_formats
        )
        
        if result:
            return ProcessResponse(status="success", data=result)
        else:
            return ProcessResponse(status="failed", error="Download or processing failed")
            
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return ProcessResponse(status="error", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
