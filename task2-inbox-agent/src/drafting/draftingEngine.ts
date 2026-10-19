import Anthropic from '@anthropic-ai/sdk';
import { CustomerEmail, EmailDraft, EmailCategory, RiskLevel, SourceCitation } from '../email/types';
import { EmailClassifier } from '../email/classifier';
import { KnowledgeBrainClient, KnowledgeQueryResponse } from '../knowledge-client/knowledgeClient';
import { AutonomyManager } from '../feedback/autonomyManager';

export class DraftingEngine {
  private anthropic: Anthropic | null = null;
  private classifier: EmailClassifier;
  private kbClient: KnowledgeBrainClient;
  private autonomyManager: AutonomyManager;
  public promptVersion = 'v1.4-consultant-grounded';

  constructor(
    kbClient?: KnowledgeBrainClient,
    autonomyManager?: AutonomyManager
  ) {
    this.classifier = new EmailClassifier();
    this.kbClient = kbClient || new KnowledgeBrainClient();
    this.autonomyManager = autonomyManager || new AutonomyManager();

    if (process.env.ANTHROPIC_API_KEY) {
      try {
        this.anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
      } catch (e) {
        console.warn('Failed to initialize Anthropic SDK:', e);
      }
    }
  }

  /**
   * Generates a grounded, professional email draft.
   */
  async generateDraft(
    email: CustomerEmail,
    modelName: string = 'claude-3-5-sonnet-20241022'
  ): Promise<EmailDraft> {
    const startTime = Date.now();

    // 1. Classify Intent and Risk
    const classification = this.classifier.classify(email.subject, email.body);
    const category = classification.category;
    const riskLevel = classification.risk_level;

    // 2. Query Knowledge Brain for Product Evidence
    let kbResponse: KnowledgeQueryResponse | null = null;
    let sources: SourceCitation[] = [];

    if (category === 'how_to' || category === 'troubleshooting' || category === 'project_request') {
      kbResponse = await this.kbClient.query(`${email.subject} ${email.body}`, modelName);
      if (kbResponse && kbResponse.sources) {
        sources = kbResponse.sources;
      }
    }

    // 3. Determine Human Review and Autonomy Eligibility
    const autonomyStatus = this.autonomyManager.getStatus(category);
    const isAutonomyEligible =
      autonomyStatus.is_auto_send_eligible &&
      riskLevel === 'low' &&
      category === 'how_to';

    const needsHumanReview = !isAutonomyEligible || riskLevel !== 'low';

    let reasonForReview = 'Standard policy check before dispatch';
    if (riskLevel === 'high') {
      reasonForReview = 'High-risk email (financial, cancellation, or escalated complaint) mandates human sign-off.';
    } else if (category === 'project_request' || category === 'quote_request') {
      reasonForReview = 'Commercial or custom engineering scope requires consultant verification.';
    } else if (!isAutonomyEligible) {
      reasonForReview = `Category '${category}' requires 20 consecutive unedited human approvals (current streak: ${autonomyStatus.consecutive_clean_sends}/20).`;
    }

    // 4. Generate Draft Reply Text
    let suggestedReply = '';
    let summary = '';
    let followUpAction = '';
    let tokens = { input: 0, output: 0, total: 0 };

    if (this.anthropic && process.env.ANTHROPIC_API_KEY) {
      try {
        const kbContext = kbResponse && kbResponse.sources.length > 0 ? kbResponse.answer : 'No direct KB article found.';
        const response = await this.anthropic.messages.create({
          model: modelName,
          max_tokens: 600,
          system: (
            `You are an AI Tech Consultant and Customer Success Specialist for Brilliant Directories.\n` +
            `Draft a polite, professional, and precise reply to the customer's email.\n` +
            `Use the following verified product knowledge:\n${kbContext}\n\n` +
            `Guidelines:\n` +
            `- Tone: Helpful, empathetic, and authoritative.\n` +
            `- Never promise unauthorized refunds or unvetted delivery dates.\n` +
            `- Cite official documentation URLs where applicable.\n` +
            `- Provide actionable next steps.`
          ),
          messages: [
            {
              role: 'user',
              content: `Subject: ${email.subject}\nFrom: ${email.sender}\nBody: ${email.body}`
            }
          ]
        });

        suggestedReply = (response.content[0] as any).text.trim();
        tokens = {
          input: response.usage.input_tokens,
          output: response.usage.output_tokens,
          total: response.usage.input_tokens + response.usage.output_tokens
        };
      } catch (err) {
        console.warn('Anthropic API call fallback to grounded template generator:', err);
      }
    }

    // Deterministic High-Quality Fallback Generator if offline or testing
    if (!suggestedReply) {
      const generated = this.synthesizeReply(email, category, riskLevel, kbResponse);
      suggestedReply = generated.reply;
      summary = generated.summary;
      followUpAction = generated.followUp;
      tokens = generated.tokens;
    } else {
      summary = `Customer inquiry regarding ${email.subject.toLowerCase()}`;
      followUpAction = 'Await customer feedback after sending';
    }

    const latencyMs = Date.now() - startTime;

    return {
      id: `DRF-${Date.now()}-${Math.random().toString(36).substring(2, 7).toUpperCase()}`,
      email_id: email.id,
      category,
      summary,
      suggested_reply: suggestedReply,
      sources,
      risk_level: riskLevel,
      needs_human_review: needsHumanReview,
      reason_for_review: reasonForReview,
      follow_up_action: followUpAction,
      auto_send_eligible: isAutonomyEligible,
      model_used: modelName,
      confidence: classification.confidence,
      tokens,
      latency_ms: latencyMs,
      created_at: new Date().toISOString()
    };
  }

