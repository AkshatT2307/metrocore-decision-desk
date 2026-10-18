"""
MetroCore Decision Desk — Organizer Evaluation Script (v2)
==========================================================
NOT distributed to participants. Completely hidden pipeline.

Loads the hidden test set, imports the participant's solve() function,
runs it on every problem, scores, and reports.

Usage:
    python evaluator.py --notebook participant_notebook.ipynb --test-set hidden_test_set.json
    python evaluator.py --submission submission.csv --test-set hidden_test_set.json

Modes:
  1. --notebook: Extracts solve() from participant notebook, runs it, scores.
  2. --submission: Scores an existing submission.csv directly.
"""

import argparse
import json
import csv
import math
import sys
import os
import time
from pathlib import Path


def parse_answer(raw: str) -> float | str:
    """Parse an answer string. Returns float or 'na'."""
    raw = raw.strip().lower()
    if raw in ("na", "n/a", "no best solution", "infeasible", "none", "-99999.0"):
        return "na"
    try:
        return float(raw)
    except ValueError:
        return "na"


def score_one(submitted, reference) -> tuple[float, str]:
    """
    Score a single problem.

    Returns (score, reason).

    Scoring rules:
      - Correct: |A - A*| / max(1, |A*|) <= 0.01  →  +1
      - Close:   within 5% of A*                   →  +0.5
      - Wrong number (feasible, off > 5%)           →   0
      - Wrong number on infeasible (should be na)   →  -0.5
      - na on feasible problem                      →  -0.5
      - Correct na on infeasible                    →  +1
      - Missing / crash                             →   0
    """
    ref = parse_answer(str(reference))
    sub = parse_answer(str(submitted)) if submitted is not None else None

    # Missing answer
    if sub is None:
        return 0.0, "missing"

    ref_is_na = (ref == "na")
    sub_is_na = (sub == "na")

    if ref_is_na and sub_is_na:
        return 1.0, "correct_na"
    if ref_is_na and not sub_is_na:
        return -0.5, "number_on_infeasible"
    if not ref_is_na and sub_is_na:
        return -0.5, "na_on_feasible"

    # Both are numbers
    ref_val = float(ref)
    sub_val = float(sub)

    denom = max(1.0, abs(ref_val))
    rel_error = abs(sub_val - ref_val) / denom

    if rel_error <= 0.01:
        return 1.0, "correct"
    elif rel_error <= 0.05:
        return 0.5, "close"
    else:
        return 0.0, "wrong"


def load_test_set(path: str) -> list[dict]:
    """Load hidden test set."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_submission(path: str) -> dict:
    """Load submission CSV. Returns {problem_id: answer}."""
    results = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["problem_id"].strip()
            answer = row["answer"].strip()
            results[pid] = answer
    return results


def run_solve_on_test_set(solve_fn, test_set: list[dict]) -> dict:
    """Run participant's solve() on every problem. Returns {problem_id: answer}."""
    submission = {}
    for i, problem in enumerate(test_set):
        pid = problem["problem_id"]
        question = problem["question"]
        image_path = problem.get("image_path", None)

        start = time.time()
        try:
            answer = solve_fn(question, image_path)
            elapsed = time.time() - start
            submission[pid] = str(answer)
            print(f"  [{i+1:>3}/{len(test_set)}] {pid}  {elapsed:6.2f}s  OK")
        except Exception as e:
            elapsed = time.time() - start
            submission[pid] = ""
            print(f"  [{i+1:>3}/{len(test_set)}] {pid}  {elapsed:6.2f}s  ERROR: {e}")

    return submission


def evaluate(submission: dict, test_set: list[dict]) -> dict:
    """Run full evaluation. Returns detailed results."""
    results = []
    for problem in test_set:
        pid = problem["problem_id"]
        ref_answer = problem["reference_answer"]
        sub_answer = submission.get(pid, None)
        score, reason = score_one(sub_answer, ref_answer)
        results.append({
            "problem_id": pid,
            "reference": ref_answer,
            "submitted": sub_answer if sub_answer is not None else "<missing>",
            "score": score,
            "reason": reason,
        })

    total_score = sum(r["score"] for r in results)
    mean_score = total_score / len(results) if results else 0.0

    reason_counts = {}
    for r in results:
        reason_counts[r["reason"]] = reason_counts.get(r["reason"], 0) + 1

    return {
        "num_problems": len(results),
        "total_score": total_score,
        "mean_score": mean_score,
        "reason_counts": reason_counts,
        "details": results,
    }


def print_report(eval_result: dict):
    """Pretty-print evaluation results."""
    print("=" * 70)
    print("  MetroCore Decision Desk — Evaluation Report")
    print("=" * 70)
    print()

    print(f"{'Problem':<10} {'Submitted':<20} {'Reference':<20} {'Score':>6}  {'Reason'}")
    print("-" * 70)
    for r in eval_result["details"]:
        sub_str = str(r["submitted"])[:18]
        ref_str = str(r["reference"])[:18]
        print(f"{r['problem_id']:<10} {sub_str:<20} {ref_str:<20} {r['score']:>+5.1f}  {r['reason']}")

    print("-" * 70)
    print()
    print(f"  Problems evaluated : {eval_result['num_problems']}")
    print(f"  Total score        : {eval_result['total_score']:+.1f}")
    print(f"  Mean score         : {eval_result['mean_score']:.4f}")
    print()
    print("  Breakdown:")
    for reason, count in sorted(eval_result["reason_counts"].items()):
        print(f"    {reason:<25} {count}")
    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="MetroCore Decision Desk — Organizer Evaluation"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--submission",
        help="Path to a pre-built submission.csv"
    )
    group.add_argument(
        "--notebook",
        help="Path to participant's .ipynb (extracts and runs solve())"
    )
    parser.add_argument(
        "--test-set", required=True,
        help="Path to hidden_test_set.json"
    )
    parser.add_argument(
        "--output-json", default=None,
        help="Optional: save detailed results to JSON"
    )
    args = parser.parse_args()

    test_set = load_test_set(args.test_set)
    print(f"Loaded {len(test_set)} problems from hidden test set.\n")

    if args.submission:
        submission = load_submission(args.submission)
    else:
        # Extract solve() from notebook
        print("Extracting solve() from notebook...")
        nb_path = Path(args.notebook)
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        # Collect all code cells
        code_cells = [
            "".join(cell["source"])
            for cell in nb["cells"]
            if cell["cell_type"] == "code"
        ]
        full_code = "\n\n".join(code_cells)

        # Execute in isolated namespace
        ns = {}
        exec(full_code, ns)

        if "solve" not in ns:
            print("ERROR: No solve() function found in notebook.", file=sys.stderr)
            sys.exit(1)

        print(f"Running solve() on {len(test_set)} problems...\n")
        submission = run_solve_on_test_set(ns["solve"], test_set)

    result = evaluate(submission, test_set)
    print_report(result)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Detailed results saved to: {args.output_json}")


if __name__ == "__main__":
    main()
