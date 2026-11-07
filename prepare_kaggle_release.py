"""Prepare disjoint public examples, private rerun inputs, and scoring assets.

No network calls or uploads. Defaults: exactly two image examples and three
text-only examples, randomly sampled with a recorded seed. Keeps all labels.
"""

import argparse
import ast
import csv
import hashlib
import html
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def notebook(cells):
    output = []
    for kind, source in cells:
        cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        output.append(cell)
    return {"nbformat": 4, "nbformat_minor": 4, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "cells": output}


def metric_source():
    source = (ROOT / "evaluator.py").read_text()
    functions = [ast.get_source_segment(source, node) for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef) and node.name in {"parse_answer", "score_one"}]
    assert len(functions) == 2
    return ("# Generated from evaluator.py; do not hand-edit.\nimport math\nfrom decimal import Decimal\n\n"
            + "\n\n".join(functions) + "\n\n" + (ROOT / "kaggle_metric_adapter.py").read_text())


def build(dataset, output, example_seed=20261109, split_seed=20261110):
    if output.exists():
        raise ValueError("Use a fresh output directory to avoid stale release files")
    problems = json.loads((dataset / "inference/problems.json").read_text())
    refs = {p["problem_id"]: p for p in json.loads((dataset / "organizer/hidden_test_set.json").read_text())}
    manifest = {p["problem_id"]: p for p in map(json.loads, (dataset / "organizer/manifest.jsonl").read_text().splitlines())}
    rng = random.Random(example_seed)
    chosen = rng.sample([p for p in problems if p["image_path"]], 2)
    chosen += rng.sample([p for p in problems if not p["image_path"]], 3)
    example_ids = {p["problem_id"] for p in chosen}
    hidden = [p for p in problems if p["problem_id"] not in example_ids]
    groups = defaultdict(list)
    for p in hidden:
        groups[(bool(p["image_path"]), refs[p["problem_id"]]["reference_answer"] == "na")].append(p["problem_id"])
    # Proposed 30/70 leaderboard split, proportional within modality/label strata.
    public_count = round(.3 * len(hidden))
    quotas = {key: int(len(ids) * .3) for key, ids in groups.items()}
    for key in sorted(groups, key=lambda key: (-(len(groups[key]) * .3 - quotas[key]), key))[:public_count-sum(quotas.values())]:
        quotas[key] += 1
    rng = random.Random(split_seed)
    feedback_ids = set()
    for key in sorted(groups):
        feedback_ids.update(rng.sample(groups[key], quotas[key]))
    for directory in ["public", "private_rerun", "scoring", "starter", "organizer", "pages"]:
        (output / directory).mkdir(parents=True)
    id_mapping = {}
    examples = []
    for i, p in enumerate(chosen, 1):
        pid = f"EX-{i:03d}"
        id_mapping[p["problem_id"]] = pid
        examples.append(dict(p, problem_id=pid, image_path=f"images/{pid.lower()}.png" if p["image_path"] else None))
    for folder, rows in [("public", examples), ("private_rerun", hidden)]:
        dest = output / folder
        save_json(dest / "problems.json", rows)
        shutil.copyfile(ROOT / "submission_runner.py", dest / "submission_runner.py")
        save_csv(dest / "sample_submission.csv", ["problem_id", "answer"], ((p["problem_id"], "skip") for p in rows))
        for p in rows:
            if p["image_path"]:
                (dest / "images").mkdir(exist_ok=True)
                original = next(x for x in chosen if id_mapping[x["problem_id"]] == p["problem_id"]) if folder == "public" else p
                shutil.copyfile(dataset / "inference" / original["image_path"], dest / p["image_path"])
    save_csv(output / "public/example_answers.csv", ["problem_id", "answer"],
             ((id_mapping[p["problem_id"]], refs[p["problem_id"]]["reference_answer"]) for p in chosen))
    save_csv(output / "scoring/solution.csv", ["problem_id", "answer", "Usage"],
             ((p["problem_id"], refs[p["problem_id"]]["reference_answer"], "Public" if p["problem_id"] in feedback_ids else "Private") for p in hidden))
    save_csv(output / "scoring/perfect_submission.csv", ["problem_id", "answer"],
             ((p["problem_id"], refs[p["problem_id"]]["reference_answer"]) for p in hidden))
    save_json(output / "scoring/hidden_test_set.json", [dict(p, reference_answer=refs[p["problem_id"]]["reference_answer"],
              image_path="../private_rerun/" + p["image_path"] if p["image_path"] else None) for p in hidden])
    code = metric_source()
    (output / "scoring/metric.py").write_text(code)
    save_json(output / "scoring/metric.ipynb", notebook([
        ("markdown", "# MetroCore metric\nHigher is better. Range [-0.5, 1]. This notebook contains no answer keys. Register it as a custom metric; test on Kaggle before launch."),
        ("code", code)]))
    intro = """# MetroCore Decision Desk — starter notebook

Implement `solve(question, image_path)`. Five examples are available in interactive
sessions. During an enabled hidden rerun, the same input paths contain the hidden
set. Never assume the public example IDs or row count. No reference answers are
mounted during hidden inference.

Return a finite number, `"na"` if infeasible, or `None`/`"skip"` to abstain.
The final cell writes `/kaggle/working/submission.csv` with `problem_id,answer`.
`skip` scores zero and avoids empty CSV cells; it is not an infeasibility claim.
Only literal `na` means infeasible. This starter returns None everywhere and is
an interface example, not a solving baseline.

Use permitted offline model weights and packages already attached as inputs.
Load models once before inference. Hidden inputs and output logs must stay private.
"""
    setup = '''import os
import sys
from pathlib import Path

# Replace the slug after the competition is created. For local testing set
# METROCORE_INPUT_DIR to release/public or release/private_rerun.
INPUT_DIR = Path(os.environ.get("METROCORE_INPUT_DIR", "/kaggle/input/metrocore-decision-desk")).resolve()
OUTPUT_PATH = Path(os.environ.get("METROCORE_OUTPUT_PATH", "/kaggle/working/submission.csv"))
if not (INPUT_DIR / "problems.json").is_file():
    raise FileNotFoundError("Set INPUT_DIR to the mounted competition bundle")
sys.path.insert(0, str(INPUT_DIR))
from submission_runner import run_submission
'''
    solve = '''def solve(question: str, image_path: str | None = None) -> float | str | None:
    # TODO: extract facts, formulate the optimization problem, and solve it.
    # image_path is absolute, or None for text-only questions.
    return None
'''
    run = '''run_submission(solve, INPUT_DIR / "problems.json", OUTPUT_PATH, missing_answer="skip")
print("Submission written.")
'''
    save_json(output / "starter/metrocore_starter.ipynb", notebook([
        ("markdown", intro), ("code", setup),
        ("markdown", "## Model setup\nLoad models and offline dependencies here."),
        ("code", "# Your model setup goes here.\n"), ("code", solve),
        ("markdown", "## Generate submission\nCaught per-problem exceptions become skip. Fatal runtime failures may invalidate the whole Kaggle submission."), ("code", run)]))
    for name in ["overview.md", "evaluation.md", "data.md", "rules.md", "ENVIRONMENT.md", "PUBLIC_README.md"]:
        src = ROOT / "release_templates" / name
        if src.exists():
            dest = output / "public" / ("README.md" if name == "PUBLIC_README.md" else name) if name in {"ENVIRONMENT.md", "PUBLIC_README.md"} else output / "pages" / name
            shutil.copyfile(src, dest)
    example_map = [{"example_id": id_mapping[p["problem_id"]], "original_id": p["problem_id"],
                    "source_row_1based": manifest[p["problem_id"]]["source_row_1based"],
                    "modality": "image" if p["image_path"] else "text"} for p in chosen]
    config = {"example_seed": example_seed, "split_seed": split_seed, "examples": example_map,
              "source_total": len(problems), "hidden_total": len(hidden),
              "hidden_image": sum(bool(p["image_path"]) for p in hidden),
              "hidden_text": sum(not p["image_path"] for p in hidden),
              "leaderboard_public": len(feedback_ids), "leaderboard_private": len(hidden)-len(feedback_ids),
              "leaderboard_split_status": "proposed 30/70; confirm before launch",
              "kaggle_deployed": False, "hosted_validation_complete": False}
    save_json(output / "organizer/release_manifest.json", config)
    with (dataset / "organizer/reference_review.csv").open() as f:
        reviews = list(csv.DictReader(f))
    save_csv(output / "organizer/reference_review.csv", [*reviews[0], "partition"],
             ([*r.values(), "example" if r["problem_id"] in example_ids else "hidden"] for r in reviews))
    cards = []
    for p, original in zip(examples, chosen):
        picture = f'<img src="{p["image_path"]}" alt="Attached data sheet">' if p["image_path"] else ""
        cards.append(f'<article><h2>{p["problem_id"]} — {"Multimodal" if picture else "Text-only"}</h2><p>{html.escape(p["question"])}</p>{picture}<p><strong>Source reference answer:</strong> {html.escape(refs[original["problem_id"]]["reference_answer"])}</p></article>')
    (output / "public/examples.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MetroCore examples</title><style>body{font:18px system-ui;max-width:1100px;margin:30px auto;padding:20px;background:#f1f4f5}article{padding:24px;margin:20px 0;background:white;border:1px solid #ccd5da;border-radius:10px}p{line-height:1.6;white-space:pre-line}img{width:100%;height:auto}</style><h1>Five public examples</h1>' + ''.join(cards) + '</html>', encoding="utf-8")
    hashes = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(output.rglob("*")) if p.is_file()}
    save_json(output / "organizer/file_hashes.json", hashes)
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets/nl4opt_mm_v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.dataset, args.output), indent=2))
