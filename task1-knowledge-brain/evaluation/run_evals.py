import sys
import os
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from typing import Dict, List
from retrieval.vector_store import HybridVectorStore
from retrieval.qa_pipeline import QAPipeline

def calculate_cost(tokens: Dict[str, int], model: str) -> float:
    """Calculates query cost in USD based on official Anthropic API pricing."""
    in_tok = tokens.get("input", 0)
    out_tok = tokens.get("output", 0)
    if "haiku" in model.lower():
        # Haiku: $0.80 / 1M input, $4.00 / 1M output
        return round((in_tok * 0.80 + out_tok * 4.00) / 1_000_000, 6)
    else:
        # Sonnet 3.5: $3.00 / 1M input, $15.00 / 1M output
        return round((in_tok * 3.00 + out_tok * 15.00) / 1_000_000, 6)

def run_task1_evaluations():
    eval_file = Path(__file__).resolve().parent / "test_cases.json"
    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    vector_store = HybridVectorStore()
    qa = QAPipeline(vector_store=vector_store)

    models_to_test = [
        ("claude-3-5-sonnet-20241022", "Sonnet 3.5"),
        ("claude-3-5-haiku-20241022", "Haiku 3.5")
    ]

    all_results = {}

    print("=" * 80)
    print(f"RUNNING TASK 1 EVALUATIONS: {len(test_cases)} TEST CASES ACROSS MODELS")
    print("=" * 80)

    for model_id, model_label in models_to_test:
        print(f"\nEvaluating Model: {model_label} ({model_id})")
        print("-" * 80)
        print(f"{'ID':<7} | {'Category':<22} | {'Status':<11} | {'Pass':<5} | {'Latency':<8} | {'Cost':<10}")
        print("-" * 80)

        passed_count = 0
        total_latency = 0.0
        total_cost = 0.0
        case_records = []

        for case in test_cases:
            cid = case["id"]
            query = case["query"]
            expected_status = case["expected_status"]
            expected_source = case.get("expected_source_keyword")
            expected_terms = case.get("expected_terms", [])

            # Run query
            t0 = time.time()
            res = qa.generate_answer(query, model_name=model_id, top_k=4, auto_escalate=True)
            latency_ms = res["latency_ms"]
            total_latency += latency_ms

            cost = calculate_cost(res["tokens"], model_id)
            total_cost += cost

            # Evaluate pass criteria
            status_match = (res["status"] == expected_status)
            
            source_match = True
            if expected_source:
                source_titles = " ".join([s["title"] for s in res.get("sources", [])])
                source_match = (expected_source.lower() in source_titles.lower()) or (expected_source.lower() in res["answer"].lower())

            term_match = True
            if expected_terms and res["status"] == "answered":
                term_match = any(t.lower() in res["answer"].lower() for t in expected_terms)

            passed = status_match and source_match and term_match
            if passed:
                passed_count += 1

            status_str = res["status"]
            pass_str = "PASS" if passed else "FAIL"
            print(f"{cid:<7} | {case['category'][:22]:<22} | {status_str:<11} | {pass_str:<5} | {latency_ms:>6.1f}ms | ${cost:.6f}")

            case_records.append({
                "case_id": cid,
                "category": case["category"],
                "query": query,
                "expected_status": expected_status,
                "actual_status": res["status"],
                "confidence": res["confidence"],
                "passed": passed,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "sources_cited": [s["title"] for s in res.get("sources", [])],
                "answer_snippet": res["answer"][:120]
            })

        accuracy = (passed_count / len(test_cases)) * 100
        avg_latency = total_latency / len(test_cases)
        avg_cost = total_cost / len(test_cases)

        print("-" * 80)
        print(f"Summary for {model_label}:")
        print(f"  Accuracy:    {passed_count}/{len(test_cases)} ({accuracy:.1f}%)")
        print(f"  Avg Latency: {avg_latency:.1f} ms")
        print(f"  Total Cost:  ${total_cost:.5f} (Avg: ${avg_cost:.6f} per query)")
        print("-" * 80)

        all_results[model_label] = {
            "model_id": model_id,
            "accuracy_pct": accuracy,
            "passed": passed_count,
            "total": len(test_cases),
            "avg_latency_ms": round(avg_latency, 1),
            "total_cost_usd": round(total_cost, 5),
            "avg_cost_usd": round(avg_cost, 6),
            "cases": case_records
        }

    output_path = Path(__file__).resolve().parent / "task1_eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved detailed evaluation metrics to {output_path}")

if __name__ == "__main__":
    run_task1_evaluations()
