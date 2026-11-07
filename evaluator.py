"""
MetroCore Decision Desk — Organizer Evaluation Script (v3)
==========================================================
NOT distributed to participants. Completely hidden pipeline.

Scores a submission against the organizer-only reference file. Never executes
participant code. Notebook execution belongs in a separate runtime that has
input questions and images, but no reference answers or scorer access.

Usage:
    python evaluator.py --submission submission.csv --test-set hidden_test_set.json
"""

import argparse
import json
import csv
import math
from decimal import Decimal


def parse_answer(raw) -> float | str | None:
    """Parse the competition format; None/blank means unanswered.

    Only literal 'na' denotes infeasibility. Source-dataset sentinel conversion
    is a data preparation step, never part of participant answer parsing.
    Invalid and nonfinite values raise ValueError.
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError("Boolean answers are not numbers")
    raw = str(raw).strip()
    if not raw:
        return None
    if raw.lower() == "na":
        return "na"
    try:
        value = float(raw)
    except (ValueError, OverflowError) as exc:
        raise ValueError("Answer must be a finite number, 'na', or blank") from exc
    if not math.isfinite(value):
        raise ValueError("Answer must be finite")
    return value


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
    ref = parse_answer(reference)
    if ref is None:
        raise ValueError("Reference answer cannot be missing")
    try:
        sub = parse_answer(submitted)
    except ValueError:
        return 0.0, "invalid"

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
    # Decimal arithmetic on parsed float strings avoids rejecting ordinary
    # exact boundaries such as 1.01 vs 1 due to binary subtraction error.
    ref_val = Decimal(str(ref))
    sub_val = Decimal(str(sub))
    denom = max(Decimal(1), abs(ref_val))
    error = abs(sub_val - ref_val)

    if error <= Decimal("0.01") * denom:
        return 1.0, "correct"
    elif error <= Decimal("0.05") * denom:
        return 0.5, "close"
    else:
        return 0.0, "wrong"


def load_test_set(path: str) -> list[dict]:
    """Load hidden test set."""
    with open(path, "r", encoding="utf-8") as f:
        problems = json.load(f)
    validate_test_set(problems)
    return problems


def validate_test_set(test_set: list[dict]) -> None:
    """Reject invalid answer keys rather than silently scoring against them."""
    if not isinstance(test_set, list) or not test_set:
        raise ValueError("Test set must be a nonempty JSON array")
    ids = set()
    for problem in test_set:
        if not isinstance(problem, dict):
            raise ValueError("Each test problem must be an object")
        pid = problem.get("problem_id")
        if not isinstance(pid, str) or not pid.strip() or pid != pid.strip():
            raise ValueError("Problem IDs must be nonempty strings without surrounding whitespace")
        if pid in ids:
            raise ValueError(f"Duplicate reference problem ID: {pid}")
        ids.add(pid)
        if "reference_answer" not in problem or parse_answer(problem["reference_answer"]) is None:
            raise ValueError(f"Missing reference answer: {pid}")


def load_submission(path: str) -> dict:
    """Load submission CSV. Returns {problem_id: answer}."""
    results = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["problem_id", "answer"]:
            raise ValueError("CSV header must be exactly: problem_id,answer")
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV row {line} must contain exactly two fields; use an empty answer for missing")
            pid = row["problem_id"].strip()
            if not pid:
                raise ValueError(f"Empty problem ID on CSV row {line}")
            if pid in results:
                raise ValueError(f"Duplicate submission problem ID: {pid}")
            answer = row["answer"].strip()
            results[pid] = answer
    return results


def evaluate(submission: dict, test_set: list[dict]) -> dict:
    """Run full evaluation. Returns detailed results."""
    validate_test_set(test_set)
    unknown = set(submission) - {problem["problem_id"] for problem in test_set}
    if unknown:
        raise ValueError("Submission contains unknown problem IDs")
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
    parser.add_argument(
        "--submission",
        required=True,
        help="Path to a pre-built submission.csv"
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

    try:
        test_set = load_test_set(args.test_set)
        submission = load_submission(args.submission)
        result = evaluate(submission, test_set)
    except (ValueError, OSError, csv.Error) as exc:
        parser.error(str(exc))
    print(f"Loaded {len(test_set)} problems from hidden test set.\n")
    print_report(result)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  Detailed results saved to: {args.output_json}")


if __name__ == "__main__":
    main()
