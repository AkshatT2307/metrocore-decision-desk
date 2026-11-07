# NL4Opt multimodal derivative v1

245 unique source problems: **100 multimodal**, **145 text-only**.
Uniform random selection without replacement; seed **20261107**.
Problem IDs and order are shuffled independently with seed 20261108.

## Files

- `inference/problems.json`: input-only questions and relative image paths.
- `inference/images/`: exactly 100 PNG data sheets.
- `inference/submission_runner.py`: participant-side inference/checkpoint helper.
- `organizer/hidden_test_set.json`: reference file for the local evaluator.
- `organizer/reference_answers.csv`: organizer-only answer CSV.
- `organizer/manifest.jsonl`: source mapping, original wording and answers,
  moved statements, image hashes, and rendering information.
- `organizer/build_manifest.json`: seed, source/font hashes, and build settings.
- `organizer/review.html`: browser gallery of all 100 images alongside their
  transformed questions and expandable organizer provenance.

Only `inference/` belongs in a hidden notebook runtime. It is **not a public
download**. The organizer directory and this whole dataset must not be uploaded
as ordinary public competition data. Public examples and leaderboard splits have
not been selected; all 245 rows are retained as requested.

## What the multimodal conversion does

Each selected question retains its scenario introduction and objective in text.
Complete quantitative statements are moved verbatim into an operational data
sheet image. The image includes qualifiers such as “at most,” units, ratios, and
word quantities such as “twice.” A note tells the participant to combine both
modalities. Statements carrying the objective stay in text even if they also
contain numerical information.

These are **document-style specification tables**, with original sentences in
the table cells, rather than rewritten parameter matrices, charts, or maps. This
first derivative prioritizes faithful transfer of the source information. Four
high-contrast palettes and domain-appropriate titles vary presentation without
adding data or changing constraints. Images are 1440 pixels wide, use a 29-pixel
body font, and grow vertically to avoid clipping. No answer/source IDs or OCR
text metadata are embedded in PNG files. Image filenames use the new problem IDs.

All 145 text-only questions are unchanged. The source file and previous 50-case
dataset remain unchanged.

## References and `na`

Numeric source answers are copied exactly. The existing source convention is
made explicit: `No Best Solution` and `-99999.0` map to `na`. Original values are
retained in the organizer manifest; this is normalization, not an independent
proof of infeasibility.

| Modality | Numeric reference | Source-mapped `na` | Total |
|---|---:|---:|---:|
| Text-only | 131 | 14 | 145 |
| Image + text | 94 | 6 | 100 |
| Total | 225 | 20 | 245 |

The scoring weights are unchanged: correct `na` gets +1; `na` on a feasible
reference or a number on an infeasible reference gets -0.5. Missing/blank,
invalid output, and caught per-problem errors get zero. Unknown, unbounded,
timeout, and infeasible must not all be conflated into `na`. Only bounded-feasible
or genuinely infeasible tasks fit the published two-outcome answer contract.

Known source-label concerns from the earlier audit are not silently corrected.
See `organizer/reference_review.csv`. All source sentinel mappings also remain
unverified. The output is a constructed benchmark candidate, not a certification
of every source optimum. Retaining a public benchmark as the source also retains
its potential for prior familiarity or memorization.

## Rebuild and validate

Requires Python 3.10+, Pillow 11.3.0, and DejaVu Sans regular/bold fonts. From the
inner `hackathon/` repository:

```bash
python3 -m pip install -r requirements-dataset.txt
python3 build_multimodal_dataset.py --output /path/to/fresh-output
python3 -B -m unittest test_evaluation test_multimodal_dataset -v
python3 evaluator.py \
  --submission /path/to/submission.csv \
  --test-set datasets/nl4opt_mm_v1/organizer/hidden_test_set.json
```

The builder refuses to overwrite an existing output directory. Exact PNG hashes
require the same Pillow version and font files; their hashes are recorded in the
build manifest. Regression checks cover all source statements and references,
the reproducible selection, image decoding/hashes, inference-bundle separation,
and scorer integration. A sample of the images was visually inspected; the
gallery supports further human review of every pair.
