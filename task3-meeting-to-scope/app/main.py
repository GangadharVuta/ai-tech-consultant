import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone
import json
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.transcript_analyst import TranscriptAnalyst
from agents.feasibility_agent import ProductFeasibilityAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from scope_diff.diff_engine import ScopeDiffEngine

app = FastAPI(
    title="AI Tech Consultant - Meeting to Scope of Work",
    version="1.0.0",
    description="Agent team transforming client meeting transcripts into scopes of work, estimates, and proposals."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate Agents
analyst = TranscriptAnalyst()
feasibility_agent = ProductFeasibilityAgent()
scope_agent = ScopeAgent()
estimation_agent = EstimationAgent(hourly_rate_usd=100.0)
proposal_agent = ProposalAgent()
diff_engine = ScopeDiffEngine()

TRANSCRIPTS_DIR = Path(__file__).resolve().parent.parent / "transcripts"

# In-memory session store of generated projects
projects_store: Dict[str, Dict] = {}

class AnalyzeRequest(BaseModel):
    transcript_name: Optional[str] = Field("meeting_a.txt", description="Name of transcript file")
    transcript_text: Optional[str] = Field(None, description="Raw transcript text override")
    hourly_rate: Optional[float] = Field(100.0, description="Hourly consulting rate in USD")

class ApproveRequest(BaseModel):
    project_id: str
    reviewer_name: str
    approval_notes: Optional[str] = "Approved after senior consultant verification"

class DiffRequest(BaseModel):
    baseline_transcript: str = "meeting_a.txt"
    followup_transcript: str = "meeting_c.txt"

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "service": "AI Tech Consultant - Meeting to Scope",
        "status": "healthy",
        "version": "1.0.0",
        "agents": [
            "TranscriptAnalyst",
            "ProductFeasibilityAgent",
            "ScopeAgent",
            "EstimationAgent",
            "ProposalAgent",
            "ScopeDiffEngine"
        ],
        "transcripts_available": [f.name for f in TRANSCRIPTS_DIR.glob("*.txt")]
    }

@app.get("/transcripts", tags=["Transcripts"])
async def list_transcripts():
    results = []
    for f in sorted(TRANSCRIPTS_DIR.glob("*.txt")):
        content = f.read_text(encoding="utf-8")
        results.append({
            "filename": f.name,
            "size_chars": len(content),
            "preview": content[:180].replace("\n", " ") + "..."
        })
    return {"transcripts": results}

@app.get("/transcripts/{name}", tags=["Transcripts"])
async def get_transcript_content(name: str):
    file_path = TRANSCRIPTS_DIR / name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Transcript {name} not found")
    return {
        "filename": name,
        "content": file_path.read_text(encoding="utf-8")
    }

@app.post("/analyze", tags=["Pipeline"])
async def analyze_transcript(req: AnalyzeRequest):
    """
    Executes the multi-agent team pipeline:
    1. TranscriptAnalyst extracts requirements.
    2. ProductFeasibilityAgent queries Task 1 Knowledge Brain API.
    3. ScopeAgent structures deliverables & exclusions.
    4. EstimationAgent calculates 3-point task estimates.
    5. ProposalAgent writes the executive proposal.
    """
    raw_text = req.transcript_text
    if not raw_text and req.transcript_name:
        f_path = TRANSCRIPTS_DIR / req.transcript_name
        if f_path.exists():
            raw_text = f_path.read_text(encoding="utf-8")

    if not raw_text:
        raise HTTPException(status_code=400, detail="No transcript text provided or file not found")

    # 1. Transcript Analyst
    analysis = analyst.analyze(raw_text)

    # 2. Product Feasibility (Calls Task 1 Knowledge Brain API!)
    feasibility_results = [
        feasibility_agent.check_feasibility(req_dict)
        for req_dict in analysis["requirements"]
    ]

    # 3. Scope Agent
    scope = scope_agent.generate_scope(analysis, feasibility_results)

    # 4. Estimation Agent
    if req.hourly_rate:
        estimation_agent.hourly_rate_usd = req.hourly_rate
    estimates = estimation_agent.estimate_scope(scope)

    # 5. Proposal Agent
    proposal = proposal_agent.generate_proposal(scope, estimates)

    project_id = f"PROJ-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{req.transcript_name.replace('.txt', '')}"
    full_project = {
        "project_id": project_id,
        "source_transcript": req.transcript_name,
        "analysis": analysis,
        "feasibility": feasibility_results,
        "scope": scope,
        "estimates": estimates,
        "proposal": proposal,
        "human_approval": {
            "is_approved": False,
            "approved_by": None,
            "approved_at": None,
            "notes": None
        }
    }

    projects_store[project_id] = full_project
    return full_project

@app.post("/diff", tags=["Scope Diff"])
async def compare_meetings(req: DiffRequest):
    """
    Compares baseline meeting (e.g. Meeting A) against follow-up meeting (Meeting C).
    Detects added, modified, removed, and out-of-scope items.
    """
    base_file = TRANSCRIPTS_DIR / req.baseline_transcript
    follow_file = TRANSCRIPTS_DIR / req.followup_transcript

    if not base_file.exists() or not follow_file.exists():
        raise HTTPException(status_code=404, detail="One or both transcript files not found")

    base_analysis = analyst.analyze(base_file.read_text(encoding="utf-8"))
    follow_analysis = analyst.analyze(follow_file.read_text(encoding="utf-8"))

    diff_result = diff_engine.compute_diff(base_analysis, follow_analysis)
    return diff_result

@app.post("/approve", tags=["Human-in-the-Loop"])
async def approve_proposal(req: ApproveRequest):
    """
    Enforces mandatory human consultant approval before proposal can be released to client.
    """
    project = projects_store.get(req.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {req.project_id} not found in active session")

    now_iso = datetime.now(timezone.utc).isoformat()
    project["human_approval"]["is_approved"] = True
    project["human_approval"]["approved_by"] = req.reviewer_name
    project["human_approval"]["approved_at"] = now_iso
    project["human_approval"]["notes"] = req.approval_notes
    project["proposal"]["status"] = "client_ready_approved"
    project["proposal"]["approved_by"] = req.reviewer_name
    project["proposal"]["approved_at"] = now_iso

    return {
        "status": "proposal_approved",
        "project_id": req.project_id,
        "approved_by": req.reviewer_name,
        "approved_at": now_iso
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8003, reload=False)
