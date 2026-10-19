// API Resolution: Automatically uses direct localhost ports when running start_all.py locally on port 8000,
// and routes through production reverse proxy (/api/task1, /api/task2, /api/task3) on live servers.
const isLocalCustomPorts = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.port === "8000";

const TASK1_API = window.ENV_TASK1_API || (isLocalCustomPorts ? "http://127.0.0.1:8001" : `${window.location.origin}/api/task1`);
const TASK2_API = window.ENV_TASK2_API || (isLocalCustomPorts ? "http://127.0.0.1:8002" : `${window.location.origin}/api/task2`);
const TASK3_API = window.ENV_TASK3_API || (isLocalCustomPorts ? "http://127.0.0.1:8003" : `${window.location.origin}/api/task3`);

// State
let allEmails = [];
let selectedEmail = null;
let currentDraft = null;
let currentProject = null;
let activeEscalationId = null;

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  checkHealthBadges();
  setInterval(checkHealthBadges, 8000);

  // Tab 1 Events
  document.getElementById("btn-kb-ask").addEventListener("click", handleKbAsk);
  document.getElementById("btn-refresh-escalations").addEventListener("click", loadEscalations);
  document.getElementById("btn-sync-sitemap").addEventListener("click", triggerSitemapSync);
  document.getElementById("btn-submit-resolution").addEventListener("click", submitResolution);
  document.querySelectorAll(".btn-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("kb-query").value = btn.dataset.query;
      handleKbAsk();
    });
  });

  // Tab 2 Events
  document.getElementById("inbox-filter-category").addEventListener("change", renderEmailsList);
  document.getElementById("btn-generate-draft").addEventListener("click", handleGenerateDraft);
  document.getElementById("btn-approve-send").addEventListener("click", () => submitEmailReview("approve"));
  document.getElementById("btn-edit-send").addEventListener("click", () => submitEmailReview("edit_and_send"));
  document.getElementById("btn-reject-draft").addEventListener("click", () => submitEmailReview("reject"));

  // Tab 3 Events
  document.getElementById("meeting-select").addEventListener("change", loadSelectedTranscript);
  document.getElementById("btn-analyze-meeting").addEventListener("click", handleAnalyzeMeeting);
  document.getElementById("btn-run-diff").addEventListener("click", handleRunDiff);
  document.getElementById("btn-approve-proposal").addEventListener("click", handleApproveProposal);

  // Initial Data Loads
  loadEscalations();
  loadEmails();
  loadAutonomyBoard();
  loadSelectedTranscript();
});

// ==================== TAB NAVIGATION ====================
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });
}

// ==================== SERVICE HEALTH MONITOR ====================
async function checkHealthBadges() {
  const checkService = async (url, badgeId) => {
    const badge = document.getElementById(badgeId);
    try {
      const resp = await fetch(`${url}/health`, { signal: AbortSignal.timeout(2000) });
      if (resp.ok) {
        badge.classList.add("active");
      } else {
        badge.classList.remove("active");
      }
    } catch {
      badge.classList.remove("active");
    }
  };

  checkService(TASK1_API, "badge-task1");
  checkService(TASK2_API, "badge-task2");
  checkService(TASK3_API, "badge-task3");
}

