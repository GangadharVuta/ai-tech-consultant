import { EmailCategory, RiskLevel } from './types';

export interface ClassificationResult {
  category: EmailCategory;
  confidence: number;
  risk_level: RiskLevel;
  urgency: 'low' | 'medium' | 'high';
  key_intent: string;
}

export class EmailClassifier {
  /**
   * Classifies email intent and risk level based on NLP rules, keyword semantics, and urgency patterns.
   */
  classify(subject: string, body: string): ClassificationResult {
    const text = `${subject} ${body}`.toLowerCase();

    // 1. High-priority Complaint Detection
    if (
      /\b(complaint|furious|unacceptable|lawyer|legal|sue|terrible|broken site|outage|down for|lost leads|scam|vanished|data loss)\b/i.test(text)
    ) {
      return {
        category: 'complaint',
        confidence: 0.96,
        risk_level: 'high',
        urgency: 'high',
        key_intent: 'Severe dissatisfaction, outage, or escalation complaint requiring immediate management review'
      };
    }

    // 2. Direct Subject Check: How-To question (e.g. "How do leads get automatically routed", "How do I...")
    if (/^how\s+(do|can|to|does|is|are)|where\s+(do|can|is)\s+i/i.test(subject.trim())) {
      return {
        category: 'how_to',
        confidence: 0.95,
        risk_level: 'low',
        urgency: 'low',
        key_intent: 'Product configuration, settings, or administrative how-to inquiry'
      };
    }

    // 3. Follow-up Detection
    if (
      /\b(following up|follow-up|follow up|checking in|status on|second request|did you receive|any update)\b/i.test(subject) ||
      /\b(following up|follow-up|second request)\b/i.test(text)
    ) {
      const isUrgent = text.includes('second request') || text.includes('refund');
      return {
        category: 'follow_up',
        confidence: 0.93,
        risk_level: isUrgent ? 'high' : 'low',
        urgency: isUrgent ? 'high' : 'medium',
        key_intent: 'Follow-up on previously submitted request or ongoing discussion'
      };
    }

    // 4. Custom Project Request Detection (custom modules, integrations, new architecture)
    if (
      /\b(build|custom project|new feature|telemedicine|data feed|virtual tour|multi-currency|booking|franchise|mitchell 1|etl)\b/i.test(text)
    ) {
      return {
        category: 'project_request',
        confidence: 0.93,
        risk_level: 'medium',
        urgency: 'medium',
        key_intent: 'Client requesting custom development, architecture, or 3rd-party integration'
      };
    }

    // 5. Troubleshooting (errors, bugs, payment double charge, SMS failure, rotated photos)
    if (
      /\b(error|failing|declined|not showing|not working|zero listings|watermark|not being delivered|urgent|crash|ssl|403|502|charged twice|upside down|rotated|not triggering)\b/i.test(text)
    ) {
      return {
        category: 'troubleshooting',
        confidence: 0.92,
        risk_level: 'medium',
        urgency: 'high',
        key_intent: 'Technical issue, payment failure, or broken feature requiring troubleshooting'
      };
    }

    // 6. Refund & Cancellation Detection (High financial/policy risk)
    if (
      /\b(refund|cancel our|cancellation|unsubscribe|stop billing|money back|void invoice|accidental charge)\b/i.test(text)
    ) {
      return {
        category: 'refund_cancellation',
        confidence: 0.95,
        risk_level: 'high',
        urgency: 'high',
        key_intent: 'Customer requesting subscription cancellation or monetary refund'
      };
    }

    // 7. Quote Request Detection
    if (
      /\b(quote|pricing quote|cost estimate|how many developer hours|hourly rate|how much would|fixed-price quote|retainer)\b/i.test(text)
    ) {
      return {
        category: 'quote_request',
        confidence: 0.94,
        risk_level: 'medium',
        urgency: 'medium',
        key_intent: 'Client requesting commercial quote, timeline, or hourly rate estimate'
      };
    }

    // 7. Default How-To Documentation Question
    return {
      category: 'how_to',
      confidence: 0.88,
      risk_level: 'low',
      urgency: 'low',
      key_intent: 'Product configuration, settings, or administrative how-to inquiry'
    };
  }
}
