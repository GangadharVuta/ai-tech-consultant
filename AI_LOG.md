# AI Coding Assistant Interaction Log

This document records the 5 most effective engineering prompts used during development, and one specific instance where an AI-generated implementation was rejected with root-cause analysis.

---

## 1. Five Most Useful Engineering Prompts

### Prompt 1: Decoupled Inter-Task Architecture Contract
> *"We need to build Task 1 (Knowledge Brain) as a completely autonomous REST service in Python, and Task 2 (Inbox Agent) in TypeScript. Design a strict HTTP JSON schema contract for `POST /query` that returns grounded answers, citation sources, and associated screenshots, but automatically signals `needs_human: true` whenever confidence falls below 0.62. Ensure Task 2 never duplicates Task 1's vector code."*
- **Why it was effective:** Enforced strict separation of concerns from Day 1, ensuring zero code leakage between Python and TypeScript.

### Prompt 2: Screenshot Contextual Association
> *"Help articles contain screenshots that carry critical settings not written in body paragraphs. When parsing HTML, write an extractor that binds each `<img>` element to its immediate parent section heading and preceding paragraph. Synthesize searchable visual context blocks like `[Visual Screenshot Note: UI setting in Finance > Payment Gateways]` so that BM25 and vector search can retrieve screenshot answers."*
- **Why it was effective:** Solved the multimodal challenge by creating rich, searchable text embeddings linked to source image URLs.

### Prompt 3: Calibrated Token-Coverage BM25 Scoring
> *"In hybrid search, single incidental words like 'bot' in 'trading bot' match 'automated bot submissions' in reCAPTCHA and score 1.0 after normalization. Rewrite the BM25 scorer so that raw BM25 is scaled by substantive query keyword coverage: `(score / max_score) * (coverage ** 0.8)`. If query coverage is below 0.20, disqualify the chunk from high confidence."*
- **Why it was effective:** Directly eliminated false positive retrievals on out-of-domain queries, achieving 100% abstention precision on unanswerable questions.

### Prompt 4: Strict 20-Clean-Sends Streak Tracker
> *"In TypeScript, implement the 20-consecutive-approval rule for email categories. Use Dice token similarity between the generated draft and the final sent body. If similarity is under 0.98 or if the reviewer clicked reject, reset the streak to 0 and record the reset reason. Also add a hardcoded safety lock so that `refund_cancellation` and `complaint` categories can never be marked autonomous regardless of streak."*
- **Why it was effective:** Created a mathematically auditable autonomy policy that prevents premature automation of high-liability customer communications.

### Prompt 5: Staged Scope Diff & Out-of-Scope Quarantine
> *"In Task 3, compare Meeting A with Meeting C. The client casually asked to roll native iOS and Android mobile apps into the same web proposal. Build a scope diff engine that compares requirement IDs and semantics, detects added and modified items, and explicitly quarantines out-of-bounds requests into an Exclusions and Out-of-Scope section with a separate quote warning."*
- **Why it was effective:** Automated a senior consultant's defensive scoping technique, protecting agencies from unpaid scope creep.

---

## 2. One Time the AI's Answer Was Rejected (and Why)

### What the AI Proposed:
During initial implementation of the RAG confidence scorer in `vector_store.py`, the AI suggested normalizing Reciprocal Rank Fusion (RRF) scores by dividing each candidate's score by the top candidate's score:
```python
# AI-generated code (REJECTED):
max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
confidence = round(min(0.98, (rrf_scores[cid] / max_rrf) * 0.75 + raw_scores.get(cid, 0.0) * 0.25), 3)
```

### Why It Was Rejected:
This mathematical logic was flawed:
1. `rrf_scores[cid] / max_rrf` is mathematically **always equal to 1.0** for the top retrieved chunk.
2. Multiplying `1.0 * 0.75` meant that every top result automatically received a baseline confidence score of at least **0.75**, even if the query was completely out-of-domain (e.g., *"How do I deploy a Kubernetes pod to Mars?"*).
3. As a result, the system failed to abstain: it matched an incidental stopword in an unrelated article and confidently returned a fabricated answer with 98% false confidence instead of routing to the human expert queue.

### How We Corrected It:
We rejected the AI's formula and replaced it with a **relevance-gated calibration**:
1. Added a hard relevance threshold: if `raw_score < 0.20`, the chunk is disqualified.
2. Base confidence is derived from true semantic overlap and keyword coverage:
   ```python
   # Corrected implementation:
   if raw_score < 0.20:
       continue
   calibrated_confidence = round(min(0.98, raw_score * 0.80 + (rrf_scores[cid] * 8.0)), 2)
   ```
3. Out-of-domain queries now score `0.00` confidence, immediately triggering the human escalation workflow as required by enterprise safety standards.
