from api import client
from tools import tools_list
from api import run_search
import json

# Map tool names to functions
available_tools = {
    "google_search": run_search
}
system_prompt = """You are a precise, helpful assistant.
You MUST output your final answer in strict JSON format with exactly one field:
1. "answer": The precise entity, date, name, or number requested.

CONSTRAINTS:
- No full sentences.
- No additional commentary or details.
- No trailing punctuation (e.g., "1972" NOT "1972.").
- No filler words (e.g., remove "The", "A", "It is").
- For numbers below 13, use words (e.g., "three" NOT "3").
- If the answer is a date, prioritize the Year and month (e.g., "November 1989") unless the specific day is asked for.

EXAMPLES:
User: "who wrote the harry potter books"
Assistant: {
    "answer": "J.K. Rowling"
}

User: "what is the capital of australia"
Assistant: {
    "answer": "Canberra"
}

User: "whats the height of the mount everest in meters"
Assistant: {
    "answer": "8,848.86 meters"
}

User: "when did the berlin wall fall"
Assistant: {
    "answer": "1989"
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
                    short_answer = data['answer']
                    print(f"Short answer: {short_answer}")
                    return short_answer, messages
                except json.JSONDecodeError:
                    # Fallback: Sometimes models (rarely) mess up even with json_object
                    print("Something went wrong with the response...")
                    print(f"Agent (Text): {content}")
                    return content, messages

        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return "Error: Max steps reached without answer", messages

def base_agent(query):
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
    short, messages = run_search_agent("who was the ruler of england in 1616?")
    short, messages = run_search_agent("when was the first hunger games book published?")