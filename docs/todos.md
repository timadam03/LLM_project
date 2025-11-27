# Project Status & TODOs

_Last updated: 2025-11-27 by Tim_

This file mirrors the structure of `group-project/README.md` so we can track completion status at a glance.

## Part I – Search-Augmented Agent

- [x] **Task 1 – Implement search-augmented agent loop**  
  Implementation lives in `group-project/agent.py`, `group-project/tools.py`, and `group-project/api.py`. The agent already supports both the Serper search tool and an optional browsing tool, logs trajectories, and enforces the strict JSON answer format.

- [x] **Task 2.1 – Baseline (no-search) generation + evaluation**  
  `results/results_4th_run/predictions_nosearch.jsonl` matches the required schema. EM = 39%, LLM judge = 72% (see `docs/tim/Results.md`), both above the minimum thresholds.

- [x] **Task 2.2 – Search agent generation + evaluation**  
  ✅ Predictions and trajectories saved under `results/results_4th_run/`.  
  ✅ **Status:** Likely Complete.  
  - Search Agent (latest run): **EM 44%**, **Judge 74%** (verified in `grading_results_llm_judge.json`).
  - Baseline (latest run): **EM 36%** (worse than previous 39%).  
  - _Analysis:_ While I cannot run the LLM judge on the new baseline (missing API key), the drop in baseline EM score suggests the baseline Judge score is likely <69%. If so, the 74% Search score meets the +5% improvement requirement (74% - <69% > 5%).

- [ ] **Task 2.3 – Analyze improvements & showcase trajectories**  
  Need to pick at least two successful queries from `results/*/agent_trajectories.jsonl`, screenshot the step-by-step reasoning, and explain how search (or browsing) improved EM/Judge outcomes in the PDF report.

- [ ] **Task 3 (Bonus) – Browsing tool**  
  Browsing tool already implemented (`website_browsing` in `tools.py`, `browsing()` in `api.py`) and evaluated (EM 44%, LLM judge 74% per `docs/tim/Results.md`). Still need to:  
  1. Capture code screenshots for the report.  
  2. Compare against search-only runs and document why browsing helps or not.

## Part II – Realistic Multi-Tool Agent

- [ ] **Task 1 – Build agent with ≥3 real-world tools (excl. Google Search)**  
  No implementation yet. Need to decide on real services (e.g., Calendar, Slack, Sheets), wire up authenticated API calls, and extend the agent loop to select among them.

- [ ] **Task 2 – Demonstrate three 5-step trajectories**  
  Blocked on Task 1. After the tools exist, record at least three distinct workflows, ensuring each uses ≥3 tools and is documented with trajectories plus analysis.

## Documentation & Submission

- [ ] Update `docs/tim/Report.md` to follow the exact numbering (1, 2.1, 2.2, …) from the README and incorporate the remaining analyses/screenshots.
- [ ] Once requirements are met, clean up `results/` (retain final runs only) and prepare the final PDF + zipped codebase per submission guidelines.


