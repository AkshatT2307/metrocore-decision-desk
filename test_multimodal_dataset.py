"""Validate the released derivative against its original source, not its labels' correctness."""

import hashlib
import json
import random
import re
import tempfile
import unittest
from pathlib import Path

from PIL import Image

import evaluator
from build_multimodal_dataset import ATTACHMENT_NOTE, render_document, transform
from submission_runner import load_inputs


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "datasets" / "nl4opt_mm_v1"


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = [json.loads(line) for line in (ROOT / "nl4opt_test.json").read_text().splitlines()]
        cls.inputs = json.loads((DATA / "inference" / "problems.json").read_text())
        cls.references = evaluator.load_test_set(DATA / "organizer" / "hidden_test_set.json")
        cls.manifest = [json.loads(line) for line in (DATA / "organizer" / "manifest.jsonl").read_text().splitlines()]
        cls.config = json.loads((DATA / "organizer" / "build_manifest.json").read_text())

    def test_counts_uniqueness_and_reproducible_selection(self):
        self.assertEqual(len(self.inputs), 245)
        self.assertEqual(len({p["problem_id"] for p in self.inputs}), 245)
        self.assertEqual(sum(p["image_path"] is not None for p in self.inputs), 100)
        self.assertEqual({m["source_row_1based"] for m in self.manifest}, set(range(1, 246)))
        selected = {m["source_row_1based"] - 1 for m in self.manifest if m["modality"] == "image"}
        self.assertEqual(selected, set(random.Random(20261107).sample(range(245), 100)))
        self.assertEqual(hashlib.sha256((ROOT / "nl4opt_test.json").read_bytes()).hexdigest(), self.config["source_sha256"])

    def test_complete_source_text_and_answers_are_preserved(self):
        by_id = {p["problem_id"]: p for p in self.inputs}
        refs = {p["problem_id"]: p for p in self.references}
        for record in self.manifest:
            with self.subTest(problem_id=record["problem_id"]):
                source = self.source[record["source_row_1based"] - 1]
                problem = by_id[record["problem_id"]]
                self.assertEqual(record["source_question"], source["en_question"])
                self.assertEqual(record["source_answer"], source["en_answer"])
                expected = "na" if source["en_answer"] in {"No Best Solution", "-99999.0"} else source["en_answer"]
                self.assertEqual(refs[record["problem_id"]]["reference_answer"], expected)
                if problem["image_path"] is None:
                    self.assertEqual(problem["question"], source["en_question"])
                    continue
                statements = record["source_statements"]
                self.assertEqual(" ".join(" ".join(statements).split()), " ".join(source["en_question"].split()))
                moved = record["moved_statement_indices"]
                self.assertEqual(record["rendered_statements"], [statements[i] for i in moved])
                self.assertRegex(" ".join(record["rendered_statements"]), r"\d")
                kept = [s for i, s in enumerate(statements) if i not in moved]
                self.assertEqual(problem["question"], " ".join(kept) + "\n\n" + ATTACHMENT_NOTE)
                for statement in record["rendered_statements"]:
                    self.assertNotIn(statement, " ".join(kept))

    def test_all_pngs_decode_without_text_metadata(self):
        by_id = {p["problem_id"]: p for p in self.inputs}
        for record in self.manifest:
            if record["modality"] != "image":
                continue
            path = DATA / "inference" / by_id[record["problem_id"]]["image_path"]
            with self.subTest(path=path), Image.open(path) as image:
                image.load()
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (record["image"]["width"], record["image"]["height"]))
                self.assertEqual(image.info, {})
                self.assertTrue(record["image"]["all_body_text_inside_cells"])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["image"]["sha256"])

    def test_inference_bundle_has_only_inputs_images_and_runner(self):
        allowed = {"problems.json", "submission_runner.py"}
        allowed.update(p["image_path"] for p in self.inputs if p["image_path"])
        actual = {str(p.relative_to(DATA / "inference")) for p in (DATA / "inference").rglob("*") if p.is_file()}
        self.assertEqual(actual, allowed)
        self.assertEqual(len(load_inputs(DATA / "inference" / "problems.json")), 245)
        for p in self.inputs:
            self.assertEqual(set(p), {"problem_id", "question", "image_path"})

    def test_new_dataset_scoring_and_class_coverage(self):
        perfect = {r["problem_id"]: r["reference_answer"] for r in self.references}
        self.assertEqual(evaluator.evaluate(perfect, self.references)["mean_score"], 1)
        self.assertEqual(evaluator.evaluate({}, self.references)["mean_score"], 0)
        na = {r["problem_id"] for r in self.references if r["reference_answer"] == "na"}
        self.assertEqual(len(na), 20)
        self.assertEqual(sum(p["problem_id"] in na for p in self.inputs if p["image_path"]), 6)

    def test_render_is_reproducible(self):
        record = next(m for m in self.manifest if m["modality"] == "image")
        with tempfile.TemporaryDirectory() as directory:
            info = render_document(record["source_question"], record["rendered_statements"],
                                   Path(directory) / "repeat.png", Path("/usr/share/fonts/truetype/dejavu"),
                                   record["image"]["style"])
            self.assertEqual(info["sha256"], record["image"]["sha256"])

    def test_decimal_and_word_quantities_survive(self):
        q = "Mr. Roberts owns a shop. Each item takes 1.5 hours and costs $2.50. At least twice as many small items are required. How many should he make to maximize profit?"
        prompt, statements, moved = transform(q)
        self.assertTrue(statements[0].startswith("Mr. Roberts"))
        self.assertEqual(len(moved), 2)
        self.assertIn("1.5 hours", " ".join(statements[i] for i in moved))
        self.assertIn("twice", " ".join(statements[i] for i in moved))
        self.assertIn("maximize profit", prompt)


if __name__ == "__main__":
    unittest.main()
