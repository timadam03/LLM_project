# Project Report

## Part I – Search-Augmented Agent

### 1. Implementation
The search-augmented agent is implemented across three main files:
- **`agent.py`**: Contains the core logic for the agent loop, handling message history and tool invocations.
- **`tools.py`**: Defines the tools available to the agent, including the Google Search tool (via Serper API).
- **`api.py`**: Manages API interactions with the DeepSeek model and the Serper search service.

The agent follows a ReAct-style loop: it receives a query, decides if it needs to use a tool, executes the tool, observes the output, and repeats until it can formulate a final answer. The strict JSON output format is enforced via the system prompt.

### 2.1 Baseline (no-search) Generation + Evaluation
The baseline agent generates answers directly from its internal knowledge without access to external tools.
- **Results File**: `results/results_4th_run/predictions_nosearch.jsonl`
- **Performance**:
  - **Exact Match (EM)**: 39%
  - **LLM Judge Score**: 72%

### 2.2 Search Agent Generation + Evaluation
The search-augmented agent uses Google Search to retrieve up-to-date or specific information before answering.
- **Results File**: `results/results_4th_run/predictions_search.jsonl`
- **Performance**:
  - **Exact Match (EM)**: 44%
  - **LLM Judge Score**: 74%

**Analysis**: The search agent achieved a **+5% improvement in Exact Match** and a **+2% improvement in LLM Judge score**. The search capability allowed the agent to answer questions requiring specific dates, recent events, or obscure facts that the baseline model either hallucinated or refused to answer.

### 2.3 Analyze Improvements & Showcase Trajectories

Below are two examples where the Search Agent successfully used tools to arrive at the correct answer, showcasing step-by-step reasoning.

#### Trajectory 1: Specific Historical Date
**Question**: "when was the last time anyone was on the moon?"
**Final Answer**: "December 1972" (Correct)

**Reasoning Trace**:
1.  **Action**: `search` ("last time anyone was on the moon date")
    -   **Observation**: Retrieved snippets mentioning "Apollo 17 (December 7–19, 1972) was the eleventh and final mission...".
2.  **Action**: `browsing` ("https://en.wikipedia.org/wiki/Apollo_17")
    -   **Observation**: Read the full Wikipedia page title "Apollo 17 - Wikipedia".
3.  **Final Answer**: Formulated "December 1972" based on the confirmed mission dates.

**Why it worked**: The search provided the mission name (Apollo 17) and dates. The agent verified this by browsing the specific Wikipedia page to ensure no later missions occurred, leading to a high-confidence correct answer.

#### Trajectory 2: Disambiguating Rulers
**Question**: "who was the ruler of england in 1616?"
**Final Answer**: "James I" (Correct)

**Reasoning Trace**:
1.  **Action**: `search` ("ruler of England in 1616")
    -   **Observation**: Snippets mentioned "James VI and I", "James I (r. 1603-1625)", and "King of Scotland as James VI... and King of England as James I".
2.  **Action**: `browsing` ("https://en.wikipedia.org/wiki/James_VI_and_I")
    -   **Observation**: Confirmed the dual title and reign dates via Wikipedia.
3.  **Final Answer**: "James I"

**Why it worked**: The query involves a monarch with different titles in different regions (James VI in Scotland, James I in England). The search results highlighted this complexity, and the browsing step allowed the agent to confirm the specific title "James I" was correct for the context of "England" in 1616.

---

## Part II – Realistic Multi-Tool Agent

### 1. Implementation
We extended the agent to support ≥3 real-world tools (excluding Google Search):
- **`calculator`**: Evaluates mathematical expressions (e.g., "11069000 / 1967").
- **`wikipedia_search`**: Searches Wikipedia for summaries.
- **`get_weather`**: Retrieves current weather data via OpenMeteo API.
- **`website_browsing`**: (Bonus) Scrapes full content from URLs.

### 2. Demonstration
We generated complex trajectories where the agent combines multiple tools to solve multi-step problems.
- **Results File**: `results/multi_tool_trajectories.jsonl`

#### Trajectory A: Cross-Checking & Calculation
**Question**: "Who is the current CEO of Microsoft? Find his birth year and the city he was born in. Then find the current population of that city. Finally, divide the population by his birth year and tell me the current weather in that city."

**Steps Taken**:
1.  **Search**: Found Satya Nadella is CEO.
2.  **Wikipedia**: Confirmed birth date (1967) and city (Hyderabad).
3.  **Search**: Found Hyderabad population (~11 million).
4.  **Browsing**: Verified population data on MacroTrends.
5.  **Calculator**: Calculated `11069000 / 1967` = `5627.35`.
6.  **Weather**: Got current weather for Hyderabad (27.5°C).

**Result**: Successfully integrated data from 4 different sources/tools into a single coherent answer.

#### Trajectory B: Historical & Real-Time Data
**Question**: "Find the host city of the 1992 Summer Olympics... Check weather... Find population... Find landmark... Calculate."

**Steps Taken**:
1.  **Wikipedia**: Identified Barcelona as the host city.
2.  **Search/Browsing**: Used to find famous landmarks (Sagrada Família) and confirm population.
3.  **Weather**: Retrieved real-time temperature for Barcelona.
4.  **Calculator**: Performed the required arithmetic.

**Result**: Demonstrated the agent's ability to maintain context across 8 distinct steps and switch between historical queries and real-time API calls.

---

## Part III (Bonus) – Browsing Tool

### Implementation
The `website_browsing` tool allows the agent to read the full text content of a webpage, overcoming the limitation of short search snippets.

```python
def browsing(link): 
    # Uses Serper API's scrape endpoint
    conn = http.client.HTTPSConnection("scrape.serper.dev")
    payload = json.dumps({ "url": link })
    headers = {
        'X-API-KEY': serper_key,
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/", payload, headers)
    # ... (response handling)
    response_dict = {
        "title": title,
        "content": content
    }
    return response_dict
```

### Evaluation
- **Usage**: The agent frequently chose to use `browsing` after a `search` to verify details.
- **Impact**: In the "Gram on Young and the Restless" query (Part I analysis), the agent struggled with search snippets alone but used browsing on a Fandom wiki page to find a specific list of minor characters, ultimately leading it closer to the answer. This "read" capability is crucial for questions where the answer is buried deep in a page and not surfaced in SEO summaries.
