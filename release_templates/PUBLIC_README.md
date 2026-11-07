# MetroCore example data

This bundle contains exactly five public examples: two image+text problems and
three text-only problems. These source problems are excluded from hidden scoring.

## Use the starter notebook

1. Add this competition's data to a Kaggle notebook.
2. Import the organizer's `metrocore_starter.ipynb`.
3. Set `INPUT_DIR` to the mounted competition folder containing `problems.json`.
4. Implement `solve(question, image_path)`. `image_path` is an absolute PNG path
   or None. Load models once before the final inference cell.
5. Run all cells. Output is `/kaggle/working/submission.csv`.

The notebook reads the actual input file at runtime; do not copy IDs from the
five-row sample template. Hidden reruns use the same filenames with different
problems and a different row count.

## Output contract

```csv
problem_id,answer
EX-001,2400.0
EX-002,67.0
EX-003,skip
EX-004,na
EX-005,32.0
```

This illustrates output tokens; it is not a perfect example submission.
`example_answers.csv` contains the source references for all five examples.

- Finite number: predicted optimal objective value.
- Literal lowercase `na`: no feasible solution exists.
- `skip`: unanswered/abstain, worth zero. Returning None or blank from solve is
  automatically written as `skip` by the starter. Do not substitute `na`.
- Exactly one row per input problem, with exactly `problem_id,answer` columns.
- Preserve IDs exactly. No extra index column, explanations, or solution vectors.

The output field is mixed numeric/text. If reading with pandas, use
`pd.read_csv(path, dtype=str, keep_default_na=False)` to preserve literal tokens.
The metric also handles actual missing cells as unanswered, but the supplied
runner emits nonempty `skip` cells for platform validation.

`examples.html` provides a readable view of all five questions, images, and
reference answers. The standalone HTML and answers are only learning aids; the
starter inference loop does not load them.

## Local execution

Set `METROCORE_INPUT_DIR` to this folder and `METROCORE_OUTPUT_PATH` to a local
CSV path before executing the starter notebook. The runner requires Python 3.10+
and the standard library. Your model/OCR/solver dependencies are separate.
