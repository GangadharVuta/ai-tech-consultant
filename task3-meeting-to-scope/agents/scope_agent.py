from typing import Dict, List

class ScopeAgent:
    """
    Scope Agent: Generates structured, unambiguous Scope of Work documents
    with deliverables, explicit exclusions, and measurable acceptance criteria.
    """

    def generate_scope(self, analysis: Dict, feasibility_results: List[Dict]) -> Dict:
        metadata = analysis["metadata"]
        requirements = analysis["requirements"]
        timeline = analysis["timeline_constraint"]

        deliverables = []
        inclusions = []
        exclusions = []
        acceptance_criteria = []

        # Map feasibility
        feasibility_map = {f["req_id"]: f for f in feasibility_results}

        d_idx = 1
        for req in requirements:
            req_id = req["req_id"]
            title = req["title"]
            desc = req["description"]
            feasibility = feasibility_map.get(req_id, {})
            cat = feasibility.get("feasibility_category", "potential_custom_development")

            if cat == "out_of_scope":
                exclusions.append(f"{title} (Excluded: {feasibility.get('technical_rationale')})")
                continue

            deliverable_id = f"DELIV-{d_idx:02d}"
            deliverables.append({
                "deliverable_id": deliverable_id,
                "requirement_ref": req_id,
                "title": title,
                "description": desc,
                "implementation_strategy": feasibility.get("implementation_strategy", "Standard implementation"),
                "feasibility_category": cat,
                "documentation_citation": feasibility.get("knowledge_citation")
            })

            inclusions.append(f"{title} - {desc}")
            acceptance_criteria.append({
                "deliverable_id": deliverable_id,
                "criterion": f"Verify {title.lower()} is configured in admin panel and functions as specified."
            })
            d_idx += 1

        # Standard safety exclusions
        exclusions.extend([
            "Native iOS / Android mobile application development and App Store publishing",
            "Ongoing third-party API transaction fees (Stripe merchant percentage, Google Maps API usage)",
            "Manual data entry of more than 50 sample member listings"
        ])

        return {
            "project_name": metadata.get("topic", "Directory Implementation"),
            "client_name": metadata.get("attendees", "Client"),
            "target_timeline": timeline,
            "project_objective": (
                "Deliver a high-converting, fully responsive member directory platform "
                "with automated subscription billing, radius search filtering, auto-matched contractor lead routing, "
                "and custom brand styling."
            ),
            "deliverables": deliverables,
            "inclusions": inclusions,
            "exclusions": exclusions,
            "acceptance_criteria": acceptance_criteria,
            "dependencies_and_assumptions": [
                "Client provides valid Stripe merchant account access via Stripe Connect authorization",
                "Client provides brand color hex codes and high-resolution logo assets",
                "Domain DNS access provided for production launch cutover"
            ]
        }
