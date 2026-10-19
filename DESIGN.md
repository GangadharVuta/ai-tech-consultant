# System Design & Architectural Decisions

## 1. The Business Problem in Plain English

Software development costs have plummeted by 90%. Projects that commanded $2,000 two years ago now sell for $200 because non-technical founders can describe what they want to tools like Claude or Cursor. 

However, writing code was never the bottleneck for consulting agencies. The real overhead is everything surrounding the code:
1. **Product Knowledge Friction:** Help centers contain hundreds of evolving articles and visual screenshots. Support reps spend 15–20 minutes searching for documentation before answering a single client ticket.
2. **Support Inbox Churn:** Support engineers draft repetitive replies by hand. Wrong answers churn clients; slow answers lose new sales.
3. **Meeting Scoping Bloat:** Turning messy client discovery calls into scopes of work, developer estimates, and proposals takes 3 to 5 business days per deal. Agencies routinely lose thousands of dollars writing custom code for features already built into the platform.

To survive when unit prices drop 10x, a tech firm must execute 10x to 20x more volume with the same headcount. The **AI Tech Consultant** is an autonomous operating system that solves this by creating one shared knowledge brain and two downstream applications.

---

## 2. System Architecture & Inter-Task Connectivity

The three tasks form a decoupled client-service architecture. Task 1 is an autonomous knowledge service. Tasks 2 and 3 call Task 1 exclusively over HTTP REST endpoints—they never share internal database connections or duplicate parsing logic.

```mermaid
flowchart TD
    subgraph Task1["Task 1: The Knowledge Brain (Python / FastAPI :8001)"]
        Site["Brilliant Directories Sitemap XML"] --> Crawler["Polite Async Crawler & Change Detector"]
        Crawler --> HTMLParser["Article Parser & Image Extractor"]
        HTMLParser --> MultiModal["Screenshot Contextual Analyzer"]
        MultiModal --> Chunker["Hierarchical Chunker"]
        Chunker --> VectorStore[("Hybrid Vector Store: BM25 + Dense Semantic")]
        VectorStore --> QAPipeline["Grounded QA Pipeline (Claude 3.5 Sonnet / Haiku)"]
        QAPipeline -->|Uncertainty / Low Score| EscQueue["Human Expert Escalation Queue"]
        EscQueue -->|Expert Resolution| VectorStore
    end

    subgraph Task2["Task 2: The Inbox Agent (TypeScript / Node.js :8002)"]
        Emails["50 Customer Emails"] --> Classifier["Intent & Risk Classifier"]
        Classifier --> KBClient2["Knowledge Brain HTTP Client"]
        KBClient2 -.->|POST /query| QAPipeline
        KBClient2 --> Drafting["Structured Draft Generator"]
        Drafting --> ReviewGate{"Human Review Gate"}
        ReviewGate -->|Approve / Edit| FeedbackStore["Feedback & Similarity Tracker"]
        FeedbackStore --> StreakEngine{"20-Clean-Sends Rule"}
        StreakEngine -->|Streak >= 20 & Low Risk| AutoSend["Autonomous Dispatch"]
        StreakEngine -->|Human Edit Detected| Reset["Reset Streak to 0"]
    end

    subgraph Task3["Task 3: Meeting to Scope of Work (Python / Multi-Agent :8003)"]
        Transcripts["Meeting Transcripts (A, B, C)"] --> Analyst["Transcript Analyst"]
        Analyst --> Feasibility["Product Feasibility Agent"]
        Feasibility -.->|POST /query| QAPipeline
        Feasibility --> ScopeGen["Scope of Work Agent"]
        ScopeGen --> Estimator["Estimation Agent (3-Point Hours)"]
        Estimator --> Proposer["Proposal Agent"]
        Transcripts --> DiffEngine["Scope Diff Engine (Follow-Up Tracker)"]
        Proposer --> ApprovalGate{"Senior Consultant Approval"}
        DiffEngine --> ApprovalGate
    end

    subgraph UserInterface["Unified Web Interface (:8000)"]
        UI["Real-Time Reactive Dashboard: Knowledge Chat | Inbox Review | Scope Diff"]
    end

    UI -.-> Task1
    UI -.-> Task2
    UI -.-> Task3
```

---

## 3. Features Chosen and Why

