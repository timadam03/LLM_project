from api import client #using the initialized client from api.py from group project
import json
import os
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix imports for extract_boxed_answer since we moved the file
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
try:
    from aime_math_agent import find_boxed_answer
except ImportError:
    # Define fallback if import fails (to avoid breaking base generation)
    def find_boxed_answer(text):
        if not text: return None
        if "\\boxed{" in text:
            return text.split("\\boxed{")[1].split("}")[0] # primitive fallback
        return None

# Configuration of input/output path and parameters
# Set paths for uni gpu cluster, to run in background
INPUT_FILE = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/data/aime24.jsonl"
if not os.path.exists(INPUT_FILE):
    # Check local relative path
    local_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "aime24.jsonl")
    if os.path.exists(local_input):
         INPUT_FILE = local_input
    else:
         INPUT_FILE = "assignment4/data/aime24.jsonl"

OUTPUT_FILE = "assignment4/results/aime24_results_nomath_1.jsonl"

num_rollouts = 4
temperature = 0.6
model = "deepseek-chat"

system_prompt = """You are solving AIME (American Invitational Mathematics Examination) problems. 
OUTPUT FORMAT:
- You MUST put your final answer inside a single box at the very end of your response.
- Format: \\boxed{your_answer}
- Example: "Therefore, the answer is \\boxed{42}."""

def generate_rollouts_base():
    # 1. Setup
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    print(f"Starting FAST Rollout Generation (N={num_rollouts}, Temp={temperature})...")

    # We need a lock so multiple threads don't scramble the file writing
    file_lock = threading.Lock()

    try:
        with open(INPUT_FILE, 'r') as f:
            pass
    except FileNotFoundError:
        print(f"Error: Input file {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r') as f_in, \
         open(OUTPUT_FILE, 'w') as f_out:

        # 2. Process each question
        for line in f_in:
            entry = json.loads(line)
            
            problem_text = entry.get('problem', entry.get('question')) 
            gold_answer = entry.get('answer', entry.get('solution'))
            q_id = entry.get('id', 'unknown')

            print(f"Processing ID {q_id} (Launching {num_rollouts} parallel requests)...")

            # --- Helper Function for a Single Request ---
            def fetch_rollout(rollout_index):
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": problem_text}
                        ],
                        temperature=temperature,
                        stream=False,
                        timeout=60 # Give math problems time to think
                    )
                    
                    full_content = response.choices[0].message.content
                    
                    # Extract only the final boxed answer for the "llm_response" field
                    extracted = find_boxed_answer(full_content)
                    
                    # If extraction succeeds, format it nicely. If not, keep full text for debugging.
                    final_response_text = f"The answer is \\boxed{{{extracted}}}" if extracted else full_content

                    return {
                        "status": "success",
                        "rollout_id": rollout_index,
                        "llm_response": final_response_text
                    }
                except Exception as e:
                    return {
                        "status": "error", 
                        "rollout_id": rollout_index, 
                        "error": str(e)
                    }

            # --- Parallel Execution Block ---
            # We run all 4 rollouts AT THE SAME TIME using threads
            with ThreadPoolExecutor(max_workers=num_rollouts) as executor:
                # Submit all 4 tasks
                future_to_id = {
                    executor.submit(fetch_rollout, i): i 
                    for i in range(num_rollouts)
                }

                # Process them as they finish
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
                        
                        # Write safely using the lock
                        with file_lock:
                            f_out.write(json.dumps(record) + "\n")
                            f_out.flush()
                    else:
                        print(f"Error on rollout {result['rollout_id']} for ID {q_id}: {result['error']}")

            # To let API rate cool down and not get Errors
            print(f"Finished ID {q_id}. Cooling down for 5 seconds...")
            time.sleep(5) 

    print(f"Done! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_rollouts_base()
