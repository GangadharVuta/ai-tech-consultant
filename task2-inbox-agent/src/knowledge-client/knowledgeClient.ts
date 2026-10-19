import { SourceCitation } from '../email/types';

export interface KnowledgeQueryResponse {
  answer: string;
  status: 'answered' | 'needs_human';
  sources: SourceCitation[];
  images: string[];
  confidence: number;
  needs_human: boolean;
  escalation_id?: string | null;
  model_used: string;
  latency_ms: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
}

export class KnowledgeBrainClient {
  private baseUrl: string;
  private timeoutMs: number;

  constructor(baseUrl: string = process.env.TASK1_API_URL || 'http://127.0.0.1:8001', timeoutMs: number = 8000) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.timeoutMs = timeoutMs;
  }

  /**
   * Queries the Task 1 Knowledge Brain API to retrieve grounded product facts and citations.
   */
  async query(question: string, modelOverride?: string): Promise<KnowledgeQueryResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Task2-InboxAgent/1.0'
        },
        body: JSON.stringify({
          query: question,
          model: modelOverride,
          top_k: 3,
          auto_escalate: true
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Knowledge Brain API returned HTTP ${response.status}: ${response.statusText}`);
      }

      const data = (await response.json()) as KnowledgeQueryResponse;
      return data;
    } catch (err: any) {
      clearTimeout(timeoutId);
      // Graceful fallback when Knowledge Brain is unreachable or offline
      return {
        answer: 'Notice: Knowledge Brain API is currently unreachable. Deferring to human specialist for verification.',
        status: 'needs_human',
        sources: [],
        images: [],
        confidence: 0.0,
        needs_human: true,
        escalation_id: null,
        model_used: 'fallback-offline',
        latency_ms: 0,
        tokens: { input: 0, output: 0, total: 0 }
      };
    }
  }

  /**
   * Checks the health and chunk count of the Task 1 Knowledge Brain.
   */
  async checkHealth(): Promise<{ healthy: boolean; details?: any }> {
    try {
      const resp = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        const data = await resp.json();
        return { healthy: true, details: data };
      }
      return { healthy: false };
    } catch {
      return { healthy: false };
    }
  }
}
