import json
import os
import time
import threading
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

current_dir = os.path.dirname(os.path.abspath(__file__))
group_proj_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'group-project')

if group_proj_path not in sys.path:
    sys.path.insert(0, group_proj_path)

try:
    from api import client
except ImportError:
    client = None

def run_python_code(script: str):
    """
    Executes Python script in a separate process.
    Captures stdout and stderr for the agent.
    """
    try:
        process = subprocess.run(
            [sys.executable, "-c", script], 
            capture_output=True, 
            text=True, 
            timeout=40 
        )
        
        if process.returncode == 0:
            std_out = process.stdout
            if not std_out:
                return "Code ran successfully (No output)."
            return f"Standard Output:\n{std_out}"
        else:
            return f"Execution Error:\n{process.stderr}"

    except subprocess.TimeoutExpired:
        return "Error: Execution timed out."
    except Exception as e:
        return f"System Error: {str(e)}"

def find_boxed_answer(text):
    """
    Helper to find \boxed{...} in the text.
    """
    if not text: 
        return None
    marker = "\\boxed{"
    idx = text.rfind(marker)
    if idx == -1:
        return None
        
    start = idx + len(marker)
    count = 1
    ptr = start
    while ptr < len(text) and count > 0:
        if text[ptr] == "{":
            count += 1
        elif text[ptr] == "}":
            count -= 1
        ptr += 1
        
    if count == 0:
        return text[start : ptr - 1].strip()
    return None

tools_list = [{
    "type": "function",
    "function": {
        "name": "run_python_code",
        "description": "Executes Python code to calculate results.",
        "parameters": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The Python script to run."
                }
            },
            "required": ["script"]
        }
    }
}]

tool_registry = {
    "run_python_code": run_python_code
}

sys_prompt = """You are a math assistant for AIME problems.
You have a 'run_python_code' tool.

GUIDELINES:
1. Write complete scripts to solve the problem.
2. PRINT the answer. The tool only returns stdout.
3. Use libraries like math, fractions, itertools, sympy, numpy.
4. Be efficient.

Final Answer format: \\boxed{answer}
"""

def solve_aime_problem(problem_text, max_turns=20):
    """
    Main agent loop.
    """
    if not client:
         try:
             from api import client as c
         except:
            return "Error: API client not initialized.", []
    
    if not client:
        return "Error: API client not initialized.", []

    convo = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": problem_text}
    ]
    
    turn = 0
    temperature = 0.6 
    
    while turn < max_turns:
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=convo,
                tools=tools_list,
                temperature=temperature,
                stream=False,
            )

            msg = resp.choices[0].message
            convo.append(msg)

            if msg.tool_calls:
                turn += 1
                for tc in msg.tool_calls:
                    fname = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                        script_val = args.get('script', args.get('code'))
                        
                        if fname in tool_registry:
                            output = tool_registry[fname](script_val)
                            convo.append({
                                "tool_call_id": tc.id,
                                "role": "tool",
                                "name": fname,
                                "content": str(output)
                            })
                        else:
                             convo.append({
                                "tool_call_id": tc.id,
                                "role": "tool",
                                "name": fname,
                                "content": "Error: Unknown tool"
                            })
                    except Exception as e:
                        convo.append({
                            "tool_call_id": tc.id,
                            "role": "tool",
                            "name": fname,
                            "content": f"Error: {e}"
                        })
                continue
            
            else:
                content = msg.content
                if not content:
                    return "Error: No content", convo
                
                extracted = find_boxed_answer(content)
                if extracted:
                    return f"The answer is \\boxed{{{extracted}}}", convo
                else:
                    return content, convo

        except Exception as e:
            return f"Loop Error: {e}", convo
            
    return "Error: Limit reached", convo
