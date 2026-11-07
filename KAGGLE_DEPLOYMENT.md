# MetroCore — Kaggle deployment and teammate handoff

Prepared 7 November 2026. This is a locally tested release candidate. Nothing has
been uploaded. The remaining launch requirements are listed below.

## Repository handoff

This is the private organizer repository. It includes the source snapshot,
constructed dataset, hidden inputs, answer keys, release builders, scoring code,
tests, starter notebook, and promotional HTML. Keep this repository private and
grant your teammate access through GitHub **Settings > Collaborators**. Do not
publish the repository through GitHub Pages or attach it to participant notebooks.
Pushing to GitHub does not deploy the Kaggle competition.

Run all commands in this guide from the repository root (the directory containing
`evaluator.py` and this file). Paths in the destination table below are relative
to `releases/kaggle_v1/`; shell commands use repository-relative paths.

Start with these files:

| File or directory | Purpose |
|---|---|
| `evaluator.py`, `kaggle_metric_adapter.py` | Organizer scorer and Kaggle DataFrame adapter |
| `submission_runner.py` | Input-only participant loop and checkpointing |
| `build_multimodal_dataset.py` | Reproducible 245-row dataset construction |
| `prepare_kaggle_release.py` | Disjoint examples, hidden inputs, metric, and starter builder |
| `datasets/nl4opt_mm_v1/README.md` | Dataset design and provenance |
| `datasets/nl4opt_mm_v1/organizer/review.html` | Visual review of all 100 image conversions |
| `releases/kaggle_v1/` | Current deployment candidate; use this starter and these bundles |
| `release_templates/` | Editable source for generated public documentation |
| `test_*.py` | Local regression tests |
| `metrocore-decision-desk.html`, `poster.html`, `ps.md` | Promotional/event material needing final alignment |

The root `hidden_test_set.json`, `test_images/`, and `evaluation_notebook.ipynb`
are earlier materials retained for context. The current release uses the files
under `releases/kaggle_v1/`, not the earlier 50-row answer key or root notebook.

## What is ready

- Five random public examples: **2 image+text, 3 text-only**.
- Disjoint hidden set: **240 problems, 98 image+text and 142 text-only**.
- Participant starter notebook and checkpointing runner.
- Standalone custom metric in Python and notebook formats.
- Private answer key and a proposed stratified **72 Public / 168 Private**
  leaderboard assignment. Both partitions' questions remain hidden.
- Public description/evaluation/data pages and a rules draft.

## What prevents launch today

1. **Kaggle must enable the hidden rerun workflow.** Its official CLI currently
   says the RERUN upload requires Kaggle admin access. Creating an ordinary
   Community competition and uploading a private answer key is insufficient.
2. **The real Kaggle validation/scoring path must pass a smoke test**, including
   mixed numeric/`na`/`skip` answers and the 5-row versus 240-row replacement.
3. **Hardware, runtime, event dates, prizes, and final rules need configuration.**
   The included environment file is explicitly a draft.
4. **Source-reference disputes remain.** The preserved labels are in the release;
   `organizer/reference_review.csv` identifies flagged cases. They have not been
   silently corrected or removed. Resolve the prize-scoring policy before launch.

## Remaining work — teammate checklist

- [ ] Create a Kaggle draft and record its URL/slug; no competition exists yet.
- [ ] Obtain hidden Code Competition rerun capability from Kaggle (Step 2).
- [ ] Review the 23 flagged source records, including all 20 legacy `na` markers.
      Record the decision and rebuild/version the release if references or rows change.
- [ ] Record the origin/version and applicable reuse terms of the bundled
      question/numeric-answer export; the local filename alone is not provenance.
- [ ] Confirm the proposed 72/168 leaderboard split and the metric policy below.
- [ ] Select hardware, memory, runtime and offline dependencies; benchmark a real
      solver on the full hidden input set. Finalize the draft environment file.
- [ ] Finalize dates, prizes, teams, submissions/day, tie handling, report weight,
      allowed external data/models and how the 7B parameter limit is interpreted.
- [ ] Configure and validate the private bundles, answer key and custom metric.
- [ ] Set the starter's actual input mount and verify 5-row/240-row replacement.
- [ ] Complete every hosted smoke test in Step 7; retain host-only evidence.
- [ ] Align `ps.md` and both HTML files with the released dataset and rules;
      remove unsupported scale/family and crash-recovery claims, replace placeholder
      links, and check navigation on desktop/mobile.
