from api import client
from tools import tools_list
from api import run_search
import json

# Map tool names to functions
available_tools = {
    "google_search": run_search
}
system_prompt = """You are a helpful search agent.
You MUST output your final answer in strict JSON format with exactly two fields:
1. "short_answer": A concise single sentence or date.
2. "detailed_answer": A full explanation with context and sources.

Example Output:
{
    "short_answer": "Donald Trump (2017-2021, 2025-Present)",
    "detailed_answer": "Donald Trump served as the 45th president..."
}
"""

def run_search_agent(question, max_steps=5):
    """
    Search agent loop that accepts user input and interacts with the LLM.
    """
    #print("Search Agent initialized. Type 'quit' to exit.")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    steps = 0
    final_answer = ""
    while steps < max_steps:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools_list,
                response_format={"type": "json_object"},
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
                try:
                    data = json.loads(content)
                    short_answer = data['short_answer']
                    detailed_answer = data['detailed_answer']
                    print(f"Short answer: {short_answer}")
                    print(f"Detailed answer: {detailed_answer}")
                    return short_answer, detailed_answer, messages
                except json.JSONDecodeError:
                    # Fallback: Sometimes models (rarely) mess up even with json_object
                    print("Something went wrong with the response...")
                    print(f"Agent (Text): {content}")
                    return content, None, messages

        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return "Error: Max steps reached without answer", None, messages

def base_agent(query):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": query},
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    short, detail, messages = run_search_agent("who was the ruler of england in 1616?")
    print("Short answer: ", short)
    print("Details: ", detail)

