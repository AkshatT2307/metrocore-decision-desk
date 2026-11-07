# MetroCore Decision Desk

Build an offline system that reads an optimization word problem, optionally with
an attached data-sheet image, and returns the optimal objective value or `na`
when infeasible. Questions are derived from NL4Opt. Some numerical statements
appear only in the image and must be combined with the text.

Five examples with source reference answers are provided. They are excluded from
hidden evaluation. In the planned Code Competition, submitted notebooks run on
hidden inputs and receive an aggregate score; participants cannot browse those
hidden questions or their reference answers.

Implement the provided notebook interface and generate `submission.csv`. Open-weight
models up to 7B parameters may be used. Inference is offline. See the rules,
evaluation page, and finalized environment specification before participating.

Host note: this is draft copy. Publish only after hidden rerun capability is
enabled and the wording matches the configured environment.
