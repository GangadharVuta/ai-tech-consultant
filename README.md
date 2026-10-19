# AI Tech Consultant (Capstone Suite)

An enterprise multi-agent consulting platform that unifies product documentation knowledge, autonomous inbox triage, and automated client meeting scoping for SaaS businesses.

Built with **Python (FastAPI)** for knowledge retrieval & multi-agent orchestration, and **TypeScript (Node.js)** for customer inbox workflows.

---

## What It Does

1. **Task 1 — The Knowledge Brain (Python / FastAPI):**
   - Continuously ingests the Brilliant Directories Solution Center help articles and screenshots.
   - Grounded RAG with hybrid BM25 + dense semantic retrieval, source citations, screenshot linking, and human escalation queues that feed resolved expert answers back into memory.
2. **Task 2 — The Inbox Agent (TypeScript / Node.js):**
   - Triages 50+ realistic customer emails across 7 categories.
   - Calls Task 1 API for factual grounding, drafts replies in company voice, and tracks a 20-consecutive-unedited approval streak before granting autonomy (with permanent safety locks on refunds and complaints).
3. **Task 3 — Meeting to Scope of Work (Python / Multi-Agent):**
   - Team of 5 specialized agents converts messy client meeting transcripts into structured Scopes of Work, 3-point task estimates (low/likely/high), and executive proposals.
   - Checks Task 1 API to resolve requirements using built-in product settings before quoting expensive custom code.
   - Computes follow-up scope diffs (Meeting A vs Meeting C) and quarantines out-of-scope requests.

---

## One-Command Quickstart

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm
- *(Optional)* `ANTHROPIC_API_KEY` for live Claude calls (high-fidelity offline fallback included).

### 1. Launch All Services
Run one command from the project root:
```bash
python start_all.py
```
*(Windows users can also double-click `start.bat`)*

This starts:
- **Unified UI Dashboard:** http://127.0.0.1:8000
- **Task 1 Knowledge Brain API:** http://127.0.0.1:8001 (Docs: `/docs`)
- **Task 2 Inbox Agent API:** http://127.0.0.1:8002 (Health: `/health`)
- **Task 3 Meeting-to-Scope API:** http://127.0.0.1:8003 (Docs: `/docs`)

---

## Running the Evaluation Suites (65 Total Test Cases)

To execute the automated benchmarks across models (Claude 3.5 Sonnet vs. Claude 3.5 Haiku):

```bash
# Task 1 Knowledge Brain Evaluations (20 Cases)
cd task1-knowledge-brain && python evaluation/run_evals.py

# Task 2 Inbox Agent Evaluations (25 Cases)
cd ../task2-inbox-agent && npm test

# Task 3 Meeting to Scope Evaluations (20 Cases)
cd ../task3-meeting-to-scope && python evaluation/run_evals.py
```

---

## Repository Structure

```text
ai-tech-consultant/
├── task1-knowledge-brain/    # Python: Crawler, multimodal RAG, citations, escalations
├── task2-inbox-agent/        # TypeScript: Classifier, KB client, 20-streak autonomy
├── task3-meeting-to-scope/   # Python: 5-agent team, feasibility checks, scope diff
├── ui/                       # Modern unified web interface for all 3 tasks
├── start_all.py              # Single command multi-process runner
├── start.bat                 # Windows quick launcher
├── README.md                 # System overview and quickstart
├── DESIGN.md                 # Architecture, trade-offs, model selection
├── EVALS.md                  # 65 test benchmarks, latency, cost & accuracy
└── AI_LOG.md                 # 5 key AI prompts & rejected code analysis
```
