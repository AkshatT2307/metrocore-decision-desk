# Data and files

- `problems.json`: five public examples with `problem_id`, `question`, and
  `image_path`. Image paths are relative to this file; null means text-only.
- `images/`: two example data sheets.
- `example_answers.csv`: source reference answers for these five examples.
- `sample_submission.csv`: five-row format illustration, with `skip` placeholders.
- `submission_runner.py`: inference loop, image-path resolution, checkpointing.
- `examples.html`: readable example gallery.
- `README.md`: detailed notebook and output instructions.
- `ENVIRONMENT.md`: runtime specification; finalize before launch.

The hidden rerun bundle uses the same `problems.json`, `images/`, and runner
paths. It contains no answer key. Build output IDs dynamically from the current
input file. Do not assume that hidden rows equal the public sample template.

Five example sources and every hidden source are disjoint. The original NL4Opt
source's numerical references are retained; legacy failure markers are normalized
to `na` under the organizer's recorded policy.
