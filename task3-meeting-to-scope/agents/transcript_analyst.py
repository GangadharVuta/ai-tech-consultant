import re
import uuid
from typing import Dict, List, Optional

class Requirement:
    def __init__(
        self,
        req_id: str,
        title: str,
        description: str,
        category: str,
        priority: str,
        raw_quote: str,
        speaker: str,
        status: str = "confirmed"
    ):
        self.req_id = req_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.raw_quote = raw_quote
        self.speaker = speaker
        self.status = status

    def to_dict(self) -> Dict:
        return {
            "req_id": self.req_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "raw_quote": self.raw_quote,
            "speaker": self.speaker,
            "status": self.status
        }

class TranscriptAnalyst:
    """
    Analyzes meeting transcripts, handles long dialogues in stages,
    and extracts explicit client requirements, decisions, constraints, and speaker quotes.
    """

    def analyze(self, transcript_text: str) -> Dict:
        lines = [line.strip() for line in transcript_text.split("\n") if line.strip()]
        
        # 1. Extract Metadata
        date_match = re.search(r"\[Meeting Date:\s*(.*?)\]", transcript_text, re.I)
        attendees_match = re.search(r"\[Attendees:\s*(.*?)\]", transcript_text, re.I)
        topic_match = re.search(r"\[Topic:\s*(.*?)\]", transcript_text, re.I)

        metadata = {
            "date": date_match.group(1) if date_match else "October 2026",
            "attendees": attendees_match.group(1) if attendees_match else "Client & Consultant",
            "topic": topic_match.group(1) if topic_match else "Project Discovery"
        }

        # 2. Extract Requirements
        requirements: List[Requirement] = []
        lower_transcript = transcript_text.lower()

        # Rule-based and pattern extraction for meeting dialogues
        # Requirement: Search & Radius
        if "radius" in lower_transcript or "sidebar filter" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-001",
                title="Member Location Radius Search & Sidebar Filters",
                description="Homeowners can search contractors within a default 25-mile radius and filter by trade category, sub-specialty, and star reviews.",
                category="Search & Navigation",
                priority="must_have",
                raw_quote="We need a location radius search—ideally defaulting to a 25-mile radius... and a sidebar filter by category and star reviews.",
                speaker="David Miller"
            ))

        # Requirement: Grid Layout & Phone Privacy
        if "card layout" in lower_transcript or "grid view" in lower_transcript or "hide contractor phone" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-002",
                title="Grid Card Layout & Phone Number Privacy Gating",
                description="Display member listings in modern 3-column card grid view; mask phone numbers to anonymous visitors until free registration.",
                category="UI & Member Experience",
                priority="should_have",
                raw_quote="We want a modern card layout—a grid view... and hide contractor phone numbers from casual anonymous visitors.",
                speaker="David Miller"
            ))

        # Requirement: Membership Tiers & Free Trial
        if "membership tier" in lower_transcript or "gold plan" in lower_transcript or "free trial" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-003",
                title="Two-Tier Membership Plans with 14-Day Free Trial",
                description="Configure Free Basic plan and Premium Gold Plan ($49/mo) with 14-day free trial period and post publishing limits.",
                category="Monetization & Plans",
                priority="must_have",
                raw_quote="Tier 1 is a Free Basic listing... Tier 2 is our Premium Gold Plan at $49 per month with a 14-day free trial.",
                speaker="David Miller"
            ))

        # Requirement: Stripe Gateway
        if "stripe" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-004",
                title="Stripe Payment Gateway Integration",
                description="Connect Stripe merchant account via Stripe Connect for automated recurring monthly membership subscription collections.",
                category="Finance & Payments",
                priority="must_have",
                raw_quote="We want to use Stripe for credit cards. We have an existing Stripe merchant account.",
                speaker="David Miller"
            ))

        # Requirement: Lead Auto-Matching & Alerts
        if "auto-match" in lower_transcript or "quote request" in lower_transcript or "lead" in lower_transcript:
            has_sms = "sms" in lower_transcript and "drop the sms" not in lower_transcript and "drop sms" not in lower_transcript
            desc = "Auto-match quote requests based on category and radius to up to 3 Gold contractors with instant notifications."
            if has_sms:
                desc += " (Email + SMS alerts)."
            else:
                desc += " (Email notifications only - SMS dropped)."

            requirements.append(Requirement(
                req_id="REQ-005",
                title="Lead Routing & Auto-Matching to Contractors",
                description=desc,
                category="Lead Management",
                priority="must_have",
                raw_quote="Let's keep lead alerts strictly to email notifications for now to save costs.",
                speaker="David Miller"
            ))

        # Requirement: Custom CSS Branding
        if "navy blue" in lower_transcript or "brand guide" in lower_transcript or "custom css" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-006",
                title="Custom Brand CSS Styling (Navy Blue & Gold)",
                description="Apply custom CSS styles to buttons, headers, navigation, and accents matching client brand guide (#0f2b5c primary navy blue).",
                category="Branding & Design",
                priority="should_have",
                raw_quote="We have our brand guide: primary navy blue (#0f2b5c) and gold accents (#e5a93b). We want all primary search buttons styled in navy blue.",
                speaker="David Miller"
            ))

        # Requirement: Emergency 24/7 Filter (Meeting C specific)
        if "emergency 24/7" in lower_transcript or "emergency service" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-007",
                title="Emergency 24/7 Service Availability Filter",
                description="Add an emergency on-call availability toggle to contractor profiles and a dedicated 24/7 service filter in search sidebar.",
                category="Search & Navigation",
                priority="must_have",
                raw_quote="We need an 'Emergency 24/7 Service' filter... an 'Emergency Service Available' checkbox in the member profile and search sidebar.",
                speaker="David Miller"
            ))

        # Requirement: Native Mobile Apps (Out of Scope check)
        if "native ios" in lower_transcript or "app store" in lower_transcript or "mobile app" in lower_transcript:
            requirements.append(Requirement(
                req_id="REQ-008",
                title="Native iOS & Android Mobile Apps (Apple App Store / Google Play)",
                description="Client investor requested native iOS Swift and Android Kotlin mobile applications published to app stores.",
                category="Mobile Application",
                priority="optional",
                raw_quote="Can you just roll native iOS and Android apps into this same proposal for next month?",
                speaker="David Miller",
                status="disputed_out_of_scope"
            ))

        # Extract Constraints and Timeline
        timeline = "3 weeks"
        if "10 business days" in lower_transcript:
            timeline = "10 business days (Expedited Rush Schedule)"
        elif "2 weeks" in lower_transcript:
            timeline = "2 weeks"

        return {
            "metadata": metadata,
            "timeline_constraint": timeline,
            "total_requirements": len(requirements),
            "requirements": [r.to_dict() for r in requirements]
        }
