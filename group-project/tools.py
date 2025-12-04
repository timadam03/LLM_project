tools_list = [{
    "type": "function",
    "function": {
        "name": "google_search",
        "description": "Search Google for current information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "website_browsing",
        "description": "Read full content of the website",
        "parameters": {
            "type": "object",
            "properties": {
                "link": {"type": "string", "description": "The link for the website"}
            },
            "required": ["link"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Perform mathematical calculations. Use Python syntax (e.g., 2+2, 3*5).",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The mathematical expression to evaluate"}
            },
            "required": ["expression"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "wikipedia_search",
        "description": "Search Wikipedia for a summary of a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic to search for"}
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city name (e.g. London, New York)"}
            },
            "required": ["location"]
        }
    }
}]
