from typing import Dict, Any
from ..state import RecipeState

def process_ingredients(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ask user for available ingredients."""
    print("\nWhat ingredients do you have available? (Enter one per line, press Enter twice to finish)")
    ingredients = []
    while True:
        ingredient = input("> ").strip()
        if not ingredient:
            break
        ingredients.append(ingredient)
    
    # Convert dict to RecipeState, update ingredients, then convert back
    recipe_state = RecipeState.model_validate(state)
    recipe_state.ingredients = ingredients
    return recipe_state.model_dump() 