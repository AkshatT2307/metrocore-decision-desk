# MetroCore Decision Desk


## 1. The challenge

MetroCore is a metropolitan area of 4.2 million people. Its various city departments face operational decision problems — scheduling shifts, routing vehicles, allocating budgets, planning infrastructure — each described in natural language. You will receive optimization problems written the way real people write: as word problems, memos, and policy excerpts.

**Your mission:** build a system that takes a problem description (text and, optionally, images) and returns the mathematically optimal answer.

## 2. What your system receives

Each problem consists of **text and, optionally, one or more images**. The text is a word problem written in the voice of a city department head. Images, when present, carry data that is essential to solving the problem — tables, charts, maps, or scanned documents. All numerical data, constraints, and objectives are embedded across the text and images together.

Problems reflect the conventions of city staff writing. Participants should expect:

- Figures that do not matter mixed with ones that do.
- Mixed units and conventions: tons and kg, weekly and monthly, lakh and crore.
- Rules that any competent analyst would assume without writing them down, such as 'a nurse cannot work two wards at once'.
- Key data supplied only inside an attached image, not repeated in the text.

### Example problem types

**Type A — Image contains a data table.**
A memo from the Transit Director reads: *"We need to assign buses to the six new routes starting Monday. Minimize total deadhead kilometres. The distance matrix is attached."* An accompanying image shows a photographed table of pairwise distances between depots and route start-points.

**Type B — Image contains a chart or graph.**
A note from the Energy Department reads: *"Attached is the hourly demand forecast for next week. Schedule our three generators to meet demand at minimum fuel cost. Each generator's capacity and per-MWh cost are listed below."* The hourly demand curve is provided as a bar chart in an image; the generator specs appear in the text.

**Type C — Image contains a map or diagram.**
A message from Parks & Environment reads: *"We are installing sensor stations across the river network. The map shows the eight candidate locations and the river segments each one covers. Place the fewest stations so every segment is monitored."* The river-network map with candidate locations is an attached image.

## 3. What your system returns

For every problem, return **one value**:

- A **single number**: the optimal objective value, at full floating-point precision.
- Or **`na`**: if no feasible solution exists (the constraints contradict each other).

The expected output is the optimal objective value only. No variable assignments, explanations, or intermediate work are required.

**Example `submission.csv`:**

```
problem_id,answer
MC-001,2450.75
MC-002,18900.0
MC-003,na
```

## 4. Scope and scale

Problems cover a broad range of operational domains — logistics, scheduling, resource allocation, infrastructure planning, financial optimization, and more. Each problem is a self-contained optimization task described in natural language.

The dataset contains more than 60 problem families. Size ranges from small (fewer than ten decisions) to large (several hundred). Some problems set one goal. Some spread decisions over several periods.

## 5. Scoring

Let A be your answer and A\* be the reference optimal value.

| Your answer | Score |
| :-- | :-- |
| Correct: \|A − A\*\| / max(1, \|A\*\|) ≤ 0.01 | **+1** |
| Close: within 5% of A\* | **+0.5** |
| Wrong number (feasible problem, answer off by >5%) | **0** |
| Wrong number on an infeasible problem (should be `na`) | **−0.5** |
| `na` on a feasible problem | **−0.5** |
| Correct `na` on an infeasible problem | **+1** |
| Missing answer or crash | **0** |

Final score = mean of per-problem scores across the evaluation set.

## 6. Runtime and environment

Your notebook reads problems and writes `submission.csv`.

| Limit | Value |
| :-- | :-- |
| Network | None. |
| Crash | Problems answered before a crash keep their scores. Unanswered problems score 0. |

**Models.** Open-weight models of up to 7B parameters may be used. Multiple models may be run in sequence. Quantization and fine-tuning are permitted on any data participants have the right to use.

**Libraries.** `ENVIRONMENT.md` lists every preinstalled package. All teams receive the same environment. Additional open-source packages may be bundled. Commercial software and anything requiring a license server are prohibited.

**Output.** Your notebook writes `submission.csv` with two columns: `problem_id` and `answer`.

## 7. Rules

1. **No internet.** No calls to any external model or service.
2. **No hardcoding.** The pipeline must work on problems it has never seen. Top-scoring teams may be rerun on a renumbered, paraphrased copy of the Dev set. A significant score drop faces review and possible disqualification.
3. **No tampering.** Do not attack the harness or attempt to read hidden data. Violations lead to disqualification.
<!-- 4. **Teams of 2 to 4.** Each person joins one team. -->
5. **Reproduction.** Prize winners hand over their code and reproduce their score on organizer hardware. Failure to reproduce forfeits the prize to the next-ranked team.

## 8. Technical report

Every team submits a technical report of at most 2500 words (excluding references and appendices). The report must cover the following:

1. **Architecture overview.** A clear system diagram and end-to-end description of the pipeline — from raw problem input (text + images) to final numerical answer. Describe every major component and how they interact.
2. **Novelty statement.** What is new or non-obvious about your approach? This could be a novel prompting strategy, a custom formulation-extraction step, an unconventional solver integration, a specialized vision pipeline, or any other technique that distinguishes your system from a naïve baseline.
3. **Model details.** For every model used, state: model name and size, quantization scheme (if any), fine-tuning data and procedure (if any), and the role the model plays in the pipeline. If multiple models are composed, explain the routing or sequencing logic.
4. **Image-understanding pipeline.** How does your system extract structured data from images (tables, charts, maps)? Describe preprocessing, extraction, and any verification steps.
<!-- 5. **Ablation study.** A table with at least four rows showing the contribution of key components (e.g., with/without vision, with/without verification, solver choice, model size). -->
<!-- 6. **Failure analysis.** A taxonomy of failure modes observed on the Dev set, with counts and representative examples. Include a hypothesis for each failure mode and, where applicable, what was tried to fix it. -->
<!-- 7. **What did not work.** Approaches that were tried and abandoned, with a brief explanation of why. -->

The jury rewards depth of insight, reproducibility, and clarity over polish.

<!-- ## 9. Starter kit

The following materials are provided at the start of the competition:

- The Dev set (100 problems with reference optimal values; problems may include associated images). -->
<!-- - A local evaluation script for the Dev set.
- A baseline notebook with its Dev score: a local 7B model reads each problem and outputs an answer.
- `ENVIRONMENT.md` listing the preinstalled runtime environment. -->
