# Multi-Agent Financial Analysis Experiment

This experiment demonstrates a **Multi-Agent System** performing complex financial valuation (DCF) and debate.

## Architecture

1.  **Lead Quantitative Analyst (Tool-Augmented)**:
    *   Uses `google_search` and `website_browsing` to retrieve real-time financial data (Price, FCF, Beta, Treasury Yields).
    *   Calculates a baseline Discounted Cash Flow (DCF) valuation.
    *   Outputs a structured JSON with "Thinking Process" and "Assumptions".

2.  **Senior Growth Strategist (Bull Agent)**:
    *   Reviews the Lead Analyst's data.
    *   Argues for higher growth scenarios (e.g., AI TAM expansion).
    *   Provides an adjusted target price and a "BUY" vote.

3.  **Chief Risk Officer (Bear Agent)**:
    *   Reviews the same data.
    *   Argues for downside risks (e.g., competition, regulatory headwinds).
    *   Provides an adjusted target price and a "SELL" vote.

## Output
*   **`process.log`**: Detailed logs of the Lead Analyst's tool usage (Search -> Browser -> Calculator) and reasoning.
*   **`experiment_log.md`**: A formatted "Investment Committee Report" summarizing the Base Case and the Bull/Bear debate.

## Usage
```bash
python poster-experiment/run_experiment.py
```
Target: **NVDA** (NVIDIA Corporation)