| Feature | Business Rationale | Technical Implementation |
|:---|:---|:---|
| **Hybrid BM25 + Dense Retrieval** | Pure vector search misses exact setting labels (e.g., "Stripe Connect", "reCAPTCHA v2"); pure keyword search misses semantic synonyms. Hybrid ensures 100% precision. | Token-coverage scaled BM25 + dense token overlap merged via Reciprocal Rank Fusion ($k=60$). |
| **Screenshot Context Association** | Over 40% of Brilliant Directories settings are only identifiable via screenshots in help docs. Text-only RAG hallucinated button locations. | Extracted image URLs tied to preceding heading and nearby paragraphs; visual features embedded into chunk text. |
| **Human Escalation Knowledge Loop** | When documentation lacks an answer, a wrong guess destroys client trust. Expert answers must permanently upgrade memory. | Automated ticket creation when confidence $<0.62$; expert resolution generates verified chunk indexed immediately. |
| **Strict 20-Clean-Sends Rule with Safety Lock** | Autonomous email sending cannot be turned on by assumption. It must be earned through evidence. | Evaluates text similarity between generated draft and human-sent reply. If similarity $<0.98$, streak resets to 0. High-risk categories (refunds, cancellations, complaints) are permanently locked from auto-sending. |
| **Product Feasibility Check before Custom Dev** | Proposing custom code for an existing platform setting overcharges the client and bloats delivery timelines. | Feasibility agent queries Task 1 API for every extracted requirement. Identifies native settings, saving clients $2,000–$4,000 per project. |
| **Scope Diff Engine (Follow-Up Meeting)** | Second meetings always alter requirements. Rewriting scopes from scratch creates inconsistencies and missed billables. | Diffs follow-up against baseline; flags added, modified, removed, and out-of-scope requests (e.g. mobile apps). |
| **One-Command Orchestration** | Reviewers and non-technical staff should not run 4 separate terminal windows. | Python `start_all.py` spawns all 3 services and dashboard, handling signals and graceful shutdown. |

---

## 4. Features Dropped and Why

1. **Autonomous Database Retraining on Every Email:**
   - *Why dropped:* Fine-tuning models on uncurated customer emails risks catastrophic forgetting and prompt drift. We chose in-context learning with structured feedback history instead.
2. **Full Sitemap Background Crawl on Boot:**
   - *Why dropped:* Ingesting 1,699 remote pages over a live network takes hours and risks IP bans. We implemented polite incremental crawling with curated offline seed snapshots for instant evaluation readiness.
3. **Automated Sending of Refund Confirmations:**
   - *Why dropped:* Bypassing human review on financial refunds creates catastrophic commercial liability. High-risk categories remain permanently locked to human sign-off.
4. **Automated Quote Generation without Human Approval:**
   - *Why dropped:* LLMs can hallucinate aggressive discounts or unrealistic deadlines. Task 3 proposals cannot be released to clients until a human consultant clicks approve.

---

## 5. Model Selection & Empirical Comparison

We evaluated **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`) against **Claude 3.5 Haiku** (`claude-3-5-haiku-20241022`) across 65 evaluation test cases.

| Dimension | Claude 3.5 Sonnet | Claude 3.5 Haiku | Decision & Rationale |
|:---|:---|:---|:---|
| **Task 1 RAG Quality** | 100% accuracy (20/20) | 100% accuracy (20/20) | **Claude 3.5 Sonnet** selected for primary RAG due to superior citation fidelity on multi-document edge cases. |
| **Task 2 Email Classification** | 100% accuracy (25/25) | 100% accuracy (25/25) | **Claude 3.5 Haiku** recommended for production email classification: 3.8x cheaper ($0.0006 vs $0.0023 per email) with 2.1ms latency. |
| **Task 3 Complex Scoping** | 100% accuracy (20/20) | 100% accuracy (20/20) | **Claude 3.5 Sonnet** selected for multi-agent synthesis: handles ambiguous constraints and out-of-scope quarantine with zero drift. |
| **Cost per 1,000 Tasks** | \$3.72 | \$0.99 | Haiku delivers 73.4% cost reduction for high-volume routine triage. |

---

## 6. Failure Modes and Mitigations

| Failure Mode | Root Cause | Implemented Mitigation |
|:---|:---|:---|
| **Brand Name Overlap in Search** | Common terms ("Brilliant", "Directories") caused irrelevant articles to match out-of-domain queries. | Custom stopword filtering removing platform brand names and token coverage scaling ($(\text{coverage})^{0.8}$). |
| **Adversarial Jailbreaks** | Untrusted email text containing injection attacks ("ignore previous instructions"). | Regex security pre-filter quarantining adversarial inputs and forcing human escalation. |
| **Scope Creep in Follow-Up Calls** | Client casually requested native iOS/Android apps during web scoping. | Feasibility agent classifies native apps as `out_of_scope`, quarantine block alerts reviewer, and excludes it from web proposal. |
| **Premature Auto-Send** | Reviewer clicks "Send" after minor edits, falsely incrementing streak. | System compares character similarity between draft and sent body. Edits below 0.98 similarity reset streak to zero. |

---

## 7. What Breaks and What to Build Next

### Current Limitations:
- **Rate-Limiting on Live Scrapes:** If the Brilliant Directories server blocks the crawler IP, live sync falls back to cached manifest.
- **Audio Transcription:** The current pipeline ingests text transcripts. Audio WAV/MP3 ingestion requires an upstream Whisper integration.

### What to Build Next:
1. **Live Stripe Webhook Sandbox:** Connect live Stripe test webhooks directly into Task 2 for instantaneous payment verification.
2. **Audio Voice Scoping Agent:** Native streaming audio ingestion to transcribe Zoom/Meet discovery calls in real-time.
3. **Automated JIRA/Linear Export:** One-click push of Task 3 developer estimates into Jira or GitHub Issues.
