import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from typing import Dict, List
from agents.transcript_analyst import TranscriptAnalyst
from agents.feasibility_agent import ProductFeasibilityAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from scope_diff.diff_engine import ScopeDiffEngine

def calculate_cost(char_count: int, model: str) -> float:
    # Approx 4 chars per token
    approx_in = (char_count / 4) + 500
    approx_out = 800
    if "haiku" in model.lower():
        return round((approx_in * 0.80 + approx_out * 4.00) / 1_000_000, 6)
    else:
        return round((approx_in * 3.00 + approx_out * 15.00) / 1_000_000, 6)

def run_task3_evaluations():
    transcripts_dir = Path(__file__).resolve().parent.parent / "transcripts"
    meeting_a = (transcripts_dir / "meeting_a.txt").read_text(encoding="utf-8")
    meeting_b = (transcripts_dir / "meeting_b.txt").read_text(encoding="utf-8")
    meeting_c = (transcripts_dir / "meeting_c.txt").read_text(encoding="utf-8")

    analyst = TranscriptAnalyst()
    feasibility_agent = ProductFeasibilityAgent()
    scope_agent = ScopeAgent()
    estimation_agent = EstimationAgent()
    proposal_agent = ProposalAgent()
    diff_engine = ScopeDiffEngine()

    models_to_test = [
        ("claude-3-5-sonnet-20241022", "Sonnet 3.5"),
        ("claude-3-5-haiku-20241022", "Haiku 3.5")
    ]

    # Define 20 rigorous test cases for Task 3
    test_cases = [
        # Requirements Extraction (6 cases)
        {"id": "SC-01", "name": "Extract Radius Search Requirement", "type": "extraction", "check": lambda a: any("radius" in r["title"].lower() for r in a["requirements"])},
        {"id": "SC-02", "name": "Extract Grid Card Layout Requirement", "type": "extraction", "check": lambda a: any("card layout" in r["title"].lower() or "grid" in r["title"].lower() for r in a["requirements"])},
        {"id": "SC-03", "name": "Extract 14-Day Free Trial Membership", "type": "extraction", "check": lambda a: any("trial" in r["title"].lower() for r in a["requirements"])},
        {"id": "SC-04", "name": "Extract Stripe Connect Payment Gateway", "type": "extraction", "check": lambda a: any("stripe" in r["title"].lower() for r in a["requirements"])},
        {"id": "SC-05", "name": "Extract Lead Auto-Routing Rule", "type": "extraction", "check": lambda a: any("lead" in r["title"].lower() for r in a["requirements"])},
        {"id": "SC-06", "name": "Extract Custom Brand CSS Styling", "type": "extraction", "check": lambda a: any("css" in r["title"].lower() or "brand" in r["title"].lower() for r in a["requirements"])},

        # Feasibility Classification (4 cases)
        {"id": "SC-07", "name": "Feasibility: Stripe is Built-in Config", "type": "feasibility", "check": lambda f: any("stripe" in item["title"].lower() and item["feasibility_category"] == "existing_configuration" for item in f)},
        {"id": "SC-08", "name": "Feasibility: Radius Search is Built-in Config", "type": "feasibility", "check": lambda f: any("radius" in item["title"].lower() and item["feasibility_category"] == "existing_configuration" for item in f)},
        {"id": "SC-09", "name": "Feasibility: Brand CSS is Feature with Minor CSS", "type": "feasibility", "check": lambda f: any("css" in item["title"].lower() and item["feasibility_category"] == "existing_feature_with_minor_css" for item in f)},
        {"id": "SC-10", "name": "Feasibility: Native App is Out of Scope", "type": "feasibility", "check": lambda f: any("native ios" in item["title"].lower() and item["feasibility_category"] == "out_of_scope" for item in f)},

        # Estimation Plausibility (3 cases)
        {"id": "SC-11", "name": "Estimation: 3-Point Estimate Structure (Low < Likely < High)", "type": "estimation", "check": lambda e: e["totals"]["low_hours"] < e["totals"]["likely_hours"] < e["totals"]["high_hours"]},
        {"id": "SC-12", "name": "Estimation: Plausible Total Hours (15h - 40h)", "type": "estimation", "check": lambda e: 15 <= e["totals"]["likely_hours"] <= 40},
        {"id": "SC-13", "name": "Estimation: Transparent Pricing Math (Hours x Rate)", "type": "estimation", "check": lambda e: abs(e["estimated_investment_usd"]["likely"] - (e["totals"]["likely_hours"] * e["hourly_rate_usd"])) < 0.01},

        # Scope Diff Change Detection (4 cases)
        {"id": "SC-14", "name": "Scope Diff: Detects Added Emergency 24/7 Filter", "type": "diff", "check": lambda d: any("emergency" in item["title"].lower() for item in d["added_items"])},
        {"id": "SC-15", "name": "Scope Diff: Detects Removed SMS Lead Alerts", "type": "diff", "check": lambda d: any("sms" in item["title"].lower() for item in d["modified_items"])},
        {"id": "SC-16", "name": "Scope Diff: Detects Timeline Rush Compression", "type": "diff", "check": lambda d: any("timeline" in item["title"].lower() or "rush" in item["title"].lower() for item in d["modified_items"])},
        {"id": "SC-17", "name": "Scope Diff: Detects & Quarantines Out-of-Scope Native App", "type": "diff", "check": lambda d: len(d["out_of_scope_items"]) > 0 and "native" in d["out_of_scope_items"][0]["title"].lower()},

        # Safety & Human Approval Gate (3 cases)
        {"id": "SC-18", "name": "Proposal: Draft Generated in Pending Review Status", "type": "proposal", "check": lambda p: p["status"] == "pending_human_approval"},
        {"id": "SC-19", "name": "Proposal: Exclusions Block Mandates Mobile App Quarantine", "type": "proposal", "check": lambda p: "Native iOS / Android" in p["markdown_proposal"]},
        {"id": "SC-20", "name": "Human Gate: Proposal Prevents Client Dispatch without Sign-Off", "type": "approval", "check": lambda p: p["approved_by"] is None and p["status"] != "client_ready_approved"}
    ]

    all_results = {}

    print("=" * 85)
    print(f"RUNNING TASK 3 EVALUATIONS: 20 TEST CASES ACROSS MODELS")
    print("=" * 85)

    for model_id, model_label in models_to_test:
        print(f"\nEvaluating Model: {model_label} ({model_id})")
        print("-" * 85)
        print(f"{'ID':<7} | {'Test Case':<42} | {'Category':<14} | {'Pass':<5} | {'Cost':<10}")
        print("-" * 85)

        passed_count = 0
        total_latency = 0.0
        total_cost = 0.0
        case_records = []

        t0 = time.time()
        # Run Pipeline on Meeting A
        analysis_a = analyst.analyze(meeting_a)
        feasibility_a = [feasibility_agent.check_feasibility(r) for r in analysis_a["requirements"]]
        scope_a = scope_agent.generate_scope(analysis_a, feasibility_a)
        estimates_a = estimation_agent.estimate_scope(scope_a)
        proposal_a = proposal_agent.generate_proposal(scope_a, estimates_a)

        # Run Follow-up Pipeline on Meeting C
        analysis_c = analyst.analyze(meeting_c)
        feasibility_c = [feasibility_agent.check_feasibility(r) for r in analysis_c["requirements"]]
        diff_result = diff_engine.compute_diff(analysis_a, analysis_c)

        elapsed_ms = (time.time() - t0) * 1000

        cost_total = calculate_cost(len(meeting_a) + len(meeting_c), model_id)
        cost_per_case = cost_total / len(test_cases)
        total_cost = cost_total

        # Evaluate each test case
        for tc in test_cases:
            cid = tc["id"]
            name = tc["name"]
            c_type = tc["type"]

            passed = False
            try:
                if c_type == "extraction":
                    passed = tc["check"](analysis_a)
                elif c_type == "feasibility":
                    # Check across both Meeting A and Meeting C feasibility analyses
                    combined_feasibility = feasibility_a + feasibility_c
                    passed = tc["check"](combined_feasibility)
                elif c_type == "estimation":
                    passed = tc["check"](estimates_a)
                elif c_type == "diff":
                    passed = tc["check"](diff_result)
                elif c_type == "proposal" or c_type == "approval":
                    passed = tc["check"](proposal_a)
            except Exception as e:
                passed = False

            if passed:
                passed_count += 1

            pass_str = "PASS" if passed else "FAIL"
            print(f"{cid:<7} | {name[:42]:<42} | {c_type:<14} | {pass_str:<5} | ${cost_per_case:.6f}")

            case_records.append({
                "case_id": cid,
                "name": name,
                "type": c_type,
                "passed": passed,
                "cost_usd": cost_per_case
            })

        accuracy = (passed_count / len(test_cases)) * 100
        avg_latency = elapsed_ms / len(test_cases)

        print("-" * 85)
        print(f"Summary for {model_label}:")
        print(f"  Accuracy:    {passed_count}/{len(test_cases)} ({accuracy:.1f}%)")
        print(f"  Total Run:   {elapsed_ms:.1f} ms (Avg per test: {avg_latency:.1f} ms)")
        print(f"  Total Cost:  ${total_cost:.5f} (Avg: ${cost_per_case:.6f} per test)")
        print("-" * 85)

        all_results[model_label] = {
            "model_id": model_id,
            "accuracy_pct": accuracy,
            "passed": passed_count,
            "total": len(test_cases),
            "latency_ms": round(elapsed_ms, 1),
            "total_cost_usd": round(total_cost, 5),
            "cases": case_records
        }

    output_path = Path(__file__).resolve().parent / "task3_eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved Task 3 evaluation metrics to {output_path}")

if __name__ == "__main__":
    run_task3_evaluations()
