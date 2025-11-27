import os
from openai import OpenAI
from dotenv import load_dotenv
import http.client
import json
import requests
import wikipedia
import pathlib

# Load from the directory where this file is located
env_path = pathlib.Path(__file__).parent / '.env'
print(f"Loading env from: {env_path}")
print(f"Exists? {env_path.exists()}")
load_dotenv(dotenv_path=env_path)

ds_key = os.environ.get('DS_API_KEY')
print(f"DS_API_KEY found: {ds_key is not None}")
if ds_key:
    print(f"DS_API_KEY starts with: {ds_key[:5]}")

serper_key = os.environ.get('SERPER_API_KEY')

#deepseek api client
try:
    client = OpenAI(api_key=ds_key, base_url="https://api.deepseek.com")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None


def get_pure_content(response_dict, num): #use this one to only return one big content string, num defines how many top results to include
    results_list = response_dict["organic"]
    
    result_snippets = [result['snippet'] for result in results_list[:num]]
    final_result = ""
    for result in result_snippets:
        result = result.removesuffix("...")
        final_result += result.strip() + "\n"
    return final_result

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

    #return get_pure_content(response_dict)
    #print(response_dict.get("organic", [])[:3])
    return response_dict.get("organic", [])[:3] #to return top3 results with title, snippet etc, for building trajectories

def dict_structure(d, indent=0): #can use to get the json structure of responses etc
    spacing = "  " * indent
    if isinstance(d, dict):
        for key, value in d.items():
            print(f"{spacing}- {key}: {type(value).__name__}")
            dict_structure(value, indent + 1)
            

def browsing(link): #using serper apis webpage function to scrape a whole website via its link/url
    conn = http.client.HTTPSConnection("scrape.serper.dev")
    payload = json.dumps({
    "url": link,
    })
    headers = {
    'X-API-KEY': serper_key,
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #print(type(data))
    data_dict = json.loads(data)
    content = data_dict.get("text", "")
    metadata = data_dict.get("metadata", "")
    title = metadata.get("title") or metadata.get("twitter:title") or metadata.get("og:title") or "" #check different title keys
    print(f"Reading this website: {title}\n Content: {content[:100]}...")
    response_dict = {
        "title": title,
        "content": content}
    return response_dict

    #dict_structure(data_dict)
    #implement logic to return important content to model, so it reads full model

def calculator(expression):
    """Safely evaluate a mathematical expression."""
    try:
        # limited safe scope
        return str(eval(expression, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"

def wikipedia_search(query):
    """Search Wikipedia and return a summary."""
    try:
        return wikipedia.summary(query, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return "Page not found."
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"

def get_weather(location):
    """Get current weather for a location using OpenMeteo."""
    try:
        # 1. Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_res = requests.get(geo_url).json()
        
        if not geo_res.get("results"):
            return f"Could not find location: {location}"
            
        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        name = geo_res["results"][0]["name"]
        country = geo_res["results"][0].get("country", "")
        
        # 2. Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url).json()
        
        current = weather_res.get("current_weather", {})
        temp = current.get("temperature")
        wind = current.get("windspeed")
        
        return f"Current weather in {name}, {country}: {temp}°C, Wind: {wind} km/h"
        
    except Exception as e:
        return f"Error getting weather: {str(e)}"

if __name__ == "__main__":
    #print(run_search("who is the president of the United States"))
    links = ["https://www.cnbc.com/2025/11/23/trump-port-of-los-angeles-containership-fire.html",
             "https://en.wikipedia.org/wiki/Artificial_intelligence","https://www.bpir.com/history-of-quality-tqm-and-business-excellence/","https://www.nytimes.com/2025/11/24/us/politics/trump-russia-ukraine-peace-plan-middle-ground.html"]
