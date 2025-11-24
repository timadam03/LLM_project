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
}]