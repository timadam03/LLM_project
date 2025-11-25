from api import client
import json

example = ['The president of the United States (POTUS) is the head of state and head of government of the United States. The president directs the executive branch of the ...', 'President Donald J. Trump is returning to the White House to build upon his previous successes and use his mandate to reject the extremist policies.', 'Donald J. Trump. President of the United States · JD Vance. VICE PRESIDENT OF THE UNITED STATES · Melania Trump. First Lady OF THE UNITED STATES · The Cabinet. Of ...']

def convert(result_list):
    final_result = ""
    for result in result_list:
        result = result.removesuffix("...")
        final_result += result.strip() + "," + "\n"
    print(final_result)


system_prompt = "You are a helpful assistant"
def base_agent(query):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            #response_format={"type": "json_object"},
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
    base_agent("who is the president of the United States")