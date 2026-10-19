export type EmailCategory =
  | 'how_to'
  | 'troubleshooting'
  | 'project_request'
  | 'refund_cancellation'
  | 'complaint'
  | 'quote_request'
  | 'follow_up';

export type RiskLevel = 'low' | 'medium' | 'high';

export type ReviewAction = 'approve' | 'edit_and_send' | 'reject' | 'escalate';

export interface CustomerEmail {
  id: string;
  sender: string;
  subject: string;
  body: string;
  received_at?: string;
  expected_category?: EmailCategory;
  expected_action?: string;
}

export interface SourceCitation {
  title: string;
  url: string;
  section?: string;
  relevance: number;
}

export interface EmailDraft {
  id: string;
  email_id: string;
  category: EmailCategory;
  summary: string;
  suggested_reply: string;
  sources: SourceCitation[];
  risk_level: RiskLevel;
  needs_human_review: boolean;
  reason_for_review: string;
  follow_up_action: string;
  auto_send_eligible: boolean;
  model_used: string;
  confidence: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  latency_ms: number;
  created_at: string;
}

export interface HumanFeedback {
  id: string;
  email_id: string;
  draft_id: string;
  category: EmailCategory;
  original_draft: string;
  sent_reply: string;
  action: ReviewAction;
  edit_similarity: number; // 1.0 = unchanged, < 0.98 = edited
  editor_name: string;
  editor_notes?: string;
  timestamp: string;
}

export interface CategoryAutonomyStatus {
  category: EmailCategory;
  consecutive_clean_sends: number;
  is_auto_send_eligible: boolean;
  high_risk_locked: boolean;
  total_processed: number;
  total_human_edits: number;
  last_reset_reason?: string;
  last_updated: string;
}
