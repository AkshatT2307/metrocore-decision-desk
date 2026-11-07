"""Local release smoke tests; these do not substitute for a Kaggle hidden rerun."""

import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import evaluator

ROOT = Path(__file__).resolve().parent
RELEASE = ROOT / "releases/kaggle_v1"


def metric_module():
    spec = importlib.util.spec_from_file_location("release_metric", RELEASE / "scoring/metric.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseTests(unittest.TestCase):
    def test_public_and_hidden_sources_are_disjoint(self):
        public = json.loads((RELEASE / "public/problems.json").read_text())
        hidden = json.loads((RELEASE / "private_rerun/problems.json").read_text())
        config = json.loads((RELEASE / "organizer/release_manifest.json").read_text())
        self.assertEqual((len(public), sum(bool(p['image_path']) for p in public)), (5, 2))
        self.assertEqual((len(hidden), sum(bool(p['image_path']) for p in hidden)), (240, 98))
        source_ids = {r['original_id'] for r in config['examples']}
        hidden_ids = {p['problem_id'] for p in hidden}
        self.assertFalse(source_ids & hidden_ids)
        self.assertEqual(len(source_ids | hidden_ids), 245)
        answers = pd.read_csv(RELEASE / "public/example_answers.csv", keep_default_na=False)
        self.assertEqual(set(answers.problem_id), {p['problem_id'] for p in public})

    def test_private_bundle_contains_no_reference_files(self):
        hidden = json.loads((RELEASE / "private_rerun/problems.json").read_text())
        allowed = {'problems.json', 'sample_submission.csv', 'submission_runner.py'}
        allowed.update(p['image_path'] for p in hidden if p['image_path'])
        actual = {str(p.relative_to(RELEASE / 'private_rerun')) for p in (RELEASE / 'private_rerun').rglob('*') if p.is_file()}
        self.assertEqual(actual, allowed)
        for p in hidden:
            self.assertEqual(set(p), {'problem_id', 'question', 'image_path'})
        public = RELEASE / 'public'
        self.assertEqual(len(list((public / 'images').glob('*.png'))), 2)
        self.assertFalse((public / 'solution.csv').exists())
        self.assertFalse((public / 'reference_review.csv').exists())

    def test_release_hashes_and_image_paths(self):
        hashes = json.loads((RELEASE / 'organizer/file_hashes.json').read_text())
        for relative, expected in hashes.items():
            self.assertEqual(hashlib.sha256((RELEASE / relative).read_bytes()).hexdigest(), expected, relative)
        for directory in ['public', 'private_rerun']:
            for p in json.loads((RELEASE / directory / 'problems.json').read_text()):
                if p['image_path']:
                    self.assertTrue((RELEASE / directory / p['image_path']).is_file())

    def test_starter_runs_on_both_bundles(self):
        nb = json.loads((RELEASE / 'starter/metrocore_starter.ipynb').read_text())
        code = '\n\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code')
        for directory, count in [('public', 5), ('private_rerun', 240)]:
            with tempfile.TemporaryDirectory() as temporary:
                out = Path(temporary) / 'submission.csv'
                env = dict(os.environ, METROCORE_INPUT_DIR=str(RELEASE / directory),
                           METROCORE_OUTPUT_PATH=str(out))
                run = subprocess.run([sys.executable, '-B', '-c', code], env=env,
                                     capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)
                result = evaluator.load_submission(out)
                self.assertEqual(len(result), count)
                self.assertEqual(set(result.values()), {'skip'})


class MetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metric = metric_module()

    def test_default_pandas_csv_preserves_na_and_skip(self):
        # Verify the parser behavior we can test locally; Kaggle validation is separate.
        frame = pd.read_csv(io.StringIO('problem_id,answer\na,na\nb,skip\nc,1.05\n'))
        self.assertEqual(frame.answer.tolist(), ['na', 'skip', '1.05'])

    def test_perfect_shuffled_and_partition_scores(self):
        solution = pd.read_csv(RELEASE / 'scoring/solution.csv')
        submission = pd.read_csv(RELEASE / 'scoring/perfect_submission.csv')
        self.assertEqual(self.metric.score(solution, submission.iloc[::-1], 'problem_id'), 1.0)
        self.assertEqual(solution.Usage.value_counts().to_dict(), {'Private': 168, 'Public': 72})
        for usage in ['Public', 'Private']:
            part = solution[solution.Usage == usage]
            pred = submission[submission.problem_id.isin(part.problem_id)]
            self.assertEqual(self.metric.score(part, pred, 'problem_id'), 1)

    def test_parity_on_numeric_na_missing_and_invalid(self):
        references = [100, -100, 0, 1, 'na']
        values = [100, 101, 105, 106, -101, 0, .01, .05, 1.01, 1.05, 'na', 'skip', '', None, 'garbage', 'inf', 'nan']
        for ref in references:
            solution = pd.DataFrame({'problem_id': ['a'], 'answer': [ref]})
            for value in values:
                pred = pd.DataFrame({'problem_id': ['a'], 'answer': [value]})
                with self.subTest(reference=ref, value=value):
                    self.assertEqual(self.metric.score(solution, pred, 'problem_id'), evaluator.score_one(value, ref)[0])

    def test_structural_errors_and_reference_parse_failure(self):
        solution = pd.DataFrame({'problem_id': ['a', 'b'], 'answer': [1, 'na']})
        invalid = [pd.DataFrame({'problem_id': ['a', 'a'], 'answer': [1, 1]}),
                   pd.DataFrame({'problem_id': ['a'], 'answer': [1]}),
                   pd.DataFrame({'problem_id': ['a', 'x'], 'answer': [1, 1]}),
                   pd.DataFrame({'problem_id': ['a', 'b'], 'answer': [1, 1], 'extra': [0, 0]})]
        for pred in invalid:
            with self.assertRaises(self.metric.ParticipantVisibleError):
                self.metric.score(solution, pred, 'problem_id')
        bad_solution = pd.DataFrame({'problem_id': ['a'], 'answer': [float('nan')]})
        with self.assertRaises(ValueError):
            self.metric.score(bad_solution, pd.DataFrame({'problem_id': ['a'], 'answer': ['na']}), 'problem_id')

    def test_generated_notebook_is_standalone(self):
        nb = json.loads((RELEASE / 'scoring/metric.ipynb').read_text())
        namespace = {}
        code = '\n\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code')
        exec(compile(code, 'metric notebook', 'exec'), namespace)
        solution = pd.DataFrame({'problem_id': ['a'], 'answer': ['na']})
        self.assertEqual(namespace['score'](solution, solution.copy(), 'problem_id'), 1)


if __name__ == '__main__':
    unittest.main()
