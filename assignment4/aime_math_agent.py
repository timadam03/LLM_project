from api import client #using the initialized client from api.py from group project
import json
import os
import time
import threading
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            timeout=45  # Safety: Kill after 45 sec
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

# Configuration of input/output path and parameters
# Set paths for uni gpu cluster, to run in background
input_file = "/store/comp4901b/tladam/COMP4901B-LLMs/assignment4/data/aime24.jsonl" 
# Switching output to the 'math' version since we are using tools now
output_file = "assignment4/results/aime24_results_math.jsonl"

system_prompt = """You are an expert mathematics assistant solving AIME problems. 
You have access to a Python interpreter (`execute_python_code`).

CRITICAL STRATEGY FOR EFFICIENCY:
1. **Batch Your Code**: Do NOT run single lines of code. Write a SINGLE, COMPLETE Python script that solves the entire problem (or a major part of it) in one turn.
2. **Print Everything**: The tool only returns what you `print()`. Print all intermediate variables and the final result clearly.
3. **Use Brute Force**: AIME problems often involve integers. Python loops/simulations are often faster and more reliable than symbolic algebra.
4. **No conversational filler**: Go straight to the code or reasoning.

When you have the result, you MUST format it as:
\\boxed{answer}

Available libraries: math, fractions, itertools, sympy, numpy
"""

def run_math_agent(problem, max_steps=20):
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
                model="deepseek-chat",
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