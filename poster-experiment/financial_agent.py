import sys
import os
import json

# Add parent directory to path to import tools and api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'group-project')))

from api import client, run_search, browsing, calculator, wikipedia_search, get_weather
from tools import tools_list

# Map tool names to functions
available_tools = {
    "google_search": run_search,
    "website_browsing": browsing,
    "calculator": calculator,
    "wikipedia_search": wikipedia_search,
    "get_weather": get_weather
}

financial_analyst_prompt = """You are an expert Financial Analyst AI. Your goal is to perform a Discounted Cash Flow (DCF) valuation for a given public company.

You must strictly follow this process:
1.  **Gather Data**: Use `google_search` to find the latest financial metrics (as of {current_date}):
    *   Current Share Price & Shares Outstanding.
    *   Free Cash Flow (FCF) for the trailing twelve months (TTM).
    *   Net Debt (Total Debt - Cash).
    *   Beta (for WACC calculation).
    *   Risk-Free Rate (use 10-year US Treasury yield).
3.  **Market Sentiment & News**:
    *   **Reddit**: Search for "site:reddit.com {ticker} stock analysis {current_year}" to gauge retail sentiment.
    *   **News**: Search for "{ticker} stock news {current_year}" to find major recent headlines (earnings, product launches, legal issues).
4.  **Determine Assumptions**:
    *   **Growth Rate**: Search for analyst consensus revenue/earnings growth rates for the next 5 years. Look for qualitative justifications (e.g., "expanding into new markets").
    *   **WACC**: Calculate Weighted Average Cost of Capital. Assume Equity Risk Premium is 5.0%. Formula: WACC = RiskFree + Beta * 5.0. (Simplify by assuming 100% equity financing for this rapid estimate, or find the actual WACC).
    *   **Terminal Growth Rate**: Use 2.5% (standard GDP growth proxy) unless you find specific reasons otherwise.
5.  **Calculate Valuation**:
    *   Perform the DCF calculation.
    *   **EFFICIENCY TIP**: You can calculate the sum of PVs in a single calculator step if you construct the formula correctly (e.g., `FCF * (1+g) / (1+r) + FCF * (1+g)**2 / (1+r)**2 ...`). Do NOT perform one tool call per year if you can combine them.
    *   Equity Value = Sum of PVs - Net Debt.
    *   Intrinsic Value per Share = Equity Value / Shares Outstanding.
6.  **Output**: Provide a structured JSON response.

You have access to a calculator tool. USE IT for all math.

OUTPUT FORMAT:
You must output a JSON object with the following structure:
{
    "thinking_process": "Step-by-step reasoning regarding data quality, assumption choices, and calculation logic.",
    "company": "Ticker/Name",
    "valuation_date": "{current_date}",
    "current_price": <float>,
    "estimated_value": <float>,
    "upside_downside": "<percentage string>",
    "assumptions": {
        "growth_rate": "<percentage string> (Source: <citation>)",
        "wacc": "<percentage string> (Source: <citation>)",
        "terminal_growth": "2.5%"
    },
    "market_sentiment": {
        "reddit_sentiment": "Bullish/Bearish/Neutral",
        "reddit_summary": "Key points from Reddit discussion.",
        "recent_news_summary": "Key recent news headlines.",
        "news_source": "<URL>"
    },
    "reasoning": "A concise paragraph explaining the valuation, citing the qualitative factors found in search that justify the growth rate."
}

Constraints:
- Be conservative in your estimates.
- If you cannot find exact FCF, estimate it as "Cash from Operations - Capital Expenditures".
- Always cite the source (e.g., "Yahoo Finance", "Morningstar", "Q3 Earnings Call") in the assumptions strings.
"""

def run_financial_agent(ticker, max_steps=40, persona="Expert Financial Analyst"):
    """
    Specialized agent for financial valuation.
    """
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().strftime("%Y")
    
    # Agent should know the date explicitly in the system prompt as well
    date_context = f"Today's date is {current_date}."
    
    query = f"Perform a DCF valuation for {ticker} as of {current_date}. Find latest FCF, shares, beta, growth outlook, Reddit sentiment, and recent news."
    
    # Format prompt with dynamic date
    formatted_prompt = financial_analyst_prompt.replace("{current_date}", current_date).replace("{current_year}", current_year).replace("{ticker}", ticker)
    
    # Inject Persona
    formatted_prompt = f"ROLE: {persona}\n" + formatted_prompt

    # Force the model to know it doesn't have the data
    messages = [
        {"role": "system", "content": date_context + "\n" + formatted_prompt + "\n\nCRITICAL INSTRUCTION: You have NO internal knowledge of today's stock prices or financial metrics. You MUST use 'google_search' or 'website_browsing' to find the current price, FCF, and shares outstanding BEFORE doing any calculations."},
        {"role": "user", "content": query}
    ]
    steps = 0

    print(f"\n--- Starting Valuation for {ticker} ---\n")

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
                print(f"Step {steps}: Agent chose {len(message.tool_calls)} tool(s)")
                
                if message.content:
                    print(f"Thought: {message.content}")
                    
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"  -> Calling {function_name} with {function_args}")

                    if function_name in available_tools:
                        function_to_call = available_tools[function_name]
                        try:
                            raw_results = function_to_call(**function_args)
                        except Exception as tool_err:
                            raw_results = f"Error calling tool: {str(tool_err)}"

                        # Format results for the model
                        if function_name == "google_search":
                            tool_response = ""
                            if isinstance(raw_results, list):
                                for item in raw_results:
                                    tool_response += f"Title: {item.get('title')}\nSnippet: {item.get('snippet')}\nSource: {item.get('link')}\n---\n"
                            else:
                                tool_response = str(raw_results)
                        elif function_name == "website_browsing":
                            if isinstance(raw_results, dict):
                                tool_response = raw_results.get("content", "")[:5000] # Limit context
                            else:
                                tool_response = str(raw_results)[:5000] # Limit context if string error
                        else:
                            tool_response = str(raw_results)

                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": "Result: " + tool_response
                        })
                    else:
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": "Error: Tool not found"
                        })
            else:
                # Final answer
                content = message.content
                try:
                    result_json = json.loads(content)
                    print(f"\n--- Valuation Complete for {ticker} ---")
                    print(json.dumps(result_json, indent=2))
                    return result_json
                except json.JSONDecodeError:
                    print("Error decoding JSON response.")
                    print(content)
                    return content

        except Exception as e:
            print(f"An error occurred: {e}")
            break
            
    return None

if __name__ == "__main__":
    # Simple test
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = "AAPL"
        
    run_financial_agent(ticker)

