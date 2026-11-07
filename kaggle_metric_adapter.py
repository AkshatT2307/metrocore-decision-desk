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
