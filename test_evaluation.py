"""Regression checks for scoring, input separation, and partial submissions."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import evaluator
from submission_runner import load_inputs, run_submission


class EvaluationTests(unittest.TestCase):
    def test_score_contract(self):
        cases = [
            (100, 100, 1, "correct"), (101, 100, 1, "correct"),
            (105, 100, .5, "close"), (106, 100, 0, "wrong"),
            (1.01, 1, 1, "correct"), (1.05, 1, .5, "close"),
            (-101, -100, 1, "correct"), (.01, 0, 1, "correct"),
            (.05, 0, .5, "close"), ("na", "na", 1, "correct_na"),
            ("na", 100, -.5, "na_on_feasible"),
            (100, "na", -.5, "number_on_infeasible"),
            (-99999, -99999, 1, "correct"),
            ("-99999.0", "-99999", 1, "correct"),
        ]
        for sub, ref, score, reason in cases:
            with self.subTest(sub=sub, ref=ref):
                self.assertEqual(evaluator.score_one(sub, ref), (score, reason))

    def test_missing_and_invalid_are_not_infeasible(self):
        for ref in [100, "na"]:
            for value in [None, "", "  "]:
                self.assertEqual(evaluator.score_one(value, ref), (0, "missing"))
            for value in ["garbage", "None", "No Best Solution", "NaN", "inf", "-inf", True]:
                self.assertEqual(evaluator.score_one(value, ref), (0, "invalid"))

    def test_invalid_reference_fails(self):
        for reference in [None, "", "garbage", "nan", "inf"]:
            with self.assertRaises(ValueError):
                evaluator.score_one(0, reference)

    def test_mean_uses_all_reference_rows(self):
        reference = [{"problem_id": "a", "reference_answer": 100},
                     {"problem_id": "b", "reference_answer": "na"}]
        self.assertEqual(evaluator.evaluate({"a": 100}, reference)["mean_score"], .5)
        self.assertEqual(evaluator.evaluate({}, reference)["mean_score"], 0)
        with self.assertRaises(ValueError):
            evaluator.evaluate({"extra": 0}, reference)
        with self.assertRaises(ValueError):
            evaluator.evaluate({}, reference + reference)
        with self.assertRaises(ValueError):
            evaluator.evaluate({}, [])

    def test_csv_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "submission.csv"
            invalid = ["id,answer\na,1\n", "problem_id,answer\na,1\na,2\n",
                       "problem_id,answer\na\n", "problem_id,answer\na,1,2\n",
                       "problem_id,answer\n,1\n"]
            for content in invalid:
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    evaluator.load_submission(path)
            path.write_text("\ufeffproblem_id,answer\na,\nb,na\n")
            self.assertEqual(evaluator.load_submission(path), {"a": "", "b": "na"})


class RunnerTests(unittest.TestCase):
    def test_image_resolution_and_crash_scoring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "image.png").write_bytes(b"test fixture; solver does not decode")
            inputs = [{"problem_id": "a", "question": "image", "image_path": "image.png"},
                      {"problem_id": "b", "question": "crash", "image_path": None},
                      {"problem_id": "c", "question": "none", "image_path": None}]
            path = root / "problems.json"
            path.write_text(json.dumps(inputs))
            output = root / "submission.csv"

            def solve(question, image):
                if question == "image":
                    self.assertEqual(image, str(root / "image.png"))
                    return 100
                if question == "crash":
                    raise RuntimeError("synthetic failure")
                return None

            with contextlib.redirect_stdout(io.StringIO()):
                run_submission(solve, path, output)
            sub = evaluator.load_submission(output)
            self.assertEqual(sub, {"a": "100", "b": "", "c": ""})
            refs = [{"problem_id": "a", "reference_answer": 100},
                    {"problem_id": "b", "reference_answer": "na"},
                    {"problem_id": "c", "reference_answer": 100}]
            self.assertEqual(evaluator.evaluate(sub, refs)["mean_score"], 1 / 3)

    def test_checkpoint_survives_process_level_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "problems.json"
            path.write_text(json.dumps([{"problem_id": "a", "question": "first"},
                                        {"problem_id": "b", "question": "exit"}]))

            def solve(question, image):
                if question == "exit":
                    raise SystemExit(1)
                return 7

            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                run_submission(solve, path, root / "submission.csv")
            self.assertEqual(evaluator.load_submission(root / "submission.csv"), {"a": "7", "b": ""})

    def test_reject_reference_data_and_bad_image_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "problems.json"
            for extra in [{"reference_answer": 7}, {"image_path": "../outside.png"},
                          {"image_path": "/tmp/image.png"}, {"image_path": "missing.png"}]:
                path.write_text(json.dumps([dict(problem_id="a", question="q", **extra)]))
                with self.subTest(extra=extra), self.assertRaises(ValueError):
                    load_inputs(path)

    def test_notebook_runner_cell(self):
        # Exercise the distributed notebook's integration with the public runner.
        nb = json.loads(Path(__file__).with_name("evaluation_notebook.ipynb").read_text())
        code = "".join(nb["cells"][-1]["source"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "problems.json").write_text(json.dumps([{"problem_id": "demo", "question": "q"}]))
            import os
            from unittest.mock import patch
            env = {"METROCORE_INPUT_DIR": str(root), "METROCORE_OUTPUT_PATH": str(root / "out.csv")}
            with patch.dict(os.environ, env), contextlib.redirect_stdout(io.StringIO()):
                exec(compile(code, "notebook runner", "exec"), {"solve": lambda q, p: 7})
            self.assertEqual(evaluator.load_submission(root / "out.csv"), {"demo": "7"})


if __name__ == "__main__":
    unittest.main()