// ==================== TAB 1: KNOWLEDGE BRAIN ====================
async function handleKbAsk() {
  const query = document.getElementById("kb-query").value.trim();
  const model = document.getElementById("kb-model").value;
  if (!query) return;

  const btn = document.getElementById("btn-kb-ask");
  btn.textContent = "Searching...";
  btn.disabled = true;

  try {
    const resp = await fetch(`${TASK1_API}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, model, top_k: 4, auto_escalate: true })
    });
    const data = await resp.json();
    renderKbResult(data);
    loadEscalations();
  } catch (err) {
    alert("Knowledge Brain API is offline or unreachable on port 8001. Please run start_all.py.");
  } finally {
    btn.textContent = "Search & Answer";
    btn.disabled = false;
  }
}

function renderKbResult(data) {
  const box = document.getElementById("kb-result-box");
  box.classList.remove("hidden");

  const statusBadge = document.getElementById("kb-status-badge");
  if (data.status === "answered") {
    statusBadge.textContent = "Grounded Answer";
    statusBadge.className = "badge-success";
  } else {
    statusBadge.textContent = "Escalated to Human Expert";
    statusBadge.className = "badge-warning";
  }

  document.getElementById("kb-metrics").textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}% | Latency: ${data.latency_ms}ms | Model: ${data.model_used.includes("haiku") ? "Haiku 3.5" : "Sonnet 3.5"}`;
  document.getElementById("kb-answer-text").innerHTML = formatMarkdown(data.answer);

  // Sources
  const sourcesContainer = document.getElementById("kb-sources-container");
  const sourcesUl = document.getElementById("kb-sources-ul");
  sourcesUl.innerHTML = "";
  if (data.sources && data.sources.length > 0) {
    sourcesContainer.classList.remove("hidden");
    data.sources.forEach(s => {
      const li = document.createElement("li");
      li.innerHTML = `<a href="${s.url}" target="_blank" rel="noopener"><strong>${s.title}</strong></a> (Relevance: ${(s.relevance * 100).toFixed(0)}%)`;
      sourcesUl.appendChild(li);
    });
  } else {
    sourcesContainer.classList.add("hidden");
  }

  // Screenshots
  const imagesContainer = document.getElementById("kb-images-container");
  const imagesDiv = document.getElementById("kb-images-div");
  imagesDiv.innerHTML = "";
  if (data.images && data.images.length > 0) {
    imagesContainer.classList.remove("hidden");
    data.images.forEach(imgUrl => {
      const a = document.createElement("a");
      a.className = "img-pill";
      a.href = imgUrl;
      a.target = "_blank";
      a.textContent = "🖼️ View UI Screenshot";
      imagesDiv.appendChild(a);
    });
  } else {
    imagesContainer.classList.add("hidden");
  }
}

async function loadEscalations() {
  try {
    const resp = await fetch(`${TASK1_API}/escalations`);
    if (!resp.ok) return;
    const items = await resp.json();
    renderEscalations(items);
  } catch (e) {
    console.warn("Could not load escalations:", e);
  }
}

function renderEscalations(items) {
  const container = document.getElementById("escalations-list");
  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.innerHTML = `<div class="empty-state">No pending escalations. All queries grounded!</div>`;
    return;
  }

  items.forEach(item => {
    const el = document.createElement("div");
    el.className = `esc-item ${item.status}`;
    el.innerHTML = `
      <div class="esc-item-top">
        <span><strong>${item.id}</strong> (${item.status.toUpperCase()})</span>
        <span>${new Date(item.created_at).toLocaleTimeString()}</span>
      </div>
      <div class="esc-item-q">${escapeHtml(item.question)}</div>
      <div style="font-size: 0.78rem; color: #64748b;">Reason: ${escapeHtml(item.reason)}</div>
      ${item.status === 'pending' ? `<button class="btn btn-sm btn-primary" style="margin-top: 8px;" onclick="openExpertModal('${item.id}', '${escapeJsStr(item.question)}')">Resolve as Expert</button>` : `<div style="font-size: 0.78rem; color: #16a34a; margin-top: 4px;">Resolved by ${escapeHtml(item.expert_name)} & indexed into Knowledge Brain memory.</div>`}
    `;
    container.appendChild(el);
  });
}

window.openExpertModal = function(id, question) {
  activeEscalationId = id;
  document.getElementById("modal-ticket-id").textContent = id;
  document.getElementById("modal-ticket-q").textContent = question;
  document.getElementById("expert-modal").classList.remove("hidden");
};

async function submitResolution() {
  if (!activeEscalationId) return;
  const expertName = document.getElementById("expert-name").value.trim();
  const solution = document.getElementById("expert-solution").value.trim();

  if (!solution) {
    alert("Please enter a verified resolution.");
    return;
  }

  try {
    const resp = await fetch(`${TASK1_API}/escalations/${activeEscalationId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        expert_name: expertName,
        expert_answer: solution,
        supporting_notes: "Resolved via Human-in-the-Loop consultant dashboard."
      })
    });
    if (resp.ok) {
      alert(`Ticket ${activeEscalationId} resolved and indexed into Knowledge Brain memory!`);
      document.getElementById("expert-modal").classList.add("hidden");
      document.getElementById("expert-solution").value = "";
      loadEscalations();
    }
  } catch (err) {
    alert("Failed to submit resolution: " + err.message);
  }
}

async function triggerSitemapSync() {
  const btn = document.getElementById("btn-sync-sitemap");
  btn.textContent = "Syncing...";
  btn.disabled = true;
  try {
    const resp = await fetch(`${TASK1_API}/ingestion/daily-sync`, { method: "POST" });
    const data = await resp.json();
    alert(`Incremental Daily Sync Completed!\nTotal in sitemap: ${data.sync_summary.total_in_sitemap}\nAdded: ${data.sync_summary.added_found}\nUpdated: ${data.sync_summary.updated_found}\nPruned Deletions: ${data.sync_summary.removed_pruned}`);
  } catch (err) {
    alert("Failed to run sitemap sync: " + err.message);
  } finally {
    btn.textContent = "Daily Sitemap Sync";
    btn.disabled = false;
  }
}

// ==================== TAB 2: INBOX AGENT ====================
async function loadEmails() {
  try {
    const resp = await fetch(`${TASK2_API}/emails`);
    if (!resp.ok) return;
    const data = await resp.json();
    allEmails = data.emails || [];
    renderEmailsList();
  } catch (e) {
    console.warn("Could not load emails:", e);
  }
}

function renderEmailsList() {
  const container = document.getElementById("emails-list-container");
  container.innerHTML = "";

  const filter = document.getElementById("inbox-filter-category").value;
  const filtered = filter ? allEmails.filter(e => e.expected_category === filter) : allEmails;

  if (filtered.length === 0) {
    container.innerHTML = `<div class="empty-state">No customer emails found.</div>`;
    return;
  }

  filtered.forEach(email => {
    const card = document.createElement("div");
    card.className = `email-card ${selectedEmail && selectedEmail.id === email.id ? "selected" : ""}`;
    card.innerHTML = `
      <div class="email-card-top">
        <span><strong>${email.id}</strong> | ${email.expected_category.toUpperCase()}</span>
        <span class="badge-tag ${email.risk_level === 'high' ? 'alert' : ''}">${email.risk_level.toUpperCase()}</span>
      </div>
      <div class="email-card-sub">${escapeHtml(email.subject)}</div>
      <div class="email-card-body-preview">${escapeHtml(email.body)}</div>
    `;
    card.addEventListener("click", () => selectEmail(email));
    container.appendChild(card);
  });
}

function selectEmail(email) {
  selectedEmail = email;
  renderEmailsList();

  document.getElementById("draft-from").textContent = email.sender;
  document.getElementById("draft-subject").textContent = email.subject;
  document.getElementById("draft-original-body").textContent = email.body;
  document.getElementById("btn-generate-draft").disabled = false;
  document.getElementById("draft-output-container").classList.add("hidden");

  updateStreakDisplay(email.expected_category);
}

async function handleGenerateDraft() {
  if (!selectedEmail) return;
  const btn = document.getElementById("btn-generate-draft");
  btn.textContent = "Calling Knowledge Brain & Drafting...";
  btn.disabled = true;

  try {
    const resp = await fetch(`${TASK2_API}/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_id: selectedEmail.id })
    });
    currentDraft = await resp.json();
    renderDraftOutput(currentDraft);
  } catch (err) {
    alert("Inbox Agent API error: " + err.message);
  } finally {
    btn.textContent = "Generate Grounded Draft";
    btn.disabled = false;
  }
}

