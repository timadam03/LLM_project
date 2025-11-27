from api import client
from tools import tools_list
from api import run_search, browsing, calculator, wikipedia_search, get_weather
import json

# Map tool names to functions
available_tools = {
    "google_search": run_search,
    "website_browsing": browsing,
    "calculator": calculator,
    "wikipedia_search": wikipedia_search,
    "get_weather": get_weather
}
system_prompt = """You are a precise, helpful and reassuring assistant. You can search the web, browse full websites, calculate math, look up wikipedia, and check weather to find more information. Use these tools to find accurate and up-to-date information to answer the questions.
You MUST output your final answer in strict JSON format with exactly one field:
1. "answer": The precise entity, date, name, or number requested.

CONSTRAINTS:
- No full sentences.
- No additional commentary or details.
- No trailing punctuation (e.g., "1972" NOT "1972.").
- No filler words (e.g., remove "The", "A", "It is").
- For numbers below 13, use words (e.g., "three" NOT "3").
- If the answer is a date, prioritize the Year and month (e.g., "November 1989") unless the specific day is asked for.

Be thorough and accurate, ensuring you have the correct answer.

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
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    steps = 0

    #trajectory log that stores all information on each step to put into agent_trajectories.jsonl later
    trajectory_log = {
        "question": question,
        "steps": [],
        "final_answer": None
    }
    while steps < max_steps:
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools_list,
                response_format={"type": "json_object"},
                #timeout=10.0,
                stream=False
            )

            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                steps += 1
                print(f"Search Agent wants to use tools: {len(message.tool_calls)} call(s)")
                if message.content:
                    print(f"Agents reasoning: {message.content}")
                    
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                        
                    print(f"  - Tool: {function_name}")
                    print(f"  - Arguments: {function_args}")

                    if function_name in available_tools:
                        function_to_call = available_tools[function_name]
                        raw_results = function_to_call(**function_args)

                        # need to process the raw_results differently based on which tool was called
                        if function_name == "website_browsing":
                            content = raw_results.get("content","") 
                            title = raw_results.get("title","")
                            tool_response = content[:100000]    # limit to first 10k characters to avoid overloading model
                            # format for the trajectory, save records for this step
                            step_record = {
                                "step_numer": steps,
                                "action": "browsing",
                                "link": function_args.get("link", ""),
                                "num_docs_requested": 1,
                                "retrieved_documents": title}
                            
                            trajectory_log["steps"].append(step_record)

                        elif function_name == "google_search":
                            # convert the raw results (dict) to string readable for LLM
                            result_text = ""
                            num_docs_requested = len(raw_results)    # this is the num_documents for the trajectory
                            retrieved_documents = []
                            query = function_args.get("query", "")
                            for item in raw_results:
                                result_text += f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\nLink: {item.get('link')}\n---\n"
                                retrieved_documents.append({"title": item.get('title'),"snippet": item.get('snippet')}) #to get actual dictionary format of requested documents for trajectory
                            tool_response = result_text.strip()
                            
                            # format for the trajectory, save records for this step
                            step_record = {
                                "step_numer": steps,
                                "action": "search",
                                "query": query,
                                "num_docs_requested": num_docs_requested,
                                "retrieved_documents": retrieved_documents}
                            
                            trajectory_log["steps"].append(step_record)
                        
                        else:
                            # Handle other tools (calculator, wikipedia, weather)
                            tool_response = str(raw_results)
                            step_record = {
                                "step_numer": steps,
                                "action": function_name,
                                "args": function_args,
                                "result": tool_response
                            }
                            trajectory_log["steps"].append(step_record)

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
                    short_answer = data.get("answer","")
                    print(f"Short answer: {short_answer}")
                    trajectory_log["final_answer"] = short_answer
                    return short_answer, messages, trajectory_log
                except json.JSONDecodeError:
                    # Fallback: Sometimes models (rarely) mess up even with json_object
                    print("Something went wrong with the response...")
                    print(f"Agent (Text): {content}")
                    return content, messages, trajectory_log

        except Exception as e:
            print(f"An error occurred: {e}")
            break
    return "Error: Max steps reached without answer", messages, trajectory_log

def run_base_agent(query):
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
    #short, messages, traj_log = run_search_agent("who was the ruler of england in 1616?")
    short, messages, traj_log = run_search_agent("Calculate 25 * 48 and tell me the weather in Paris")
    print(traj_log)