- [ ] Publish finalized pages and starter, verify participant visibility, then launch.

### Dataset grounding and reference limitations

All 245 bundled questions are retained in the constructed dataset; 100 randomly
selected questions move source statements verbatim into document-style images.
The images are statement sheets, not newly invented maps or quantitative charts.
The five published examples are removed from hidden scoring, leaving 240 cases.
Source mappings, seeds and hashes are in the organizer manifests. A source-content
review covered the 100 images and 355 moved statements; this establishes source
fidelity, not mathematical correctness of the source answer key.

Numeric source answers are preserved. Fourteen `No Best Solution` and six
`-99999.0` markers are normalized to `na`; those markers do not independently
prove infeasibility. The review CSV contains 23 flagged rows and known
counterexamples for MM-0047, MM-0079, MM-0088, MM-0183 and MM-0213. The current
release still contains their source references. Resolve whether to adjudicate,
exclude, or explicitly score agreement with those references before awarding prizes.
Do not silently edit the original source snapshot.

The source benchmark is public: hiding this derivative does not prevent prior
exposure or memorization. State the permitted training data and hardcoding policy.
More than 245 unique source problems requires additional source data; rendering
another image of the same problem does not add an independent test case.

### Current metric policy

For numeric predictions, error is `abs(prediction-reference) / max(1, abs(reference))`.
Each row scores +1 at error ≤ 0.01, +0.5 at error ≤ 0.05, otherwise 0.
Correct `na` scores +1; a numeric/`na` classification mistake scores -0.5.
Abstention (`skip`) scores 0. The leaderboard uses the mean row score, higher is
better, with possible range [-0.5, 1]. The denominator makes thresholds absolute
for references with magnitude below 1.

No scoring-code change is required merely to support `na`. The unresolved issue
is whether each source marker actually means infeasible. `na` must not mean
unknown, timeout or unbounded. The release adapter converts `skip` to missing;
the local scorer also gives it zero (as an invalid answer). Invalid values receive
zero in the metric, but Kaggle may reject a malformed submission before scoring.

All five randomly selected public examples happen to have numeric references.
Their IDs are EX-001 and EX-002 (images), EX-003 through EX-005 (text). The `na`
contract is documented; do not infer infeasibility from the absence of a solution.

## Keep the three data destinations separate

| Local directory/file | Where it goes | Who can read it |
|---|---|---|
| `public/` contents | Competition public data bundle | Participants |
| `starter/metrocore_starter.ipynb` | Starter Kaggle notebook | Participants |
| `private_rerun/` contents | Private replacement/RERUN bundle, via Kaggle-enabled process | Submitted code during hidden execution |
| `scoring/solution.csv` | Host solution/answer-key upload | Scoring service/hosts only |
| `scoring/metric.ipynb` | Custom metric registration | Metric source may be public; it contains no answers |
| `scoring/perfect_submission.csv` | Host sandbox test only | Hosts only |
| `organizer/` | Keep locally/private | Hosts only |

**Never upload this release root, `scoring/`, `organizer/`, or the original
dataset directory as public competition data.** A hidden inference bundle must
also contain no answer key. A private Dataset attached to the host's own notebook
does not by itself configure competition-wide hidden reruns.

## Step 1 — Create an unlaunched competition draft

Use Kaggle's competition creation flow and keep the draft unlaunched. This event
needs automated Code Competition scoring, not just the Hackathon writeup/judging
format. After creation, record the actual competition slug.

Optional CLI equivalent, if the installed official Kaggle CLI offers these
commands:

```bash
kaggle competitions init /tmp/metrocore-kaggle-host
```

Edit the generated `competition-metadata.json` to set title, unique slug, brief
description, and intended visibility. Keep notebooks enabled. Then:

```bash
kaggle competitions create -p /tmp/metrocore-kaggle-host
kaggle competitions settings get YOUR-COMPETITION-SLUG --json
```

These commands are instructions for the host, not commands run by this project.
Use your authenticated Kaggle session; do not place API credentials in release
files or participant notebooks.

## Step 2 — Confirm hidden rerun access with Kaggle

Ask Kaggle to confirm that your draft can:

- require notebook submissions and execute them on hidden replacement inputs;
- hide the rerun logs, output artifacts, questions, and images from entrants;
- disable inference internet and enforce selected compute/runtime limits;
- score a mixed numeric/text answer column using a custom metric;
- replace the public five-row input/sample bundle with the 240-row hidden bundle.