function renderDraftOutput(draft) {
  const container = document.getElementById("draft-output-container");
  container.classList.remove("hidden");

  document.getElementById("draft-cat-pill").textContent = `Category: ${draft.category.toUpperCase()}`;
  document.getElementById("draft-risk-pill").textContent = `Risk: ${draft.risk_level.toUpperCase()}`;
  document.getElementById("draft-risk-pill").className = draft.risk_level === "high" ? "badge-danger" : draft.risk_level === "medium" ? "badge-warning" : "badge-success";

  document.getElementById("draft-meta-metrics").textContent = `Latency: ${draft.latency_ms}ms | Confidence: ${(draft.confidence * 100).toFixed(0)}%`;
  document.getElementById("draft-text-editor").value = draft.suggested_reply;

  const autonomyBadge = document.getElementById("draft-autonomy-badge");
  if (draft.auto_send_eligible) {
    autonomyBadge.textContent = "⚡ Auto-Send Eligible (20 Streak Reached)";
    autonomyBadge.className = "badge-tag";
  } else {
    autonomyBadge.textContent = "Human Review Mandatory";
    autonomyBadge.className = "badge-tag alert";
  }
}

async function submitEmailReview(action) {
  if (!selectedEmail || !currentDraft) return;
  const finalReply = document.getElementById("draft-text-editor").value;

  try {
    const resp = await fetch(`${TASK2_API}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email_id: selectedEmail.id,
        draft_id: currentDraft.id,
        action,
        final_reply: finalReply,
        editor_name: "Senior Support Reviewer"
      })
    });
    const result = await resp.json();
    alert(`Review recorded: ${action.toUpperCase()}\nText Similarity: ${(result.similarity * 100).toFixed(1)}%\nCategory streak: ${result.autonomy_status.consecutive_clean_sends}/20\nAuto-send eligible: ${result.autonomy_status.is_auto_send_eligible}`);
    loadAutonomyBoard();
  } catch (err) {
    alert("Review submission error: " + err.message);
  }
}

async function loadAutonomyBoard() {
  try {
    const resp = await fetch(`${TASK2_API}/autonomy`);
    if (!resp.ok) return;
    const statuses = await resp.json();
    const grid = document.getElementById("autonomy-cards-grid");
    grid.innerHTML = "";

    for (const [cat, info] of Object.entries(statuses)) {
      const card = document.createElement("div");
      card.className = "autonomy-card";
      card.innerHTML = `
        <div class="cat-title">${cat.replace('_', ' ').toUpperCase()}</div>
        <div>Streak: <strong>${info.consecutive_clean_sends} / 20</strong></div>
        <div style="font-size: 0.7rem; color: ${info.is_auto_send_eligible ? '#16a34a' : info.high_risk_locked ? '#dc2626' : '#64748b'}; font-weight: 600;">
          ${info.high_risk_locked ? "🔒 High-Risk Locked" : info.is_auto_send_eligible ? "⚡ Autonomous" : "Manual Review"}
        </div>
      `;
      grid.appendChild(card);
    }
  } catch (e) {
    console.warn("Could not load autonomy statuses:", e);
  }
}

function updateStreakDisplay(category) {
  fetch(`${TASK2_API}/autonomy`)
    .then(r => r.json())
    .then(data => {
      const info = data[category];
      if (info) {
        document.getElementById("mini-streak-display").textContent = `Streak: ${info.consecutive_clean_sends} / 20 ${info.is_auto_send_eligible ? '(Auto-Send)' : ''}`;
      }
    }).catch(() => {});
}

// ==================== TAB 3: MEETING TO SCOPE ====================
async function loadSelectedTranscript() {
  const filename = document.getElementById("meeting-select").value;
  try {
    const resp = await fetch(`${TASK3_API}/transcripts/${filename}`);
    if (resp.ok) {
      const data = await resp.json();
      document.getElementById("meeting-transcript-text").value = data.content;
    }
  } catch (e) {
    console.warn("Could not load transcript:", e);
  }
}

async function handleAnalyzeMeeting() {
  const filename = document.getElementById("meeting-select").value;
  const btn = document.getElementById("btn-analyze-meeting");
  btn.textContent = "Agent Team Analyzing...";
  btn.disabled = true;

  try {
    const resp = await fetch(`${TASK3_API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript_name: filename, hourly_rate: 100.0 })
    });
    currentProject = await resp.json();
    renderMeetingProject(currentProject);
  } catch (err) {
    alert("Meeting to Scope API error: " + err.message);
  } finally {
    btn.textContent = "Run Agent Team";
    btn.disabled = false;
  }
}

