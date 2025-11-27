from api import client #using the initialized client from api.py from group project
import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from aime_math_agent import extract_boxed_answer

# Configuration of input/output path and parameters
# Set paths for uni gpu cluster, to run in background
input_file = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/data/aime24.jsonl"
output_file_base = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/results/aime24_results_no_math.jsonl"

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
    os.makedirs("results/", exist_ok=True)
    
    print(f"Starting FAST Rollout Generation (N={num_rollouts}, Temp={temperature})...")

    # We need a lock so multiple threads don't scramble the file writing
    file_lock = threading.Lock()

    with open(input_file, 'r') as f_in, \
         open(output_file_base, 'w') as f_out:

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
                    extracted = extract_boxed_answer(full_content)
                    
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

    print(f"Done! Results saved to {output_file_base}")

if __name__ == "__main__":
    generate_rollouts_base()
