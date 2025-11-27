import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from aime_math_agent import run_math_agent, extract_boxed_answer

# Configuration of input/output path and parameters
# Set paths for uni gpu cluster, to run in background
input_file = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/data/aime24.jsonl" 
# Switching output to the 'math' version since we are using tools now
output_file = "assignment4/results/aime24_results_math.jsonl"

num_rollouts = 4
temperature = 0.6
model = "deepseek-chat"

# Using different threads to run rollouts parallelly

def generate_rollouts_math():
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    print(f"Starting MATH AGENT Rollout (N={num_rollouts}, Temp={temperature})...")

    file_lock = threading.Lock()

    with open(input_file, 'r') as f_in, \
         open(output_file, 'w') as f_out:

        for line in f_in:
            entry = json.loads(line)
            problem_text = entry.get('problem', entry.get('question'))
            gold_answer = entry.get('answer', entry.get('solution'))
            q_id = entry.get('id', 'unknown')

            print(f"Processing ID {q_id} (Launching {num_rollouts} agents)...")

            # Wrapper to run the agent logic inside the thread pool
            def fetch_rollout(rollout_index):
                try:
                    # Call the Agent Loop
                    final_ans, messages = run_math_agent(problem_text)
                    
                    return {
                        "status": "success",
                        "rollout_id": rollout_index,
                        "llm_response": final_ans
                    }
                except Exception as e:
                    return {
                        "status": "error", 
                        "rollout_id": rollout_index, 
                        "error": str(e)
                    }

            # Run 4 Agents in Parallel
            with ThreadPoolExecutor(max_workers=num_rollouts) as executor:
                future_to_id = {
                    executor.submit(fetch_rollout, i): i 
                    for i in range(num_rollouts)
                }

                for future in as_completed(future_to_id):
                    result = future.result()
                    
                    if result["status"] == "success":
                        record = {
                            "id": q_id,
                            "rollout_id": result["rollout_id"],
                            "problem": problem_text,
                            "answer": gold_answer,
                            "llm_response": result["llm_response"]
                        }
                        
                        with file_lock:
                            f_out.write(json.dumps(record) + "\n")
                            f_out.flush()
                    else:
                        print(f"Error on rollout {result['rollout_id']}: {result['error']}")

            print(f"Finished ID {q_id}. Cooling down for 5 seconds...")
            time.sleep(5) 

    print(f"Done! Results saved to {output_file}")

if __name__ == "__main__":
    generate_rollouts_math()