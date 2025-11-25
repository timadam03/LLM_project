import os
from openai import OpenAI
from dotenv import load_dotenv
import http.client
import json

load_dotenv()
ds_key = os.environ.get('DS_API_KEY')
serper_key = os.environ.get('SERPER_API_KEY')

#deepseek api client
client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")



def run_search(query):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
    "q": query,
    })
    headers = {
    'X-API-KEY': serper_key,
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    response_dict = json.loads(data.decode("utf-8"))
    results_list = response_dict["organic"]
    
    result_snippets = [result['snippet'] for result in results_list[:3]]
    final_result = ""
    for result in result_snippets:
        result = result.removesuffix("...")
        final_result += result.strip() + "\n"
    return final_result





if __name__ == "__main__":
    print(run_search("who is the president of the United States"))