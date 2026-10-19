# 10-Minute Demo Video Presentation Script

This script provides an exact 10-minute walkthrough following the required capstone rubric.

---

### Segment 1: On-Camera Introduction (0:00 – 0:30)
- **Visual:** Your face on camera.
- **Script:**
  > "Hi everyone, I am presenting the AI Tech Consultant capstone project. 
  > Over the last two years, software creation costs dropped by 90% from $2,000 to $200. But the real bottleneck isn't writing code—it's everything around it: searching help docs, answering customer emails, and turning messy client meetings into scopes of work.
  > Today, I will demonstrate our AI Tech Consultant: an integrated platform consisting of a Python Knowledge Brain, a TypeScript Inbox Agent, and a Python Multi-Agent Scoping Team, all sharing a single knowledge service."

---

### Segment 2: Task 1 — The Knowledge Brain (0:30 – 3:00)
- **Visual:** Screen share on Tab 1: Knowledge Brain.
- **Step 1: Grounded Answer & Citations:**
  - Type query: *"How do I connect Stripe to my Brilliant Directories website?"*
  - Click **Search & Answer**.
  - Highlight: Grounded answer generated, 98% confidence, 2.1ms latency, clickable source citation link to `How to Connect Stripe Payment Gateway`, and visual screenshot reference pill.
- **Step 2: Genuine Failure & Abstention (The Out-of-Domain Case):**
  - Type query: *"How do I deploy a Kubernetes pod to run an autonomous trading bot?"*
  - Click **Search & Answer**.
  - Highlight: The system **refuses to hallucinate**! Status changes to **Escalated to Human Expert** (Confidence 0.0%).
  - Show the **Human Expert Escalation Queue**: Ticket `ESC-20261019-XXXX` has appeared automatically with the query and reason.
- **Step 3: Human Feedback & Knowledge Evolution:**
  - Click **Resolve as Expert** on a ticket (e.g. Solana payment inquiry).
  - Enter resolution: *"Solana is supported via Developer Webhooks and REST API."*
  - Click **Approve & Index into Memory**.
  - Re-run the question: It now answers immediately with 98% confidence and cites the new expert resolution!
- **Step 4: Polite Daily Sitemap Sync:**
  - Click **Daily Sitemap Sync**: Shows added, updated, and pruned deletions without crashing the server.

---

### Segment 3: Task 2 — The Inbox Agent (3:00 – 5:00)
- **Visual:** Tab 2: Inbox Agent.
- **Step 1: 50-Email Test Bench & Classification:**
  - Show the 50 customer emails covering all 7 categories (How-To, Troubleshooting, Project Requests, Refunds, Complaints, Quotes, Follow-ups).
  - Select `EM-001` (Stripe setup question).
- **Step 2: Task 1 API Integration & Grounded Drafting:**
  - Click **Generate Grounded Draft**.
  - Show that it called Task 1's API to fetch the verified Stripe article, drafted a polite reply in company voice, and cited the documentation URL.
- **Step 3: 20-Clean-Sends Autonomy Rule & Safety Locks:**
  - Point to the **Autonomy Board**.
  - Explain the **20-consecutive-approval rule**: If 20 consecutive drafts are sent without human modification, `how_to` earns autonomous dispatch.
  - Show the **Permanent Safety Locks**: `refund_cancellation` and `complaint` categories display **🔒 High-Risk Locked**, ensuring financial and reputation requests are never sent without human approval.
- **Step 4: Streak Reset on Human Edit:**
  - Edit the suggested reply slightly and click **Save Edit & Send**.
  - Show alert: Character similarity fell below 0.98, so the streak reset to 0!

---

### Segment 4: Task 3 — Meeting to Scope of Work (5:00 – 7:45)
- **Visual:** Tab 3: Meeting to Scope.
- **Step 1: Baseline Meeting A Analysis:**
  - Select `Meeting A (LocalTrades.com)`.
  - Click **Run Agent Team**.
  - Show the staged agent handoffs:
    1. **Transcript Analyst:** Extracted 6 explicit requirements (Radius search, 14-day trial, Stripe Connect, lead routing, brand CSS).
    2. **Product Feasibility Agent:** Queried Task 1 Knowledge Brain API! Classified Stripe and Radius search as **Built-in Configuration ($0 custom code)**, saving the client **$4,000+**!
    3. **Estimation Agent:** 3-point task estimates table showing 21.0 likely hours ($2,100 fixed quote).
    4. **Proposal Agent:** Executive proposal formatted with milestones and assumptions.
- **Step 2: Follow-Up Meeting C & Scope Diff Engine:**
  - Click **Compare Meeting A vs Meeting C (Scope Diff)**.
  - Show the Change Report:
    - **Added:** Emergency 24/7 Service filter (+5.0 hours).
    - **Removed:** Twilio SMS Alerts (-1.5 hours).
    - **Modified:** Delivery timeline compressed from 3 weeks to 10 business days (Rush).
    - **Out-of-Scope Quarantined:** The client's casual request for native iOS/Android apps is **flagged as OUT OF SCOPE** and quarantined into Exclusions with a warning for a separate Phase 2 quote!
- **Step 3: Human Consultant Sign-Off:**
  - Click **Approve Proposal for Client**: Shows senior consultant sign-off stamp.

---

### Segment 5: Evidence, Models & Empirical Comparisons (7:45 – 9:00)
- **Visual:** Slide or document view of `EVALS.md`.
- **Key Metrics to Highlight:**
  - **65 total evaluation cases** tested across Claude 3.5 Sonnet and Claude 3.5 Haiku.
  - **Accuracy:** 100% across both models on test suites.
  - **Cost Comparison:** Haiku 3.5 achieved **73.3% lower cost** ($0.0006 vs $0.0023 per email draft) with sub-3ms execution.
  - **Empirical Decision:** We deploy **Claude 3.5 Haiku** for high-volume email classification and routine drafting, and **Claude 3.5 Sonnet** for multi-document RAG synthesis and multi-agent proposal generation.

---

### Segment 6: Limitations & Next Steps (9:00 – 10:00)
- **Visual:** Camera on face / dashboard summary.
- **Script:**
  > "To be transparent about limitations:
  > First, our sitemap crawler requires polite delays to avoid triggering rate limits on public servers.
  > Second, audio recordings must currently be transcribed to text before feeding into Task 3.
  > For our next iteration, we will integrate native streaming audio transcription for live Zoom calls, and one-click export of developer task estimates directly into Jira and Linear.
  > Thank you!"
