"""Build an auditable NL4Opt multimodal derivative without rewriting facts.

Requires Pillow==11.3.0 for deterministic document rendering. The 100 selected
questions move complete numerical source statements into data-sheet images.
Source answers are preserved except for explicit legacy sentinel normalization.
"""

import argparse
import csv
import hashlib
import html
import json
import math
import random
import re
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


VERSION = "nl4opt-mm-v1"
QUANTITY = re.compile(r"\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|half|third|quarter|twice|thrice)\b", re.I)
GOAL = re.compile(r"\b(?:minimi[sz]e|maximi[sz]e|minimum cost|maximum profit|how many|how much|determine|formulate|find)\b", re.I)
SENTINEL_MAP = {"No Best Solution": "na", "-99999.0": "na"}
# Recorded counterexamples from the earlier audit; labels remain unchanged.
KNOWN_REVIEW = {
    16: "Integer vehicle shifts: 10 ambulance + 8 van shifts cost 12600, below source 12860.",
    37: "Feasible witness: 27 small + 9 large bins use 99 workers; source says No Best Solution.",
    164: "Integer shifts: 54 cart + 3 hand shifts give 4035 interactions and 330 refills; source is 95.",
    179: "11 motion + 6 manual machines meet requirements with 17 machines; source is 18.",
    215: "Feasible witness: 7 large + 9 small planes carry 300 cars with fewer large planes.",
}
ATTACHMENT_NOTE = (
    "The attached data sheet contains additional specifications and requirements. "
    "Use every statement in that sheet together with the information above. "
    "Return only the optimal objective value, or na if the problem is infeasible."
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_statements(question: str) -> list[str]:
    """Keep decimal points intact and avoid splitting common abbreviations."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", question.strip())
    merged = []
    for part in parts:
        if merged and re.search(r"\b(?:Mr|Mrs|Ms|Dr|sq)\.$", merged[-1]):
            merged[-1] += " " + part
        else:
            merged.append(part)
    return merged


def transform(question: str) -> tuple[str, list[str], list[int]]:
    statements = split_statements(question)
    # Leave scenario introduction and the complete objective in text. Moving
    # whole statements avoids losing comparators, units, or numeric precision.
    moved = [i for i, text in enumerate(statements)
             if i > 0 and QUANTITY.search(text) and not GOAL.search(text)]
    for i, text in enumerate(statements):
        if text.startswith("(") and i - 1 in moved and i not in moved:
            moved.append(i)
    moved.sort()
    if not moved or not any(re.search(r"\d", statements[i]) for i in moved):
        raise ValueError("Selected question has no suitable numerical statement to move")
    remaining = [text for i, text in enumerate(statements) if i not in moved]
    if not any(GOAL.search(text) for text in remaining):
        raise ValueError("Objective must remain in participant text")
    return " ".join(remaining) + "\n\n" + ATTACHMENT_NOTE, statements, moved


def normalize_answer(raw: str) -> str:
    if raw in SENTINEL_MAP:
        return SENTINEL_MAP[raw]
    if not math.isfinite(float(raw)):
        raise ValueError("Unexpected nonfinite source answer")
    return raw


def document_title(question: str) -> str:
    q = question.lower()
    if re.search(r"pill|medicin|vaccine|syrup|painkiller|swab", q):
        return "Clinical operations data sheet"
    if re.search(r"calori|vitamin|diet|protein|nutrition", q):
        return "Nutrition and ingredient specifications"
    if re.search(r"transport|deliver|ship|fleet|trip|vehicle|plane|boat", q):
        return "Transport operations data sheet"
    if re.search(r"farm|crop|acre|hectare|fertilizer|orchard", q):
        return "Agricultural operations record"
    if re.search(r"invest|advertis|commercial|subscription", q):
        return "Planning and allocation data sheet"
    if re.search(r"factory|manufactur|produc|machine|assembl|company", q):
        return "Production and resource specifications"
    return "Operating specifications and requirements"


def category(statement: str) -> str:
    s = statement.lower()
    if re.search(r"at least|at most|minimum|maximum|no more than|must|limits|limited", s):
        return "Requirement"
    if re.search(r"available|budget|stock|total", s):
        return "Resources"
    if re.search(r"cost|profit|paid|earn|revenue", s):
        return "Cost / return"
    return "Specification"


def wrap(draw, text, font, width):
    lines = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= width:
            line = candidate
        else:
            if not line or draw.textlength(word, font=font) > width:
                raise ValueError("Unwrappable word would be clipped")
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def render_document(question, rows, destination, font_dir, style):
    palettes = [("#193C4B", "#EEF4F5"), ("#294536", "#F0F4EF"),
                ("#3D3654", "#F3F1F7"), ("#51402B", "#F7F3EC")]
    accent, alternate = palettes[style % len(palettes)]
    width, margin, label_width = 1440, 70, 230
    normal = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 29)
    small = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 23)
    bold = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 25)
    title_font = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 40)
    draw = ImageDraw.Draw(Image.new("RGB", (width, 1)))
    title_lines = wrap(draw, document_title(question), title_font, width - 2 * margin)
    top = 108 + 54 * len(title_lines) + 78
    text_x = margin + label_width + 25
    text_width = width - margin - 26 - text_x
    prepared = []
    for statement in rows:
        lines = wrap(draw, statement, normal, text_width)
        prepared.append((statement, lines, max(85, 46 * len(lines) + 40)))
    height = top + 54 + sum(row[2] for row in prepared) + 105
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 14), fill=accent)
    draw.text((margin, 47), "OPERATIONS  /  REFERENCE SHEET", font=small, fill=accent)
    for index, line in enumerate(title_lines):
        draw.text((margin, 96 + 54 * index), line, font=title_font, fill="#172126")
    draw.text((margin, top - 52), "Read with the accompanying problem statement.", font=small, fill="#53616A")
    draw.rectangle((margin, top, width - margin, top + 54), fill=accent)
    draw.text((margin + 22, top + 10), "Section", font=bold, fill="white")
    draw.text((text_x, top + 10), "Recorded specification or requirement", font=bold, fill="white")
    y = top + 54
    boxes = []
    for index, (statement, lines, row_height) in enumerate(prepared):
        draw.rectangle((margin, y, width - margin, y + row_height), fill=alternate if index % 2 == 0 else "#FFFFFF")
        draw.line((margin, y + row_height, width - margin, y + row_height), fill="#CAD3D8", width=1)
        label_lines = wrap(draw, category(statement), small, label_width - 38)
        for j, line in enumerate(label_lines):
            draw.text((margin + 20, y + 23 + j * 34), line, font=small, fill=accent)
        for j, line in enumerate(lines):
            xy = (text_x, y + 19 + j * 46)
            bbox = draw.textbbox(xy, line, font=normal)
            if not (margin <= bbox[0] < bbox[2] <= width - margin and y <= bbox[1] < bbox[3] <= y + row_height):
                raise ValueError("Text extends outside its table cell")
            boxes.append(bbox)
            draw.text(xy, line, font=normal, fill="#182329")
        y += row_height
    draw.line((margin + label_width, top + 54, margin + label_width, y), fill="#CAD3D8", width=1)
    draw.text((margin, y + 34), "Values, units and qualifying conditions apply as written.", font=small, fill="#53616A")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=False)
    return {"width": width, "height": height, "body_font_px": 29,
            "rendered_line_count": len(boxes), "all_body_text_inside_cells": True,
            "sha256": digest(destination.read_bytes()), "style": style % len(palettes)}


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(source, output, count=100, seed=20261107,
          font_dir=Path("/usr/share/fonts/truetype/dejavu")):
    source, output, font_dir = Path(source), Path(output), Path(font_dir)
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    if not 0 <= count <= len(rows):
        raise ValueError("Multimodal count must be between zero and source count")
    if output.exists():
        raise ValueError("Output already exists; choose a fresh version directory")
    for name in ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]:
        if not (font_dir / name).is_file():
            raise ValueError(f"Missing rendering font: {name}")
    if len({r["en_question"] for r in rows}) != len(rows):
        raise ValueError("Duplicate source questions require review")
    selected = set(random.Random(seed).sample(range(len(rows)), count))
    transformed = {i: transform(rows[i]["en_question"]) for i in selected}
    # Independently shuffle IDs/order so they do not expose source row numbers.
    order = list(range(len(rows)))
    random.Random(seed + 1).shuffle(order)
    inference = output / "inference"
    organizer = output / "organizer"
    inference.mkdir(parents=True)
    organizer.mkdir()
    problems, references, manifest = [], [], []
    for index, source_index in enumerate(order, start=1):
        row = rows[source_index]
        question, raw_answer = row["en_question"], row["en_answer"]
        pid = f"MM-{index:04d}"
        answer = normalize_answer(raw_answer)
        image_path = None
        record = {"problem_id": pid, "source_row_1based": source_index + 1,
                  "source_question": question, "source_answer": raw_answer,
                  "reference_answer": answer, "source_question_sha256": digest(question.encode()),
                  "answer_policy": "legacy_sentinel_to_na_unverified" if raw_answer in SENTINEL_MAP else "source_unchanged",
                  "modality": "image" if source_index in selected else "text"}
        if source_index in selected:
            prompt, statements, moved = transformed[source_index]
            image_path = f"images/{pid.lower()}.png"
            image_info = render_document(question, [statements[i] for i in moved], inference / image_path, font_dir, index)
            record.update(source_statements=statements, moved_statement_indices=moved,
                          rendered_statements=[statements[i] for i in moved], image=image_info)
        else:
            prompt = question
        problem = {"problem_id": pid, "question": prompt, "image_path": image_path}
        problems.append(problem)
        # These paths are relative to the organizer reference file, for inspection.
        references.append(dict(problem, reference_answer=answer,
                               image_path=f"../inference/{image_path}" if image_path else None))
        record["participant_question_sha256"] = digest(prompt.encode())
        manifest.append(record)
    write_json(inference / "problems.json", problems)
    shutil.copyfile(Path(__file__).with_name("submission_runner.py"), inference / "submission_runner.py")
    write_json(organizer / "hidden_test_set.json", references)
    with (organizer / "reference_answers.csv").open("w", newline="") as f:
        writer = csv.writer(f); writer.writerow(["problem_id", "answer"])
        writer.writerows((p["problem_id"], p["reference_answer"]) for p in references)
    with (organizer / "manifest.jsonl").open("w", encoding="utf-8") as f:
        for entry in manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    with (organizer / "reference_review.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["problem_id", "source_row_1based", "source_answer", "reference_answer", "review_reason", "label_changed"])
        for record in manifest:
            row_number = record["source_row_1based"]
            reason = KNOWN_REVIEW.get(row_number)
            if record["source_answer"] in SENTINEL_MAP:
                reason = (reason + " " if reason else "") + "Legacy source marker mapped to na; infeasibility not independently certified."
            if reason:
                writer.writerow([record["problem_id"], row_number, record["source_answer"], record["reference_answer"], reason, "false"])
    counts = Counter((m["modality"], m["reference_answer"] == "na") for m in manifest)
    summary = {"version": VERSION, "source_file": source.name,
               "source_sha256": digest(source.read_bytes()), "seed": seed,
               "selection_method": "uniform random sample without replacement",
               "id_shuffle_seed": seed + 1, "total": len(rows), "multimodal": count,
               "text_only": len(rows) - count, "source_na_mappings": SENTINEL_MAP,
               "image_numeric": counts[("image", False)], "image_na": counts[("image", True)],
               "text_numeric": counts[("text", False)], "text_na": counts[("text", True)],
               "pillow_version": pillow_version,
               "font_sha256": {name: digest((font_dir / name).read_bytes()) for name in ["DejaVuSans.ttf", "DejaVuSans-Bold.ttf"]},
               "source_labels_independently_certified": False,
               "public_examples_reserved": False,
               "leaderboard_split_assigned": False}
    write_json(organizer / "build_manifest.json", summary)
    cards = []
    for problem, record in zip(problems, manifest):
        if problem["image_path"]:
            cards.append(f'<article><h2>{html.escape(problem["problem_id"])}</h2><p>{html.escape(problem["question"])}</p><img loading="lazy" src="../inference/{problem["image_path"]}" alt="Data sheet"><details><summary>Organizer provenance and reference</summary><pre>{html.escape(json.dumps(record,ensure_ascii=False,indent=2))}</pre></details></article>')
    (organizer / "review.html").write_text('<!doctype html><meta charset="utf-8"><title>Multimodal organizer review</title><style>body{font:18px system-ui;background:#eef2f3;margin:32px auto;max-width:1100px}article{padding:28px;background:white;margin:24px 0;border:1px solid #ccd5d9;border-radius:10px}img{width:100%;height:auto}p{line-height:1.6;white-space:pre-line}pre{white-space:pre-wrap;font-size:14px}details{margin-top:20px}</style><h1>Organizer-only multimodal review</h1><p>Contains source questions and answers. Do not publish.</p>' + "\n".join(cards), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).with_name("nl4opt_test.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--multimodal-count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261107)
    parser.add_argument("--font-dir", type=Path, default=Path("/usr/share/fonts/truetype/dejavu"))
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output, args.multimodal_count, args.seed, args.font_dir), indent=2))
