from langchain.tools import tool
import requests
import os

@tool
def search_recipes(preferences: dict) -> list:
    """
    Search for recipes using an external recipe API based on user preferences.
    Expects a dictionary with ingredients, cuisine, diet, allergies, etc.
    """
    # Get API key from environment variable
    api_key = os.getenv("SPOONACULAR_API_KEY")
    if not api_key:
        raise ValueError("SPOONACULAR_API_KEY environment variable is not set")
        
    url = "https://api.spoonacular.com/recipes/complexSearch"

    params = {
        "apiKey": api_key,
        "includeIngredients": ",".join(preferences.get("ingredients", [])),
        "diet": preferences.get("diet"),
        "intolerances": ",".join(preferences.get("allergies", [])),
        "cuisine": preferences.get("cuisine"),
        "maxReadyTime": preferences.get("prep_time", 60),
        "number": 5
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data.get("results", [])
