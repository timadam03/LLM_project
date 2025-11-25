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
}]