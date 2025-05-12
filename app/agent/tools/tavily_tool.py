# app/agent/tools/tavily_tool.py
from langchain_core.tools import tool
import os
import requests

@tool
def tavily_search(query: str) -> str:
    """
    Search the web for recipe information using Tavily.
    Inputs:
        - query: A natural language string (e.g., 'Quick vegan dinner with broccoli')
    Returns:
        - A summarized result or top few search hits.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Missing Tavily API key."

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"query": query, "max_results": 3}
    url = "https://api.tavily.com/search"

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return f"Tavily API error: {response.status_code} - {response.text}"

    results = response.json().get("results", [])
    return "\n".join([r.get("content", "") for r in results])
