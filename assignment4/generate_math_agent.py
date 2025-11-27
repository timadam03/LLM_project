import json
import os
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to path so we can import the agent
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from aime_math_agent import solve_aime_problem

# Configuration
# Attempt to find the input file robustly
INPUT_FILE = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/data/aime24.jsonl"
if not os.path.exists(INPUT_FILE):
    # Check local relative path
    local_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "aime24.jsonl")
    if os.path.exists(local_input):
         INPUT_FILE = local_input
    else:
         INPUT_FILE = "assignment4/data/aime24.jsonl"

OUTPUT_FILE = "assignment4/results/aime24_results_math.jsonl"

NUM_ROLLOUTS = 4
TEMP = 0.6

def run_evaluation_loop():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    print(f"Starting Evaluation (N={NUM_ROLLOUTS}, T={TEMP})...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} not found.")
        return

    file_lock = threading.Lock()

    # Load all problems
    try:
        with open(INPUT_FILE, 'r') as f:
            problems = [json.loads(line) for line in f]
    except Exception as e:
        print(f"Failed to read input file: {e}")
        return

    # Open output file in append mode (or write to clear?) 
    # We clear it to start fresh
    with open(OUTPUT_FILE, 'w') as f:
        pass

    with open(OUTPUT_FILE, 'a') as f_out:
        for entry in problems:
            problem_text = entry.get('problem') or entry.get('question')
            gold_answer = entry.get('answer') or entry.get('solution')
            q_id = entry.get('id', 'unknown')

            print(f"Processing Problem ID {q_id}...")

            def run_single_rollout(rid):
                try:
                    # Call our agent
                    res_text, _ = solve_aime_problem(problem_text, max_turns=20)
                    return {
                        "status": "ok",
                        "rid": rid,
                        "output": res_text
                    }
                except Exception as err:
                    return {
                        "status": "error",
                        "rid": rid,
                        "msg": str(err)
                    }

            # Parallel execution
            with ThreadPoolExecutor(max_workers=NUM_ROLLOUTS) as pool:
                futures = {pool.submit(run_single_rollout, i): i for i in range(NUM_ROLLOUTS)}
                
                for fut in as_completed(futures):
                    result = fut.result()
                    if result["status"] == "ok":
                        row = {
                            "id": q_id,
                            "rollout_id": result["rid"],
                            "problem": problem_text,
                            "answer": gold_answer,
                            "llm_response": result["output"]
                        }
                        with file_lock:
                            f_out.write(json.dumps(row) + "\n")
                            f_out.flush()
                    else:
                        print(f"  Rollout {result['rid']} Error: {result['msg']}")

            print(f"Finished ID {q_id}. Pausing...")
            time.sleep(2)

    print(f"Evaluation Complete. Results in {OUTPUT_FILE}")

if __name__ == "__main__":
    run_evaluation_loop()