function renderMeetingProject(project) {
  // 1. Feasibility section
  document.getElementById("feasibility-section").classList.remove("hidden");
  const badgesContainer = document.getElementById("feasibility-badges-container");
  badgesContainer.innerHTML = "";

  project.feasibility.forEach(f => {
    const pill = document.createElement("div");
    pill.className = `feasibility-pill ${f.feasibility_category}`;
    pill.innerHTML = `
      <div><strong>${escapeHtml(f.title)}</strong> (${f.feasibility_category.replace(/_/g, ' ').toUpperCase()})</div>
      <div style="font-size: 0.75rem; color: #475569;">${escapeHtml(f.technical_rationale)}</div>
      <div style="font-size: 0.75rem; color: #16a34a; font-weight: 600;">Estimated Savings: ${f.estimated_client_savings}</div>
    `;
    badgesContainer.appendChild(pill);
  });

  // 2. Estimates section
  document.getElementById("estimates-section").classList.remove("hidden");
  const tbody = document.getElementById("estimates-tbody");
  tbody.innerHTML = "";

  project.estimates.tasks.forEach(t => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(t.task_name)}</strong><br/><span style="font-size: 0.75rem; color: #64748b;">${escapeHtml(t.rationale)}</span></td>
      <td>${t.low_hours}h</td>
      <td><strong>${t.likely_hours}h</strong></td>
      <td>${t.high_hours}h</td>
      <td>${escapeHtml(t.complexity)}</td>
    `;
    tbody.appendChild(tr);
  });

  const totals = project.estimates.totals;
  const inv = project.estimates.estimated_investment_usd;
  document.getElementById("estimates-totals-bar").innerHTML = `
    Total Likely Effort: <strong>${totals.likely_hours} Hours</strong> (Low: ${totals.low_hours}h | High: ${totals.high_hours}h) &nbsp;|&nbsp; 
    Recommended Fixed Investment: <span style="color: #16a34a;">$${inv.recommended_fixed_quote.toLocaleString()} USD</span>
  `;

  // 3. Proposal section
  document.getElementById("proposal-section").classList.remove("hidden");
  document.getElementById("proposal-preview-text").innerHTML = formatMarkdown(project.proposal.markdown_proposal);

  const approvalBadge = document.getElementById("proposal-approval-badge");
  if (project.human_approval && project.human_approval.is_approved) {
    approvalBadge.textContent = `Approved by ${project.human_approval.approved_by}`;
    approvalBadge.className = "badge-tag";
  } else {
    approvalBadge.textContent = "Awaiting Senior Sign-Off";
    approvalBadge.className = "badge-tag alert";
  }
}

async function handleRunDiff() {
  const btn = document.getElementById("btn-run-diff");
  btn.textContent = "Computing Diff...";
  btn.disabled = true;

  try {
    const resp = await fetch(`${TASK3_API}/diff`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        baseline_transcript: "meeting_a.txt",
        followup_transcript: "meeting_c.txt"
      })
    });
    const diff = await resp.json();
    document.getElementById("diff-section").classList.remove("hidden");
    document.getElementById("diff-preview-text").innerHTML = formatMarkdown(diff.change_report_markdown);
  } catch (err) {
    alert("Scope Diff error: " + err.message);
  } finally {
    btn.textContent = "Compare Meeting A vs Meeting C (Scope Diff)";
    btn.disabled = false;
  }
}

async function handleApproveProposal() {
  if (!currentProject) {
    alert("Please run analysis on a meeting first.");
    return;
  }
  const reviewer = document.getElementById("reviewer-name-input").value.trim();
  try {
    const resp = await fetch(`${TASK3_API}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: currentProject.project_id,
        reviewer_name: reviewer
      })
    });
    if (resp.ok) {
      alert(`Proposal Approved by ${reviewer}! Ready for client delivery.`);
      const approvalBadge = document.getElementById("proposal-approval-badge");
      approvalBadge.textContent = `Approved by ${reviewer}`;
      approvalBadge.className = "badge-tag";
    }
  } catch (err) {
    alert("Approval error: " + err.message);
  }
}

// Utility Helpers
function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeJsStr(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, " ");
}

function formatMarkdown(md) {
  if (!md) return "";
  let html = escapeHtml(md);
  // Markdown links: [title](url)
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // Bold: **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Headers
  html = html.replace(/^### (.*?)$/gm, '<h4 style="margin: 8px 0;">$1</h4>');
  html = html.replace(/^## (.*?)$/gm, '<h3 style="margin: 12px 0 6px 0;">$1</h3>');
  html = html.replace(/^# (.*?)$/gm, '<h2 style="margin: 16px 0 8px 0;">$1</h2>');
  // Bullet lists
  html = html.replace(/^- (.*?)$/gm, '• $1<br/>');
  return html;
}
