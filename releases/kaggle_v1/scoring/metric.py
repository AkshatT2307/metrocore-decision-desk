# Generated from evaluator.py; do not hand-edit.
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

"""Build-time adapter appended to shared score_one/parse_answer definitions.

The generated metric.py / metric.ipynb include those definitions and run standalone.
This source is not intended to be uploaded on its own.
"""

import pandas as pd


class ParticipantVisibleError(Exception):
    pass


def score(solution: pd.DataFrame, submission: pd.DataFrame,
          row_id_column_name: str) -> float:
    """Mean MetroCore score; higher is better, range [-0.5, 1].

    Kaggle supplies the relevant leaderboard subset to this function. Usage is
    host metadata, not used to choose a subset inside this metric. Prediction
    rows must match that supplied subset exactly. No solution values appear in
    participant-visible errors. 'skip' is the nonempty abstention wire token.
    """
    identifier = row_id_column_name
    expected = {identifier, "answer"}
    if identifier == "answer" or not expected.issubset(solution.columns):
        raise ValueError("Organizer solution schema is invalid")
    if solution.empty or solution.columns.duplicated().any():
        raise ValueError("Organizer solution is empty or has duplicate columns")
    if submission.columns.duplicated().any() or set(submission.columns) != expected:
        raise ParticipantVisibleError("Submission must contain only the ID column and answer")
    for frame, organizer in [(solution, True), (submission, False)]:
        ids = frame[identifier]
        invalid = ids.isna().any() or ids.duplicated().any() or any(
            not isinstance(value, str) or not value.strip() or value != value.strip()
            for value in ids.tolist()
        )
        if invalid:
            if organizer:
                raise ValueError("Organizer solution IDs are invalid")
            raise ParticipantVisibleError("Submission IDs must be unique, nonempty strings")
    if set(solution[identifier]) != set(submission[identifier]):
        raise ParticipantVisibleError("Submission IDs do not match the expected input IDs")
    predictions = submission.set_index(identifier)["answer"]
    total = 0.0
    for pid, reference in zip(solution[identifier], solution["answer"]):
        # A missing reference is a host-side problem, never an infeasible case.
        if pd.isna(reference):
            raise ValueError("Organizer reference is missing; check CSV token parsing")
        value = predictions.loc[pid]
        if pd.isna(value) or (isinstance(value, str) and value.strip().lower() == "skip"):
            value = None
        total += score_one(value, reference)[0]
    return float(total / len(solution))
