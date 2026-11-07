# Evaluation

Submissions are scored against source reference answers. Higher mean score is
better. Each expected hidden problem contributes equally within the leaderboard
partition supplied to the scorer.

For numeric reference A* and prediction A, let
`error = abs(A - A*) / max(1, abs(A*))`.

| Outcome | Score |
|---|---:|
| Numeric error <= 0.01 | +1 |
| Numeric error > 0.01 and <= 0.05 | +0.5 |
| Numeric error > 0.05 | 0 |
| Correct `na` | +1 |
| `na` against a numeric reference | -0.5 |
| Numeric prediction against `na` | -0.5 |
| `skip`, missing, or invalid answer | 0 |

`na` means infeasible. It does not mean unknown, timed out, or unbounded. Use
`skip` to abstain. The starter maps None, blank, and caught per-problem errors to
`skip`. Fatal notebook errors may invalidate the entire submission on Kaggle.

Submit `problem_id,answer`, one row for every input problem. IDs must be unique
and match the input set; malformed structure is rejected. Numeric outputs must
be finite. No hidden per-problem references are returned to participants.

The proposed leaderboard uses 30% of hidden problems for feedback and 70% for
final ranking, stratified by modality and source feasibility label. Both sets of
questions remain hidden. Host must confirm this split before launch.
