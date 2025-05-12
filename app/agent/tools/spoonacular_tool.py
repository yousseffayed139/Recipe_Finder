# app/agent/tools/spoonacular_tool.py
from langchain_core.tools import tool
import os
import requests
from typing import List, Optional

@tool
def spoonacular_search(ingredients: List[str], diet: Optional[str] = None,
                       allergies: Optional[List[str]] = None,
                       cuisine: Optional[str] = None,
                       prep_time: Optional[int] = None) -> str:
    """
    Search for recipes using the Spoonacular API.
    Inputs:
        - ingredients: List of ingredients available
        - diet: Diet preference (e.g., vegetarian, keto)
        - allergies: List of allergies (e.g., nuts, dairy)
        - cuisine: Desired cuisine type
        - prep_time: Maximum preparation time in minutes
    Returns:
        - A list of recipe titles and links.
    """
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        return "Missing Spoonacular API key."

    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": api_key,
        "includeIngredients": ",".join(ingredients),
        "diet": diet,
        "intolerances": ",".join(allergies or []),
        "cuisine": cuisine,
        "maxReadyTime": prep_time,
        "number": 5
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Spoonacular API error: {response.status_code} - {response.text}"
    
    data = response.json().get("results", [])
    if not data:
        return "No matching recipes found."
    
    return "\n".join([f"- {r['title']}" for r in data])
