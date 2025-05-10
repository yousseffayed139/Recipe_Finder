from typing import Dict, Any
from ..state import RecipeState

def process_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ask user for recipe preferences."""
    print("\nWhat are your preferences?")
    
    # Ask for dietary restrictions
    print("\nDo you have any dietary restrictions? (e.g., vegetarian, vegan, gluten-free)")
    diet = input("> ").strip() or None
    
    # Ask for allergies
    print("\nDo you have any allergies? (Enter one per line, press Enter twice to finish)")
    allergies = []
    while True:
        allergy = input("> ").strip()
        if not allergy:
            break
        allergies.append(allergy)
    
    # Ask for cuisine preference
    print("\nWhat type of cuisine do you prefer? (e.g., Italian, Chinese, Mexican)")
    cuisine = input("> ").strip() or None
    
    # Ask for maximum prep time
    print("\nWhat's the maximum preparation time you're willing to spend? (in minutes)")
    prep_time = input("> ").strip() or None
    
    # Convert dict to RecipeState, update preferences, then convert back
    recipe_state = RecipeState.model_validate(state)
    recipe_state.preferences.diet = diet
    recipe_state.preferences.allergies = allergies
    recipe_state.preferences.cuisine = cuisine
    recipe_state.preferences.prep_time = prep_time
    return recipe_state.model_dump() 