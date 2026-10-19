import express, { Request, Response } from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { CustomerEmail, EmailDraft, ReviewAction } from './email/types';
import { DraftingEngine } from './drafting/draftingEngine';
import { AutonomyManager } from './feedback/autonomyManager';
import { KnowledgeBrainClient } from './knowledge-client/knowledgeClient';

dotenv.config();

const app = express();
const PORT = process.env.TASK2_PORT ? parseInt(process.env.TASK2_PORT) : 8002;

app.use(cors());
app.use(express.json());

const kbClient = new KnowledgeBrainClient();
const autonomyManager = new AutonomyManager();
const draftingEngine = new DraftingEngine(kbClient, autonomyManager);

// Load emails
const emailsFilePath = path.resolve(__dirname, '../data/emails.json');
let emails: CustomerEmail[] = [];
if (fs.existsSync(emailsFilePath)) {
  try {
    emails = JSON.parse(fs.readFileSync(emailsFilePath, 'utf-8'));
  } catch (err) {
    console.error('Failed to load emails:', err);
  }
}

// In-memory cache of generated drafts
const draftsCache = new Map<string, EmailDraft>();

// Endpoints
app.get('/health', async (req: Request, res: Response) => {
  const kbHealth = await kbClient.checkHealth();
  res.json({
    service: 'AI Tech Consultant - Inbox Agent',
    status: 'healthy',
    version: '1.0.0',
    total_emails_loaded: emails.length,
    knowledge_brain_connected: kbHealth.healthy,
    prompt_version: draftingEngine.promptVersion
  });
});

app.get('/emails', (req: Request, res: Response) => {
  const categoryFilter = req.query.category as string;
  let result = emails;
  if (categoryFilter) {
    result = emails.filter((e) => e.expected_category === categoryFilter);
  }
  res.json({
    total: result.length,
    emails: result
  });
});

app.get('/emails/:id', (req: Request, res: Response) => {
  const email = emails.find((e) => e.id === req.params.id);
  if (!email) {
    return res.status(404).json({ error: `Email ${req.params.id} not found.` });
  }
  const draft = draftsCache.get(email.id) || null;
  res.json({ email, existing_draft: draft });
});

app.post('/draft', async (req: Request, res: Response) => {
  const { email_id, email_data, model } = req.body;
  let targetEmail: CustomerEmail | undefined;

  if (email_id) {
    targetEmail = emails.find((e) => e.id === email_id);
  } else if (email_data) {
    targetEmail = email_data;
  }

  if (!targetEmail) {
    return res.status(400).json({ error: 'Please provide valid email_id or email_data.' });
  }

  try {
    const draft = await draftingEngine.generateDraft(targetEmail, model);
    draftsCache.set(targetEmail.id, draft);
    res.json(draft);
  } catch (err: any) {
    res.status(500).json({ error: 'Draft generation failed', details: err.message });
  }
});

app.post('/review', (req: Request, res: Response) => {
  const { email_id, draft_id, action, final_reply, editor_name, editor_notes } = req.body;

  const targetEmail = emails.find((e) => e.id === email_id);
  const draft = draftsCache.get(email_id);

  if (!targetEmail || !draft) {
    return res.status(400).json({ error: 'Email or generated draft not found in session.' });
  }

  const result = autonomyManager.recordFeedback({
    emailId: targetEmail.id,
    draftId: draft_id || draft.id,
    category: draft.category,
    originalDraft: draft.suggested_reply,
    sentReply: final_reply || draft.suggested_reply,
    action: action as ReviewAction,
    editorName: editor_name || 'Support Reviewer',
    editorNotes: editor_notes
  });

  res.json({
    status: 'feedback_recorded',
    action_taken: action,
    similarity: result.similarity,
    autonomy_status: result.status
  });
});

app.get('/autonomy', (req: Request, res: Response) => {
  res.json(autonomyManager.getAllStatuses());
});

app.post('/autonomy/simulate-streak', (req: Request, res: Response) => {
  const { category, count } = req.body;
  if (!category) {
    return res.status(400).json({ error: 'category is required' });
  }
  const updated = autonomyManager.simulateStreak(category, count || 20);
  res.json(updated);
});

app.get('/feedback', (req: Request, res: Response) => {
  const limit = req.query.limit ? parseInt(req.query.limit as string) : 50;
  res.json(autonomyManager.getFeedbackHistory(limit));
});

export default app;

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`[Task 2] Inbox Agent Server listening on http://127.0.0.1:${PORT}`);
  });
}
