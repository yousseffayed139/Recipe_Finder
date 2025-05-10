from typing import Dict, Any
from langgraph.graph import StateGraph
from app.state import RecipeState, initial_state
from app.nodes.recipes import RecipeController


# Initialize MCP components
recipe_controller = RecipeController()


def ask_ingredients(state: Dict[str, Any]) -> Dict[str, Any]:
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

def ask_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
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

def find_recipes(state: Dict[str, Any]) -> Dict[str, Any]:
    """Find and display matching recipes."""
    # Convert dict to RecipeState
    recipe_state = RecipeState.model_validate(state)
    
    # Get matching recipes
    matching_recipes = recipe_controller.get_matching_recipes(recipe_state)
    
   
    print(matching_recipes)
    return state

def build_recipe_graph() -> StateGraph:
    """Build the recipe finder state graph."""
    # Create the graph
    workflow = StateGraph(RecipeState)
    
    # Add nodes
    workflow.add_node("ask_ingredients", ask_ingredients)
    workflow.add_node("ask_preferences", ask_preferences)
    workflow.add_node("find_recipes", find_recipes)
    
    # Add edges
    workflow.add_edge("ask_ingredients", "ask_preferences")
    workflow.add_edge("ask_preferences", "find_recipes")
    
    # Set entry point
    workflow.set_entry_point("ask_ingredients")
    
    return workflow.compile()