  /**
   * High-fidelity deterministic synthesis engine grounded in product knowledge.
   */
  private synthesizeReply(
    email: CustomerEmail,
    category: EmailCategory,
    risk: RiskLevel,
    kbResponse: KnowledgeQueryResponse | null
  ): { reply: string; summary: string; followUp: string; tokens: any } {
    let reply = '';
    let summary = '';
    let followUp = '';

    const senderName = email.sender.split('@')[0].replace('.', ' ').replace(/\b\w/g, (c) => c.toUpperCase());

    switch (category) {
      case 'how_to':
        summary = `Customer asking how to configure ${email.subject.replace(/how to|where do i/gi, '').trim()}`;
        if (kbResponse && kbResponse.status === 'answered' && kbResponse.sources.length > 0) {
          const src = kbResponse.sources[0];
          reply = (
            `Hi ${senderName},\n\n` +
            `Thank you for reaching out to support!\n\n` +
            `Here are the exact steps to configure this in your Brilliant Directories admin dashboard:\n\n` +
            `${kbResponse.answer.replace(/According to.*?:\n\n/g, '').replace(/For complete.*?$/g, '').trim()}\n\n` +
            `For step-by-step screenshots and additional settings, please see our official documentation guide:\n` +
            `${src.url}\n\n` +
            `Please let us know if you have any questions as you set this up!\n\n` +
            `Best regards,\nCustomer Success Team`
          );
        } else {
          reply = (
            `Hi ${senderName},\n\n` +
            `Thank you for reaching out! We received your inquiry regarding "${email.subject}".\n\n` +
            `Our engineering team is reviewing the specific settings for your directory configuration. ` +
            `We will follow up shortly with precise step-by-step instructions.\n\n` +
            `Best regards,\nCustomer Success Team`
          );
        }
        followUp = 'Check in 24 hours if customer succeeded with setup.';
        break;

      case 'troubleshooting':
        summary = `Troubleshooting report: ${email.subject}`;
        reply = (
          `Hi ${senderName},\n\n` +
          `Thank you for alerting us to this issue. We take technical interruptions seriously and are investigating immediately.\n\n` +
          `Preliminary analysis:\n` +
          `- Issue: ${email.subject}\n` +
          `- Recommended immediate check: Verify settings in your Admin Dashboard and confirm active credentials/API keys.\n\n` +
          `Our technical support specialist is reviewing your site logs now and will provide an update within 2 hours.\n\n` +
          `Sincerely,\nTechnical Operations Support`
        );
        followUp = 'Escalate to Tier 2 Engineer for immediate log inspection.';
        break;

      case 'project_request':
        summary = `Custom development scope inquiry: ${email.subject}`;
        reply = (
          `Hi ${senderName},\n\n` +
          `Thank you for considering our team for your custom project!\n\n` +
          `We have received your request regarding: "${email.subject}". ` +
          `Our Senior Solutions Architect is reviewing your requirements to determine existing built-in capabilities vs. custom engineering modules.\n\n` +
          `We would love to schedule a brief 20-minute discovery call this week to finalize specifications and prepare a formal Scope of Work and developer estimate.\n\n` +
          `Looking forward to collaborating,\nAI Tech Consulting Team`
        );
        followUp = 'Coordinate calendar link and generate preliminary Scope of Work draft.';
        break;

      case 'refund_cancellation':
        summary = `Urgent billing/refund inquiry: ${email.subject}`;
        reply = (
          `Dear ${senderName},\n\n` +
          `We have received your cancellation and refund request regarding your account.\n\n` +
          `Your request has been routed to our Billing Department for immediate review under our terms of service and refund guarantee. ` +
          `To protect your account security, our billing supervisor is reviewing the order history and will confirm the cancellation and refund transaction details shortly.\n\n` +
          `Reference ID: ${email.id}\n\n` +
          `Warm regards,\nBilling & Accounts Management`
        );
        followUp = 'Mandatory supervisor sign-off before issuing Stripe refund.';
        break;

      case 'complaint':
        summary = `Escalated customer complaint: ${email.subject}`;
        reply = (
          `Dear ${senderName},\n\n` +
          `We sincerely apologize for the frustration and disruption this has caused your business.\n\n` +
          `We understand how critical uninterrupted uptime and prompt support are to your operations. ` +
          `Your feedback has been escalated directly to our Leadership and Technical Operations teams. ` +
          `A senior manager is personally reviewing your case and will contact you directly today with a full root-cause report and resolution.\n\n` +
          `Sincerely,\nCustomer Relations Director`
        );
        followUp = 'Director phone call or personal email within 1 hour.';
        break;

      case 'quote_request':
        summary = `Commercial quote request: ${email.subject}`;
        reply = (
          `Hi ${senderName},\n\n` +
          `Thank you for requesting an estimate on your project!\n\n` +
          `We are preparing a detailed breakdown covering milestones, developer hours (low, likely, high estimates), and transparent pricing. ` +
          `Our proposals include both built-in configuration options and custom development tasks so you can choose the budget that suits your business.\n\n` +
          `Our proposal will be delivered to your inbox within 24 hours.\n\n` +
          `Best regards,\nSolutions Consulting Team`
        );
        followUp = 'Run Task 3 Meeting-to-Scope estimator to produce task hour table.';
        break;

      case 'follow_up':
        summary = `Follow-up received for ${email.subject}`;
        reply = (
          `Hi ${senderName},\n\n` +
          `Thank you for following up! We appreciate your patience.\n\n` +
          `We are actively working on your request and will provide the requested update by end of day today.\n\n` +
          `Best regards,\nCustomer Success Team`
        );
        followUp = 'Deliver promised update before 5:00 PM.';
        break;
    }

    const approxIn = (email.subject.length + email.body.length) / 3;
    const approxOut = reply.length / 3;

    return {
      reply,
      summary,
      followUp,
      tokens: {
        input: Math.round(approxIn),
        output: Math.round(approxOut),
        total: Math.round(approxIn + approxOut)
      }
    };
  }
}