Suggested request (not sent):

> We are hosting MetroCore Decision Desk for CARE 2026 at IIT Roorkee.
> Our draft competition is YOUR-COMPETITION-SLUG. Participants receive five
> examples and submit offline notebooks. We need private reruns on 240 hidden
> text/image optimization problems, with reference answers held only by the
> scoring service. Our output is problem_id,answer, where answer is numeric,
> na for infeasible, or skip for abstention. Can you enable the private RERUN
> bundle, confirm the upload and sample-submission replacement procedure,
> and confirm restrictions on hidden-run outputs and available hardware?

The documented private-data CLI form is:

```bash
kaggle competitions data update YOUR-COMPETITION-SLUG \
  -p releases/kaggle_v1/private_rerun \
  -m "MetroCore hidden rerun v1" --rerun
```

**Do not run this without the required enablement; do not omit `--rerun` as a
workaround.** Without that option the documented command targets public data.
If access is unavailable, an external isolated evaluation service is separate
engineering work; it is not implemented by these local release files.

## Step 3 — Upload only the public data

Once the hosting plan is confirmed, upload the contents of `public/` through the
host's public data controls, preserving `images/` relative paths. CLI equivalent:

```bash
kaggle competitions data update YOUR-COMPETITION-SLUG \
  -p releases/kaggle_v1/public \
  -m "Five public examples and starter support files"
```

In a participant-equivalent view, verify that only five problems and two images
are visible. Open `examples.html` locally to inspect the examples first.

## Step 4 — Register the metric and upload the answer key

1. Import `scoring/metric.ipynb` as a Kaggle notebook for custom-metric creation.
2. Use Kaggle's custom Python metric workflow, then select that metric in
   **Host > Evaluation Metric**. Choose **higher is better**.
3. Configure `problem_id` as the identifier and `answer` as the scored column.
   `Usage` is host-only split metadata, not a prediction column.
4. Upload `scoring/solution.csv` through the private host solution upload.
5. Confirm 240 reference rows and the proposed Public/Private assignment.

Optional solution CLI:

```bash
kaggle competitions solution create YOUR-COMPETITION-SLUG \
  -p releases/kaggle_v1/scoring/solution.csv
kaggle competitions solution status YOUR-COMPETITION-SLUG
```

Wait for solution preprocessing to report ready. `scoring/metric.py` is the same
metric as the notebook; use whichever import path Kaggle's enabled flow supports.
The function signature is `score(solution, submission, row_id_column_name)`.
Kaggle must supply the relevant leaderboard subset to both frames. Confirm this
in the sandbox: the adapter deliberately rejects mismatched ID sets.

The **public** `sample_submission.csv` illustrates five example IDs, while the
**private rerun** version covers 240 hidden IDs. Confirm the enabled hosting
workflow validates the replacement template correctly. Do not mix the public
example IDs into the hidden answer key just to satisfy a prediction-only setup.

## Step 5 — Configure and publish the starter notebook

Import `starter/metrocore_starter.ipynb`, attach the competition data, and set its
`INPUT_DIR` to the actual mounted competition directory shown by Kaggle. The
default `/kaggle/input/metrocore-decision-desk` is a placeholder until the final
slug/mount is confirmed. Output should be:

```text
/kaggle/working/submission.csv
```

Participants implement:

```python
def solve(question: str, image_path: str | None = None):
    # Read text and optional image; formulate and solve.
    return optimal_value  # or "na" or None
```

The final runner cell handles the input iteration and writes:

```csv
problem_id,answer
EX-001,2400.0
EX-002,67.0
EX-003,skip
EX-004,na
EX-005,32.0
```

This is a **format illustration**, not the complete correct example output.
`public/example_answers.csv` contains the five source references. Hidden output
uses the hidden IDs read from `problems.json` and must have exactly 240 rows.

- Number: predicted objective value, finite and unformatted (no currency symbols).
- `na`: infeasible, not unknown/timed out/unbounded.
- `skip`: unanswered, zero score. None/blank/caught exceptions become `skip`.
- No dataframe index column, explanations, or variable assignments.

All-skip is the starter's intentional placeholder behavior: it tests the interface
and scores zero. It is not a solving baseline. Users must replace `solve`.

