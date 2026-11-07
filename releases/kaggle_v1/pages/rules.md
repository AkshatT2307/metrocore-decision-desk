# Rules — host draft

1. Submitted inference runs offline. Do not call external APIs or services.
2. Open-weight models up to 7B parameters per model are permitted. Quantization,
   multiple models in sequence, and fine-tuning are permitted under the finalized
   external-data and model rules.
3. Do not hardcode source answers or use question-to-reference lookup tables.
   The pipeline must formulate and solve the provided problem.
4. Do not attack the runner, inspect answer keys, or attempt to extract hidden
   questions through outputs or leaderboard probing.
5. Prize winners must provide reproducible code and model/dependency details.
6. Submit a technical report of at most 2500 words covering architecture,
   novelty, model details, and image understanding.

Before publishing, the host must specify eligibility, team sizes, prizes, dates,
daily submission limits, final submission selection, tie-breaking, and whether
the technical report affects ranking. Also clarify permitted prior NL4Opt
training exposure and how model-size rules apply to vision components/MoE models.
These are unresolved event settings; this draft is not a final competition rulebook.
