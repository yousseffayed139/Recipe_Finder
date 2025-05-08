from langchain.tools import tool
import requests

@tool
def search_recipes(preferences: dict) -> list:
    """
    Search for recipes using an external recipe API based on user preferences.
    Expects a dictionary with ingredients, cuisine, diet, allergies, etc.
    """
    # Example: Using Spoonacular (you could also call a local web search tool or use MCP proxy)
    api_key = "2e7a0f619dc24c969bc049f109c18b2c"
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