Local pandas testing preserves lowercase `na` and `skip`; blank cells load as
missing and score zero. Nevertheless, test the actual Kaggle preprocessing path:
do not publish if it rejects the string tokens or converts `na` into missing.

## Step 6 — Set the runtime and event rules

Choose and record hardware, memory, notebook time limits, offline model/package
policy, daily submissions, team limits, final-submission selection, tie rules,
dates/timezone, prizes, and report weighting. Use Asia/Kolkata for event-facing
times and explicit offsets/UTC for platform configuration.

Benchmark a real pipeline on all 240 problems before setting the runtime limit.
The starter is fast because it does not solve anything; its runtime cannot
justify a competition budget. Capture the selected environment and replace the
draft `public/ENVIRONMENT.md`. Hardware/model-size enforcement is not supplied
by the local scorer. The runner has no per-problem watchdog.

Review `pages/` and remove all host-draft notes after finalizing the policy.
These pages avoid the older unsupported 60+ families/large-scale claims. Replace
the promotional site's placeholder competition links with the actual slug.

## Step 7 — Run an end-to-end private smoke test

Before launch, require all of the following:

| Check | Expected result |
|---|---|
| Interactive starter with public bundle | 5 rows, no hidden problems visible |
| Hidden rerun of starter | 240 rows, all skip, score 0 |
| Host perfect submission against private solution | Score 1.0 on both partitions |
| Host shuffled perfect rows | Same score; ID alignment works |
| Numeric error exactly 1% / 5% | +1 / +0.5 |
| Correct na / incorrect na | +1 / -0.5 |
| Number against na | -0.5 |
| Skip | 0; token accepted by Kaggle preprocessing |
| One caught solve exception | That row skip; remaining rows processed |
| Missing/duplicate/unknown IDs | Format rejected |
| Fatal notebook failure | Verify platform error behavior; do not promise partial credit |
| Hidden-run logs and output artifacts | Not retrievable by entrants |
| Submitted notebook without answer-key mount | Cannot read references |

`scoring/perfect_submission.csv` is only for host sandbox scoring. Never attach
it to a participant notebook, including for an end-to-end test.

For a safe notebook-level correctness check, use a separate temporary competition
or authorized synthetic rerun bundle with simple known inputs. Do not hardcode
real hidden answers into a notebook that could become publicly visible.

## Step 8 — Launch only after the checks pass

Use the host launch checklist after confirming data separation, hidden-run
capability, metric correctness, finalized references, runtime, and rules. No
upload or launch has been attempted by this workspace.

## Local verification and rebuilding

Create an isolated local test environment (Python 3.10+):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dataset.txt -r requirements-evaluation-tests.txt
```

The renderer also needs DejaVu Sans regular/bold fonts; the existing build records
their paths and hashes. The dependencies above are organizer test/build dependencies,
not a finalized participant runtime. Run:

```bash
.venv/bin/python -B -m unittest discover -s . -p 'test_*.py' -v
.venv/bin/python -B evaluator.py \
  --submission releases/kaggle_v1/scoring/perfect_submission.csv \
  --test-set releases/kaggle_v1/scoring/hidden_test_set.json
```

Regenerate a separate version after changes:

```bash
.venv/bin/python -B prepare_kaggle_release.py --output /tmp/metrocore-release-rebuilt
```

The builders refuse to overwrite existing output directories. Edit Python sources
and `release_templates/`, rebuild into a fresh directory, compare artifacts, then
select/version the next release. Do not hand-edit generated metric copies or change
hashed release files without rebuilding their manifest. The deployment guide is
maintained separately from generated artifacts. Preserve the old release for audit.
The full local suite contains 25 tests, including starter execution on both bundles,
metric parity/boundaries, source mappings, image paths, and release hashes. Local
passing tests do not certify Kaggle integration or the source labels.

Selection seed is 20261109; leaderboard split seed is 20261110. Source v1 remains
unchanged. File hashes and example-to-source mappings are organizer-only.

## Official references checked

- [Kaggle competition setup](https://www.kaggle.com/docs/competitions-setup):
  custom metric registration, private solution files, and Usage split metadata.
- [Kaggle official host CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/competition_creation.md):
  draft creation, settings, data/solution commands, and admin-only rerun upload.
- [Kaggle code competition debugging](https://www.kaggle.com/code-competition-debugging):
  hidden notebook execution, submission extraction, and failure modes.
