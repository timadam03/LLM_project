from api import client
from tools import math_tools
import math
import fractions
import json
import itertools
import sympy as sp
import numpy as np
import sys
import subprocess

system_prompt = """You are solving AIME (American Invitational Mathematics Examination) problems, Be accurate and exact.

You have access to Python code execution via the execute_python_code tool. Use it to perform calculations, verify solutions, or explore patterns.

OUTPUT FORMAT:
- You MUST put your final answer inside a single box at the very end of your response.
- Format: \\boxed{your_answer}
- Example: "Therefore, the answer is \\boxed{42}."

Available Python modules: math, fractions, itertools, sympy, numpy"""

def execute_code(code: str):
    """
    Executes Python code in a safe, isolated subprocess.
    """
    try:
        # 1. Run the code in a separate process
        # capture_output=True grabs what would print to terminal
        # text=True decodes bytes to string
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
        return "Error: Code execution timed out (ran longer than 10 seconds)."
    except Exception as e:
        return f"System Error executing code: {str(e)}"

# helper function to extract the answer of the final output of math model
def extract_boxed_answer(text):
    """
    Extracts the content inside the last \boxed{...} from the text.
    Handles nested brackets like \boxed{\frac{1}{2}} correctly.
    """
    if not text: 
        return None
        
    # Look for the LAST occurrence of \boxed{ to get the final answer
    start_marker = "\\boxed{"
    start_index = text.rfind(start_marker)
    
    if start_index == -1:
        return None
        
    # Start scanning after \boxed{
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
        
    # If we exited loop with balance 0, we found the closing bracket
    if balance == 0:
        return text[content_start : current_pos - 1].strip()
        
    return None


# Map tool names to functions
available_tools = {
    "execute_python_code": execute_code
}

def run_math_agent(problem, max_steps=5):
    """
    Search agent loop that accepts user input and interacts with the LLM.
    """
    #print("Search Agent initialized. Type 'quit' to exit.")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": problem}
    ]
    steps = 0
    final_answer = ""
    while steps < max_steps:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=math_tools,
                #response_format={"type": "json_object"},
                stream=False
            )

            message = response.choices[0].message
            messages.append(message)

            if message.tool_calls:
                steps += 1
                print(f"Search Agent wants to use tools: {len(message.tool_calls)} call(s)")
                    
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                        
                    print(f"  - Tool: {function_name}")
                    print(f"  - Arguments: {function_args}")

                    if function_name in available_tools:
                        function_to_call = available_tools[function_name]
                        tool_response = function_to_call(**function_args)
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": "Here is the result: " + str(tool_response),
                        })
                    else:
                        print(f"Error: Tool {function_name} not found.")
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": "Error: Tool not found",
                        })
                
            else:
                # Tool calls is empty, meaning model has its final answer
                content = message.content
                if not content:
                    return "Error: Empty response", None, messages
                answer = extract_boxed_answer(content)
                if answer is not None:
                    print(f"Final Answer extracted: {answer}")
                    return answer, messages
                else:
                    print("No boxed answer found in the final response., Returning full content.")
                    return content, messages

        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return "Error: Max steps reached without answer", messages

def base_agent_hw4(query):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            response_format={"type": "json_object"},
            stream=False
        )
        try:
            content = response.choices[0].message.content
            if not content:
                return "Error: Empty response"
            data = json.loads(content)
            short_answer = data['answer']
            print(f"Short answer: {short_answer}")
            return short_answer
        except json.JSONDecodeError:
            # Fallback: Sometimes models (rarely) mess up even with json_object
            print("Something went wrong with the response...")
            print(f"Agent (Text): {content}")
            return content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    code1 = """
x = 10
y = A
print(f"The result is {x * y}")
"""
    code_math = """
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(f"The 10th Fibonacci number is: {fib(10)}")
"""
    code_fractions = """
from fractions import Fraction

f1 = Fraction(1, 3)
f2 = Fraction(2, 5)
result = f1 + f2
print(f"1/3 + 2/5 = {result}")
print(f"Decimal value: {float(result)}")
"""
    code_numpy = """
import numpy as np

arr = np.array([1, 2, 3, 4, 5])
squared = arr ** 2
mean_val = np.mean(squared)

print(f"Original: {arr}")
print(f"Squared: {squared}")
print(f"Mean of squared: {mean_val}")
"""
    print(execute_code(code_fractions))