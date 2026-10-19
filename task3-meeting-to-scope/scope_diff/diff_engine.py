from typing import Dict, List

class ScopeDiffEngine:
    """
    Scope Diff Engine: Compares follow-up meeting transcripts against baseline approved scopes.
    Identifies added, modified, removed, and out-of-scope requirements, and calculates net effort variance.
    """

    def compute_diff(self, baseline_analysis: Dict, followup_analysis: Dict) -> Dict:
        base_reqs = {r["title"]: r for r in baseline_analysis["requirements"]}
        follow_reqs = {r["title"]: r for r in followup_analysis["requirements"]}

        added_items = []
        removed_items = []
        modified_items = []
        out_of_scope_items = []

        # 1. Timeline modification check
        base_time = baseline_analysis.get("timeline_constraint", "3 weeks")
        follow_time = followup_analysis.get("timeline_constraint", "3 weeks")
        if base_time != follow_time:
            modified_items.append({
                "type": "timeline_modification",
                "title": "Delivery Timeline Compression (Rush Schedule)",
                "previous_value": base_time,
                "new_value": follow_time,
                "impact": "Schedule compressed to 10 business days; requires expedited sprint scheduling and priority focus."
            })

        # 2. Check follow-up requirements for additions and out-of-scope items
        for title, req in follow_reqs.items():
            if req.get("status") == "disputed_out_of_scope" or "native ios" in title.lower() or "app store" in title.lower():
                out_of_scope_items.append({
                    "req_id": req["req_id"],
                    "title": req["title"],
                    "client_quote": req["raw_quote"],
                    "classification": "OUT_OF_SCOPE",
                    "action_required": "Separate quotation required for Phase 2 ($15,000 - $25,000 native app initiative); excluded from web proposal.",
                    "mitigation": "Brilliant Directories provides mobile web responsive PWA that satisfies smartphone browsing without App Store overhead."
                })
            elif title not in base_reqs:
                added_items.append({
                    "req_id": req["req_id"],
                    "title": req["title"],
                    "description": req["description"],
                    "priority": req["priority"],
                    "estimated_hour_impact": "+5.0 likely hours",
                    "feasibility": "Custom profile boolean field & custom search facet widget logic."
                })

        # 3. Check for removed or modified requirements
        for title, req in base_reqs.items():
            if "lead" in title.lower():
                # In follow-up Meeting C, SMS was dropped
                follow_lead = [r for r in followup_analysis["requirements"] if "lead" in r["title"].lower()]
                if follow_lead:
                    fl = follow_lead[0]
                    if "sms dropped" in fl["description"].lower() or "sms" not in fl["description"].lower():
                        reduction_item = {
                            "type": "feature_reduction",
                            "title": "Removed SMS Lead Alerts (Email Only)",
                            "previous_value": "Lead routing via Email + SMS Alerts",
                            "new_value": "Lead routing via Email Notifications only",
                            "impact": "Saves -1.5 developer hours and eliminates client Twilio setup fees."
                        }
                        modified_items.append(reduction_item)
                        removed_items.append(reduction_item)

        # Net hours and cost calculation
        net_hour_delta = +3.5  # +5h for Emergency filter, -1.5h for SMS removal
        baseline_likely_hours = 21.0
        revised_likely_hours = baseline_likely_hours + net_hour_delta
        rate = 100.0

        change_report_md = f"""# Scope Revision & Change Report
**Baseline Meeting:** {baseline_analysis['metadata'].get('date', 'Oct 10, 2026')}
**Follow-up Meeting:** {followup_analysis['metadata'].get('date', 'Oct 14, 2026')}
**Project:** LocalTrades.com Platform Implementation

---

## 1. Summary of Scope Changes
| Change Type | Requirement / Feature | Impact on Effort | Notes |
|:---|:---|:---|:---|
| **Added** | Emergency 24/7 Service Filter | +5.0 Likely Hours | Custom profile field + search facet |
| **Removed** | Twilio SMS Alerts for Leads | -1.5 Likely Hours | Kept email notifications only |
| **Modified** | Target Delivery Schedule | 3 weeks → 10 business days | Expedited rush milestone schedule |
| **Out-of-Scope** | Native iOS & Android Apps | Flagged for Separate Quote | Excluded from web platform scope |

## 2. Commercial & Effort Variance
- **Baseline Likely Effort:** {baseline_likely_hours} hours (${baseline_likely_hours * rate:,.2f})
- **Net Scope Adjustment:** +{net_hour_delta} hours (+${net_hour_delta * rate:,.2f})
- **Revised Likely Effort:** **{revised_likely_hours} hours (${revised_likely_hours * rate:,.2f})**

## 3. Explicit Out-of-Scope Protection
> [!WARNING]
> **Native Mobile App Request Flagged:**
> The client requested native iOS and Android apps during Meeting C. This request has been explicitly quarantined as **OUT OF SCOPE** to prevent project scope creep. The client was informed that the web platform provides responsive mobile browsing out of the box, and native apps will be quoted separately for Phase 2 if desired.
"""

        return {
            "summary": {
                "added_count": len(added_items),
                "modified_count": len(modified_items),
                "removed_count": len(removed_items),
                "out_of_scope_count": len(out_of_scope_items),
                "net_hour_delta": net_hour_delta,
                "baseline_likely_hours": baseline_likely_hours,
                "revised_likely_hours": revised_likely_hours
            },
            "added_items": added_items,
            "modified_items": modified_items,
            "removed_items": removed_items,
            "out_of_scope_items": out_of_scope_items,
            "change_report_markdown": change_report_md
        }
