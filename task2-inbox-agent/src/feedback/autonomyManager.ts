import fs from 'fs';
import path from 'path';
import { EmailCategory, CategoryAutonomyStatus, HumanFeedback, ReviewAction } from '../email/types';

export class AutonomyManager {
  private statusFilePath: string;
  private feedbackFilePath: string;
  private statuses: Record<EmailCategory, CategoryAutonomyStatus>;
  private feedbackHistory: HumanFeedback[];

  constructor(dataDir?: string) {
    const dir = dataDir || path.resolve(__dirname, '../../data');
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    this.statusFilePath = path.join(dir, 'autonomy_status.json');
    this.feedbackFilePath = path.join(dir, 'feedback_history.json');

    this.statuses = this.loadStatuses();
    this.feedbackHistory = this.loadFeedback();
  }

  private loadStatuses(): Record<EmailCategory, CategoryAutonomyStatus> {
    if (fs.existsSync(this.statusFilePath)) {
      try {
        return JSON.parse(fs.readFileSync(this.statusFilePath, 'utf-8'));
      } catch (e) {
        console.error('Error reading autonomy status file:', e);
      }
    }
    return this.initializeDefaultStatuses();
  }

  private initializeDefaultStatuses(): Record<EmailCategory, CategoryAutonomyStatus> {
    const categories: EmailCategory[] = [
      'how_to',
      'troubleshooting',
      'project_request',
      'refund_cancellation',
      'complaint',
      'quote_request',
      'follow_up'
    ];

    const defaultStatuses: any = {};
    const now = new Date().toISOString();

    for (const cat of categories) {
      const isHighRisk = cat === 'refund_cancellation' || cat === 'complaint';
      defaultStatuses[cat] = {
        category: cat,
        consecutive_clean_sends: 0,
        is_auto_send_eligible: false,
        high_risk_locked: isHighRisk,
        total_processed: 0,
        total_human_edits: 0,
        last_updated: now
      };
    }
    return defaultStatuses;
  }

  private saveStatuses(): void {
    fs.writeFileSync(this.statusFilePath, JSON.stringify(this.statuses, null, 2), 'utf-8');
  }

  private loadFeedback(): HumanFeedback[] {
    if (fs.existsSync(this.feedbackFilePath)) {
      try {
        return JSON.parse(fs.readFileSync(this.feedbackFilePath, 'utf-8'));
      } catch (e) {
        console.error('Error reading feedback file:', e);
      }
    }
    return [];
  }

  private saveFeedback(): void {
    fs.writeFileSync(this.feedbackFilePath, JSON.stringify(this.feedbackHistory, null, 2), 'utf-8');
  }

  /**
   * Calculates string similarity using Dice coefficient / token overlap (0.0 to 1.0).
   */
  public computeSimilarity(original: string, modified: string): number {
    const cleanOrig = original.trim().replace(/\s+/g, ' ');
    const cleanMod = modified.trim().replace(/\s+/g, ' ');

    if (cleanOrig === cleanMod) return 1.0;
    if (!cleanOrig || !cleanMod) return 0.0;

    const words1 = cleanOrig.toLowerCase().split(' ');
    const words2 = cleanMod.toLowerCase().split(' ');

    const set1 = new Set(words1);
    const set2 = new Set(words2);

    let intersection = 0;
    for (const w of set1) {
      if (set2.has(w)) intersection++;
    }

    const similarity = (2.0 * intersection) / (set1.size + set2.size);
    return Math.round(similarity * 100) / 100;
  }

  /**
   * Records human reviewer action and updates consecutive approval streaks.
   */
  public recordFeedback(feedback: {
    emailId: string;
    draftId: string;
    category: EmailCategory;
    originalDraft: string;
    sentReply: string;
    action: ReviewAction;
    editorName: string;
    editorNotes?: string;
  }): { status: CategoryAutonomyStatus; similarity: number } {
    const similarity = this.computeSimilarity(feedback.originalDraft, feedback.sentReply);
    const isUnchanged = feedback.action === 'approve' || similarity >= 0.98;
    const now = new Date().toISOString();

    const record: HumanFeedback = {
      id: `FDB-${Date.now()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
      email_id: feedback.emailId,
      draft_id: feedback.draftId,
      category: feedback.category,
      original_draft: feedback.originalDraft,
      sent_reply: feedback.sentReply,
      action: feedback.action,
      edit_similarity: similarity,
      editor_name: feedback.editorName,
      editor_notes: feedback.editorNotes,
      timestamp: now
    };

    this.feedbackHistory.push(record);
    this.saveFeedback();

    // Update streak
    const catStatus = this.statuses[feedback.category];
    catStatus.total_processed += 1;
    catStatus.last_updated = now;

    if (isUnchanged && feedback.action !== 'reject' && feedback.action !== 'escalate') {
      catStatus.consecutive_clean_sends += 1;
      // Check 20-consecutive-approval threshold
      if (catStatus.consecutive_clean_sends >= 20 && !catStatus.high_risk_locked) {
        catStatus.is_auto_send_eligible = true;
      }
    } else {
      // Draft was edited, rejected, or escalated -> RESET STREAK!
      catStatus.total_human_edits += 1;
      const prevStreak = catStatus.consecutive_clean_sends;
      catStatus.consecutive_clean_sends = 0;
      catStatus.is_auto_send_eligible = false;
      catStatus.last_reset_reason =
        feedback.action === 'reject'
          ? 'Draft rejected by human reviewer'
          : feedback.action === 'escalate'
          ? 'Escalated to human expert'
          : `Human reviewer edited draft (similarity ${similarity.toFixed(2)}, prior streak was ${prevStreak})`;
    }

    this.saveStatuses();
    return { status: catStatus, similarity };
  }

  public getStatus(category: EmailCategory): CategoryAutonomyStatus {
    return this.statuses[category] || this.initializeDefaultStatuses()[category];
  }

  public getAllStatuses(): Record<EmailCategory, CategoryAutonomyStatus> {
    return { ...this.statuses };
  }

  public getFeedbackHistory(limit: number = 50): HumanFeedback[] {
    return this.feedbackHistory.slice(-limit).reverse();
  }

  /**
   * For evaluation & testing: simulate a 20-streak clean run to verify auto-send unlocking.
   */
  public simulateStreak(category: EmailCategory, count: number = 20): CategoryAutonomyStatus {
    const catStatus = this.statuses[category];
    catStatus.consecutive_clean_sends = count;
    if (count >= 20 && !catStatus.high_risk_locked) {
      catStatus.is_auto_send_eligible = true;
    }
    catStatus.last_updated = new Date().toISOString();
    this.saveStatuses();
    return catStatus;
  }
}
