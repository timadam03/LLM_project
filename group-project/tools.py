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
math_tools = [{
    "type": "function",
    "function": {
        "name": "execute_python_code",
        "description": "Execute Python code to perform calculations and verify solutions",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
    }
}]