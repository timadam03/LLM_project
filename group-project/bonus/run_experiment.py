import json
import sys
from datetime import datetime
from financial_agent import run_financial_agent
from api import client

class Logger(object):
    def __init__(self, filename='poster-experiment/process.log'):
        self.terminal = sys.stdout
        self.log = open(filename, 'w')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def get_critique(base_case_json, persona, bias):
    """
    Uses the LLM to critique the base case valuation from a specific perspective.
    Does NOT use tools, just pure reasoning based on the provided data.
    """
    prompt = f"""
    You are {persona}.
    Your goal is to critique the following DCF valuation of {base_case_json.get('company')}.
    
    Bias: {bias}
    
    BASE CASE DATA:
    {json.dumps(base_case_json, indent=2)}
    
    Review the assumptions (Growth Rate, WACC) and the Reasoning.
    Provide your own perspective.
    
    OUTPUT FORMAT (Strict JSON):
    {{
        "analyst_name": "{persona}",
        "critique": "Your detailed argument...",
        "proposed_adjustment": "e.g., Increase growth to 15% because...",
        "new_estimated_value": <float> (Your rough estimate based on adjustment),
        "vote": "BUY" or "SELL" or "HOLD"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "You are a senior financial strategist. Output strict JSON."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            stream=False
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"analyst_name": persona, "critique": f"Error: {str(e)}", "vote": "HOLD"}

def main():
    # Redirect stdout to log file
    sys.stdout = Logger()
    
    ticker = "NVDA"
    print(f"--- Starting Multi-Agent Valuation for {ticker} ---")
    
    # 1. Lead Analyst (Tool User)
    print("\n>>> Round 1: Lead Quantitative Analyst (Gathering Data & Base Model)...")
    base_case = run_financial_agent(ticker, max_steps=40, persona="Lead Quantitative Analyst")
    
    if not base_case:
        print("Failed to generate base case.")
        return

    # 2. Bull Strategist (Critique)
    print("\n>>> Round 2: Growth Strategist (Bull Case)...")
    bull_case = get_critique(base_case, "Senior Growth Strategist", "Optimistic. Focus on AI total addressable market (TAM) expansion and monopoly pricing power.")

    # 3. Bear Strategist (Critique)
    print("\n>>> Round 3: Risk Manager (Bear Case)...")
    bear_case = get_critique(base_case, "Chief Risk Officer", "Pessimistic. Focus on competition, overvaluation, and cyclical semi-conductor risks.")
    
    # Save all results
    full_report = {
        "base_case": base_case,
        "bull_case": bull_case,
        "bear_case": bear_case
    }
    
    with open("poster-experiment/valuation_results.json", "w") as f:
        json.dump(full_report, f, indent=2)
        
    # Create the Final Report Log
    with open("poster-experiment/experiment_log.md", "w") as log:
        log.write(f"# Multi-Agent Investment Committee Report: {ticker}\n")
        log.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        log.write("## 1. Lead Analyst (Base Case)\n")
        log.write(f"**Valuation**: ${base_case.get('estimated_value', 0)}\n")
        log.write(f"**Upside**: {base_case.get('upside_downside')}\n")
        log.write(f"**Reasoning**: {base_case.get('reasoning')}\n")
        log.write(f"**Thinking Process**: *{base_case.get('thinking_process', 'N/A')}*\n\n")
        
        log.write("## 2. The Debate\n")
        
        log.write(f"### {bull_case.get('analyst_name')} (Bull)\n")
        log.write(f"**Critique**: {bull_case.get('critique')}\n")
        log.write(f"**Adjustment**: {bull_case.get('proposed_adjustment')}\n")
        log.write(f"**Target**: ${bull_case.get('new_estimated_value')}\n")
        log.write(f"**Vote**: {bull_case.get('vote')}\n\n")

        log.write(f"### {bear_case.get('analyst_name')} (Bear)\n")
        log.write(f"**Critique**: {bear_case.get('critique')}\n")
        log.write(f"**Adjustment**: {bear_case.get('proposed_adjustment')}\n")
        log.write(f"**Target**: ${bear_case.get('new_estimated_value')}\n")
        log.write(f"**Vote**: {bear_case.get('vote')}\n\n")

        log.write("## 3. Committee Decision\n")
        votes = [base_case.get('upside_downside', '-'), bull_case.get('vote', 'HOLD'), bear_case.get('vote', 'HOLD')]
        # Simple logic for final verdict (can be enhanced)
        log.write("The committee has reviewed the quantitative data and qualitative arguments.\n")
        log.write("- **Base**: " + str(base_case.get('estimated_value')) + "\n")
        log.write("- **Bull**: " + str(bull_case.get('new_estimated_value')) + "\n")
        log.write("- **Bear**: " + str(bear_case.get('new_estimated_value')) + "\n")
        
    print("\nExperiment complete. Multi-agent debate saved to poster-experiment/experiment_log.md")
    print("Full process log saved to poster-experiment/process.log")

if __name__ == "__main__":
    main()
