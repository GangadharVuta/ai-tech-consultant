import sys
from pathlib import Path

# Ensure task root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query as FastQuery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from retrieval.vector_store import HybridVectorStore
from retrieval.qa_pipeline import QAPipeline
from app.escalation_manager import EscalationManager
from ingestion.crawler import PoliteCrawler
from ingestion.sitemap_parser import SitemapParser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Knowledge Brain API: High-performance RAG, incremental sitemap sync, multimodal screenshot understanding, and human-in-the-loop escalation."
)

# Enable CORS for downstream Task 2, Task 3, and UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core singletons
vector_store = HybridVectorStore()
escalation_manager = EscalationManager()
qa_pipeline = QAPipeline(vector_store=vector_store, escalation_manager=escalation_manager)
crawler = PoliteCrawler(vector_store=vector_store)
sitemap_parser = SitemapParser()

# Request & Response Schemas
class QueryRequest(BaseModel):
    query: str = Field(..., description="Customer or consultant question about the product", min_length=3)
    model: Optional[str] = Field(None, description="Claude model override (e.g. claude-3-5-sonnet-20241022 or claude-3-5-haiku-20241022)")
    top_k: int = Field(4, ge=1, le=10, description="Number of evidence chunks to retrieve")
    auto_escalate: bool = Field(True, description="Whether to automatically open an escalation ticket if evidence is lacking")

class SourceCitation(BaseModel):
    title: str
    url: str
    section: Optional[str] = None
    relevance: float

class QueryResponse(BaseModel):
    answer: str
    status: str
    sources: List[SourceCitation]
    images: List[str]
    confidence: float
    needs_human: bool
    escalation_id: Optional[str] = None
    model_used: str
    latency_ms: float
    tokens: Dict[str, int]

class ResolveEscalationRequest(BaseModel):
    expert_name: str = Field(..., min_length=2)
    expert_answer: str = Field(..., min_length=10)
    supporting_notes: str = Field("", description="Internal notes or documentation references")

class CrawlRequest(BaseModel):
    max_pages: Optional[int] = Field(20, description="Max pages to crawl politely in this run")

@app.get("/health", tags=["System"])
async def health_check():
    """Returns system status, index statistics, and available models."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "total_chunks_indexed": len(vector_store.chunks),
        "primary_model": settings.PRIMARY_MODEL,
        "fast_model": settings.FAST_MODEL,
        "has_anthropic_key": bool(settings.ANTHROPIC_API_KEY)
    }

@app.post("/query", response_model=QueryResponse, tags=["Retrieval & QA"])
async def query_knowledge_brain(req: QueryRequest):
    """
    Core RAG question answering endpoint.
    Retrieves evidence from indexed help articles and screenshots,
    returns grounded answer with source citations, or creates an expert escalation task.
    """
    try:
        result = qa_pipeline.generate_answer(
            query=req.query,
            model_name=req.model,
            top_k=req.top_k,
            auto_escalate=req.auto_escalate
        )
        return result
    except Exception as e:
        logger.error(f"Error handling query '{req.query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/run", tags=["Ingestion"])
async def trigger_crawl(req: CrawlRequest, background_tasks: BackgroundTasks):
    """
    Triggers a polite, resumable crawl of Brilliant Directories help articles.
    Runs asynchronously in the background so the caller is not blocked.
    """
    if crawler.is_running:
        return {"status": "already_running", "message": "A crawl job is currently active."}

    background_tasks.add_task(crawler.run_sync, max_pages=req.max_pages)
    return {
        "status": "started",
        "message": f"Polite crawl job started for up to {req.max_pages} pages.",
        "delay_per_request_seconds": settings.CRAWL_DELAY_SECONDS
    }

@app.post("/ingestion/daily-sync", tags=["Ingestion"])
async def trigger_daily_sync():
    """
    Executes incremental daily synchronization:
    1. Compares sitemap XML against local manifest.
    2. Identifies added and updated articles and indexes them.
    3. Identifies removed articles and prunes them from vector store.
    """
    result = crawler.run_sync(max_pages=15)
    return {
        "status": "completed",
        "sync_summary": result
    }

@app.get("/ingestion/status", tags=["Ingestion"])
async def get_ingestion_status():
    """Returns the crawler status, manifest entries count, and vector index size."""
    manifest = sitemap_parser.load_manifest()
    indexed_count = sum(1 for m in manifest.values() if m.get("status") == "indexed")
    failed_count = sum(1 for m in manifest.values() if m.get("status") == "failed")
    
    return {
        "is_crawler_running": crawler.is_running,
        "total_manifest_entries": len(manifest),
        "indexed_articles": indexed_count,
        "failed_articles": failed_count,
        "total_searchable_chunks": len(vector_store.chunks),
        "manifest_path": str(settings.MANIFEST_FILE)
    }

@app.get("/escalations", tags=["Human-in-the-Loop"])
async def list_escalations(status: Optional[str] = FastQuery(None, description="Filter by 'pending' or 'resolved'")):
    """Lists human expert escalation tickets."""
    return escalation_manager.list_escalations(status=status)

@app.post("/escalations/{escalation_id}/resolve", tags=["Human-in-the-Loop"])
async def resolve_escalation(escalation_id: str, req: ResolveEscalationRequest):
    """
    Resolves an escalation ticket.
    The expert's verified solution is automatically indexed into the vector store
    so future queries on this topic are answered immediately.
    """
    resolved_item = escalation_manager.resolve_escalation(
        escalation_id=escalation_id,
        expert_name=req.expert_name,
        expert_answer=req.expert_answer,
        supporting_notes=req.supporting_notes,
        vector_store=vector_store
    )
    if not resolved_item:
        raise HTTPException(status_code=404, detail=f"Escalation ticket {escalation_id} not found.")

    return {
        "status": "resolved_and_indexed",
        "escalation": resolved_item,
        "total_searchable_chunks": len(vector_store.chunks)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
