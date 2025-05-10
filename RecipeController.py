# recipe_agent/mcp/controller/recipe_controller.py

import requests
from recipe_agent.Recipe_Finder.state import RecipeState
from typing import List
import os

class RecipeController:
    def __init__(self):
        self.api_key = os.getenv("SPOONACULAR_API_KEY")  # Set this in your .env or env vars
        self.endpoint = "https://api.spoonacular.com/recipes/complexSearch"

    def get_matching_recipes(self, state: RecipeState) -> List[dict]:
        if not self.api_key:
            raise ValueError("Spoonacular API key is not set in environment variable.")
        print(self.api_key)

        params = {
            "apiKey": self.api_key,
            "includeIngredients": ",".join(state.ingredients),
            "diet": state.preferences.diet,
            "intolerances": ",".join(state.preferences.allergies),
            "cuisine": state.preferences.cuisine,
            "maxReadyTime": state.preferences.prep_time,
            "number": 1,
            "addRecipeInformation": True
        }

        # Clean up None values
        params = {k: v for k, v in params.items() if v}

        response = requests.get(self.endpoint, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"API request failed: {response.status_code} - {response.text}")

        return response.json().get("results", [])
