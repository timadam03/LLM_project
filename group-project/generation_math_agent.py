#from api import client
import json
import os
import time
import threading
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

api_key = "sk-3399321b039a4cb29dca79d2280f3333"
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
# --- CONFIGURATION ---
input_file = "assignment4/data/aime24.jsonl" 
# Switching output to the 'math' version since we are using tools now
output_file = "assignment4/results/aime24_results_math.jsonl"

num_rollouts = 4
temperature = 0.6
model = "deepseek-chat"

system_prompt = """You are solving AIME (American Invitational Mathematics Examination) problems. Be accurate and exact.

You have access to Python code execution via the execute_python_code tool. Use it to perform calculations, verify solutions, or explore patterns.

OUTPUT FORMAT:
- You MUST put your final answer inside a single box at the very end of your response.
- Format: \\boxed{your_answer}
- Example: "Therefore, the answer is \\boxed{42}."

Available Python modules: math, fractions, itertools, sympy, numpy"""

# --- TOOL DEFINITIONS ---

def execute_code(code: str):
    """
    Executes Python code in a safe, isolated subprocess.
    """
    try:
        # 1. Run the code in a separate process
        result = subprocess.run(
            [sys.executable, "-c", code], 
            capture_output=True, 
            text=True, 
            timeout=15  # Safety: Kill after 15 sec
        )
        
        # 2. Check for success
        if result.returncode == 0:
            output = result.stdout
            if not output:
                return "Code executed successfully (No output printed)."
            return f"Output:\n{output}"
        else:
            return f"Error:\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (ran longer than 15 seconds)."
    except Exception as e:
        return f"System Error executing code: {str(e)}"

def extract_boxed_answer(text):
    """
    Extracts the content inside the last \boxed{...} from the text.
    """
    if not text: 
        return None
    start_marker = "\\boxed{"
    start_index = text.rfind(start_marker)
    if start_index == -1:
        return None
    content_start = start_index + len(start_marker)
    balance = 1
    current_pos = content_start
    while current_pos < len(text) and balance > 0:
        char = text[current_pos]
        if char == "{":
            balance += 1
        elif char == "}":
            balance -= 1
        current_pos += 1
    if balance == 0:
        return text[content_start : current_pos - 1].strip()
    return None

# Tool Schema for LLM
math_tools = [{
    "type": "function",
    "function": {
        "name": "execute_python_code",
        "description": "Execute Python code to perform calculations and verify solutions",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
    }
}]

available_tools = {
    "execute_python_code": execute_code
}

# --- AGENT LOGIC ---

def run_math_agent(problem, max_steps=5):
    """
    Runs the ReAct loop for a single math problem.
    Returns: (final_answer_string, messages_history)
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": problem}
    ]
    steps = 0
    
    while steps < max_steps:
        try:
            # 1. Call LLM
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=math_tools,
                temperature=temperature,
                stream=False,
            )

            message = response.choices[0].message
            messages.append(message)

            # 2. Tool Execution Branch
            if message.tool_calls:
                steps += 1
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name in available_tools:
                            # Execute Code
                            tool_output = available_tools[function_name](**function_args)
                            
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": str(tool_output)
                            })
                        else:
                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": "Error: Tool not found"
                            })
                    except Exception as e:
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": f"Error executing tool: {e}"
                        })
                continue # Loop back to let LLM see output
            
            # 3. Final Answer Branch
            else:
                content = message.content
                if not content:
                    return "Error: Empty response", messages
                
                # Try to extract \boxed{answer}
                extracted = extract_boxed_answer(content)
                if extracted:
                    return f"The answer is \\boxed{{{extracted}}}", messages
                else:
                    # Return full content if box missing (so we can see reasoning)
                    return content, messages

        except Exception as e:
            return f"Error in loop: {e}", messages
            
    return "Error: Max steps reached", messages

# --- PARALLEL GENERATION ---

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
                    final_ans, history = run_math_agent(problem_text)
                    
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
                        print(f"  ❌ Error on rollout {result['rollout_id']}: {result['error']}")

            print(f"Finished ID {q_id}. Cooling down for 5 seconds...")
            time.sleep(5) 

    print(f"Done! Results saved to {output_file}")

if __name__ == "__main__":
    generate_rollouts_math()