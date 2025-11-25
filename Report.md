# LLM Project Report

* **updated:** 24.11 Tim
* **Status:** Part I/II implementation and evaluation

## Setup

* Created an `.env` file storing the two required API keys.
* Set up a Python virtual environment using `uv` and installed all dependencies from `requirements.txt`.

## Implementation Overview

This section outlines the project structure and the purpose of each component.

### Added Files

#### **tools.py**

Contains the list of tools used by the agent. Currently includes:

* Search function wrapper for the Serper API

#### **api.py**

Handles all API-related logic:

* Initializes DeepSeek model client
* Implements the Serper search request function

#### **agent.py**

Implements logic for both the search-augmented agent and the baseline agent.

### Agent Designs

#### **Search Agent**

**Inputs:**
* system_prompt: ensures right output format, might need to be adjusted if results not short enough
* `messages`: contains system prompt + user query
* `tools_list`: imported from `tools.py`
* Response format instructions enforcing JSON output

**Outputs:**

* Short answer
* Detailed answer
* The full messages dictionary containing the interaction

#### **Baseline Agent**

**Input:**

* Simple system prompt + user question

**Output:**

* One-step response directly from the model without using any search tools


#### **generate.py**

Implements logic to generate using both agents, savingthe results in the exact formats as defined by prof


---

Findings: Model answers good, also searches mulitple times when needed, only need to change system_prompt so the models answers more exact and concise, to pass Exact Match evaluation, therefore give some examples and cut out fillwords,
maybe also increase the max_steps that the model can take to search

### Notes for now
To add serching whole websites serper has website mode where it scrapes the whole website of url we give it, so when model thinks it needs more info, it can call second tool that returns all contents of a website, will do that later today

For the scraping whole website, response structure for Serper API:
- text: str
-  metadata: dict
    - contains different stuff, always author, sometimes title, og:title etc
- credits: int

For improving look at results where it was wrong, change the max_steps, add website reading, etc
