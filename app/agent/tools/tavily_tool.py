# app/agent/tools/tavily_tool.py
from langchain_core.tools import tool
import os
import requests
from typing import Optional

@tool
def tavily_search(query: str, search_depth: Optional[str] = "basic") -> str:
    """
    Search the web for recipe information or cooking techniques using Tavily.
    
    This tool has two main uses:
    1. Finding recipes when Spoonacular fails to return results
    2. Looking up specific cooking techniques or ingredient information
    
    Inputs:
        - query: A natural language search query.
          For recipes: "recipes using chicken broccoli lemon with keto diet restrictions"
          For techniques: "how to properly dice an onion" or "safe temperature for cooking pork"
        - search_depth: Optional parameter - use "deep" for more comprehensive recipe searches 
          or "basic" (default) for quick technique lookups.
          
    Returns:
        - For recipe searches: complete recipe information with ingredients and steps
        - For technique searches: detailed explanation of the cooking technique
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Missing Tavily API key."

    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Determine max results based on search type
    max_results = 5 if search_depth == "deep" else 3
    
    params = {
        "query": query, 
        "max_results": max_results,
        "search_depth": "advanced" if search_depth == "deep" else "basic"
    }
    
    url = "https://api.tavily.com/search"

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return f"Tavily API error: {response.status_code} - {response.text}"

    results = response.json().get("results", [])
    
    if not results:
        return "No relevant information found. Try different search terms."
        
    # Format results differently based on search type
    if "recipe" in query.lower() or "recipes" in query.lower():
        # Recipe search results - combine content for full recipe details
        combined_content = "\n\n".join([r.get("content", "") for r in results])
        return f"Recipe search results:\n{combined_content}"
    else:
        # Technique search - present each result separately
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append(f"Source {i+1}: {result.get('content', '')}")
        return "\n\n".join(formatted_results)
