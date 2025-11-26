#from math_aime_logic import run_math_agent, base_agent_hw4
#from api import client
import json
import os   
from openai import OpenAI


api_key = "sk-3399321b039a4cb29dca79d2280f3333"
client1 = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

system_prompt = """You are solving AIME (American Invitational Mathematics Examination) problems. 
OUTPUT FORMAT:
- You MUST put your final answer inside a single box at the very end of your response.
- Format: \\boxed{your_answer}
- Example: "Therefore, the answer is \\boxed{42}."""

num_rollouts = 4
temperature = 0.6
input_file = "/Users/timadam/Desktop/LLM_agents_project/LLM_project/assignment4/data/aime24.jsonl"
output_file_base = "/Users/timadam/Desktop/LLM_agents_project/LLM_project/assignment4/results/aime24_results_no_math.jsonl"
output_file_math = "/Users/timadam/Desktop/LLM_agents_project/LLM_project/assignment4/results/aime24_results_math.jsonl"

def generate_rollouts_base():
    # 1. Setup
    os.makedirs("assignment4/results/", exist_ok=True)
    
    print(f"Starting Rollout Generation (N={num_rollouts}, Temp={temperature})...")

    with open(input_file, 'r') as f_in, \
         open(output_file_base, 'w') as f_out:

        # 2. Process each question
        for line in f_in:
            entry = json.loads(line)
            
            # Extract fields based on your dataset format
            # (Adjust 'problem'/'question' key if your jsonl uses different names)
            problem_text = entry.get('problem', entry.get('question')) 
            gold_answer = entry.get('answer', entry.get('solution'))
            q_id = entry.get('id', 'unknown')

            print(f"Processing ID {q_id}...")

            # 3. The Rollout Loop (Run 4 times for the same question)
            for i in range(num_rollouts):
                try:
                    # Direct API Call (No Agent Loop, No Tools)
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": problem_text}
                        ],
                        temperature=temperature, # Higher temp = more diverse reasoning
                        stream=False
                    )
                    
                    llm_content = response.choices[0].message.content

                    # 4. Save exactly in the requested format
                    record = {
                        "id": q_id,
                        "rollout_id": i,  # 0, 1, 2, 3
                        "problem": problem_text,
                        "answer": gold_answer,
                        "llm_response": llm_content
                    }
                    
                    f_out.write(json.dumps(record) + "\n")
                    f_out.flush() # Ensure it writes immediately

                except Exception as e:
                    print(f"Error on rollout {i} for ID {q_id}: {e}")

    print(f"Done! Results saved to {output_file_base}")

if __name__ == "__main__":
    generate_rollouts_base()