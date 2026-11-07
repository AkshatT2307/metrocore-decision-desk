"""Participant-side inference over input-only problems.json.

This is a convenience runner, not a sandbox. Run participant notebooks in the
platform's restricted runtime, without mounting the organizer answer key.
"""

import csv
import json
import os
import tempfile
from pathlib import Path


def load_inputs(path: str | Path) -> list[dict]:
    path = Path(path).resolve()
    problems = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(problems, list) or not problems:
        raise ValueError("problems.json must contain a nonempty array")
    seen = set()
    for problem in problems:
        if not isinstance(problem, dict) or set(problem) - {"problem_id", "question", "image_path"}:
            raise ValueError("Input records may contain only problem_id, question, image_path")
        pid = problem.get("problem_id")
        if not isinstance(pid, str) or not pid.strip() or pid != pid.strip() or pid in seen:
            raise ValueError("Problem IDs must be unique, nonempty strings without surrounding whitespace")
        seen.add(pid)
        if not isinstance(problem.get("question"), str) or not problem["question"].strip():
            raise ValueError("Each problem needs a question")
        image = problem.get("image_path")
        if image is not None:
            if not isinstance(image, str) or not image or Path(image).is_absolute():
                raise ValueError("image_path must be a relative path or null")
            resolved = (path.parent / image).resolve()
            if not resolved.is_relative_to(path.parent) or not resolved.is_file():
                raise ValueError("Image must exist inside the input directory")
            problem["image_path"] = str(resolved)
    return problems


def _checkpoint(problems: list[dict], answers: dict, output: Path) -> None:
    """Atomically persist all expected IDs, with blank unanswered rows."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.writer(stream)
            writer.writerow(["problem_id", "answer"])
            for problem in problems:
                pid = problem["problem_id"]
                writer.writerow([pid, answers.get(pid, "")])
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run_submission(solve_fn, input_path: str | Path,
                   output_path: str | Path = "submission.csv") -> dict:
    """Call solve(question, image_path), checkpointing after each attempt.

    Ordinary per-problem exceptions become blank answers, worth zero. Fatal
    runtime failures are controlled by the execution platform; a checkpoint
    does not guarantee that Kaggle will score a failed notebook session.
    """
    if not callable(solve_fn):
        raise ValueError("solve must be callable")
    problems = load_inputs(input_path)
    output = Path(output_path)
    answers = {}
    _checkpoint(problems, answers, output)
    for index, problem in enumerate(problems, start=1):
        pid = problem["problem_id"]
        try:
            answer = solve_fn(problem["question"], problem.get("image_path"))
            answers[pid] = "" if answer is None else str(answer)
            status = "returned"
        except Exception:
            answers[pid] = ""
            status = "failed"
        _checkpoint(problems, answers, output)
        # Never include question text, reference data, or exception messages.
        print(f"{index}/{len(problems)} {status}")
    return answers
