from typing import Dict, List

class EstimationAgent:
    """
    Estimation Agent: Decomposes deliverables into discrete engineering tasks
    and calculates 3-point estimates (Low, Likely, High hours) with transparent reasoning.
    """

    def __init__(self, hourly_rate_usd: float = 100.0):
        self.hourly_rate_usd = hourly_rate_usd

    def estimate_scope(self, scope: Dict) -> Dict:
        deliverables = scope.get("deliverables", [])
        tasks = []

        for deliv in deliverables:
            did = deliv["deliverable_id"]
            title = deliv["title"]
            cat = deliv.get("feasibility_category", "")

            if cat == "existing_configuration":
                # Built-in configuration requires setup and validation only
                tasks.append({
                    "task_id": f"TSK-{did}-01",
                    "deliverable_ref": did,
                    "task_name": f"Configure & Test {title}",
                    "low_hours": 1.0,
                    "likely_hours": 2.0,
                    "high_hours": 3.5,
                    "complexity": "Low (Native Setting)",
                    "rationale": "Supported natively in Brilliant Directories admin panel; requires setting activation and test verification."
                })
            elif cat == "existing_feature_with_minor_css":
                tasks.append({
                    "task_id": f"TSK-{did}-01",
                    "deliverable_ref": did,
                    "task_name": f"Implement Brand CSS Overrides for {title}",
                    "low_hours": 2.0,
                    "likely_hours": 3.5,
                    "high_hours": 6.0,
                    "complexity": "Medium (CSS Styling)",
                    "rationale": "Writing custom CSS rules in Settings > Design Settings, responsive testing across mobile/desktop."
                })
            elif cat == "custom_development":
                tasks.append({
                    "task_id": f"TSK-{did}-01",
                    "deliverable_ref": did,
                    "task_name": f"Develop Custom Field & Query Logic for {title}",
                    "low_hours": 3.5,
                    "likely_hours": 6.0,
                    "high_hours": 9.0,
                    "complexity": "High (Custom Development)",
                    "rationale": "Adding custom member profile form variables, modifying search results widget facet, and validating query filtering."
                })

        # Add Quality Assurance and Launch Deployment
        tasks.append({
            "task_id": "TSK-QA-01",
            "deliverable_ref": "GENERAL",
            "task_name": "End-to-End Quality Assurance & Cross-Browser Testing",
            "low_hours": 2.0,
            "likely_hours": 3.5,
            "high_hours": 5.0,
            "complexity": "Medium (QA)",
            "rationale": "Verify checkout transactions, search radius filtering, lead auto-matching, and mobile responsiveness."
        })
        tasks.append({
            "task_id": "TSK-DEP-01",
            "deliverable_ref": "GENERAL",
            "task_name": "Domain Cutover, SSL Generation & Production Handover",
            "low_hours": 1.5,
            "likely_hours": 2.5,
            "high_hours": 4.0,
            "complexity": "Low (DevOps)",
            "rationale": "DNS pointing, SSL certificate provisioning, and administrative walkthrough with client."
        })

        total_low = round(sum(t["low_hours"] for t in tasks), 1)
        total_likely = round(sum(t["likely_hours"] for t in tasks), 1)
        total_high = round(sum(t["high_hours"] for t in tasks), 1)

        cost_low = round(total_low * self.hourly_rate_usd, 2)
        cost_likely = round(total_likely * self.hourly_rate_usd, 2)
        cost_high = round(total_high * self.hourly_rate_usd, 2)

        return {
            "hourly_rate_usd": self.hourly_rate_usd,
            "tasks": tasks,
            "totals": {
                "low_hours": total_low,
                "likely_hours": total_likely,
                "high_hours": total_high
            },
            "estimated_investment_usd": {
                "low": cost_low,
                "likely": cost_likely,
                "high": cost_high,
                "recommended_fixed_quote": cost_likely
            },
            "pricing_assumptions": [
                f"Billed at standard technical consulting rate of ${self.hourly_rate_usd:.0f}/hour",
                "Includes 14 days of complimentary post-launch warranty support",
                "Built-in feature utilization saves client over $4,000 compared to greenfield custom development"
            ]
        }
