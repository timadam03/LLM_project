# LLM Project Report

* **updated:** 24.11 Tim
* **Status:** Part I implementation and evaluation

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

---
