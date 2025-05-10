from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.state import RecipeState, initial_state
from app.nodes.recipes import RecipeController
from app.nodes.llm_helper import query_llm_for_preferences



# Initialize MCP components
recipe_controller = RecipeController()


# def ask_ingredients(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Ask user for available ingredients."""
#     print("\nWhat ingredients do you have available? (Enter one per line, press Enter twice to finish)")
#     ingredients = []
#     while True:
#         ingredient = input("> ").strip()
#         if not ingredient:
#             break
#         ingredients.append(ingredient)
    
#     # Convert dict to RecipeState, update ingredients, then convert back
#     recipe_state = RecipeState.model_validate(state)
#     recipe_state.ingredients = ingredients
#     return recipe_state.model_dump()

# def ask_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Ask user for recipe preferences."""
#     print("\nWhat are your preferences?")
    
#     # Ask for dietary restrictions
#     print("\nDo you have any dietary restrictions? (e.g., vegetarian, vegan, gluten-free)")
#     diet = input("> ").strip() or None
    
#     # Ask for allergies
#     print("\nDo you have any allergies? (Enter one per line, press Enter twice to finish)")
#     allergies = []
#     while True:
#         allergy = input("> ").strip()
#         if not allergy:
#             break
#         allergies.append(allergy)
    
#     # Ask for cuisine preference
#     print("\nWhat type of cuisine do you prefer? (e.g., Italian, Chinese, Mexican)")
#     cuisine = input("> ").strip() or None
    
#     # Ask for maximum prep time
#     print("\nWhat's the maximum preparation time you're willing to spend? (in minutes)")
#     prep_time = input("> ").strip() or None
    
#     # Convert dict to RecipeState, update preferences, then convert back
#     recipe_state = RecipeState.model_validate(state)
#     recipe_state.preferences.diet = diet
#     recipe_state.preferences.allergies = allergies
#     recipe_state.preferences.cuisine = cuisine
#     recipe_state.preferences.prep_time = prep_time
#     return recipe_state.model_dump()


conversation_history = ""

def collect_user_info(state: Dict[str, Any]) -> Dict[str, Any]:
    global conversation_history

    print("\nYou can talk to the assistant. Type your preferences and ingredients.")
    user_input = input("> ").strip()
    conversation_history += f"\nUser: {user_input}"

    result = query_llm_for_preferences(conversation_history)

    recipe_state = RecipeState.model_validate(state)

    # Update state with whatever was returned
    if "ingredients" in result:
        # print("test I'm here")
        # print("Ingredients:", result["ingredients"])
        recipe_state.ingredients = list(set(recipe_state.ingredients + result["ingredients"]))
        # print("Ingredients:", recipe_state.ingredients)
    prefs = result.get("preferences", {})
    if prefs.get("diet"): recipe_state.preferences.diet = prefs["diet"]
    if prefs.get("allergies"): recipe_state.preferences.allergies += prefs["allergies"]
    if prefs.get("cuisine"): recipe_state.preferences.cuisine = prefs["cuisine"]
    if prefs.get("prep_time"): recipe_state.preferences.prep_time = prefs["prep_time"]
    if prefs.get("craving"): recipe_state.preferences.craving = prefs["craving"]

    # Decide if enough info is available
    if recipe_state.ingredients and recipe_state.preferences.diet and recipe_state.preferences.cuisine:
        return  recipe_state.model_dump()
    print("Current state test:", recipe_state.model_dump())
    return recipe_state.model_dump()

def find_recipes(state: Dict[str, Any]) -> Dict[str, Any]:
    """Find and display matching recipes."""
    # Convert dict to RecipeState
    recipe_state = RecipeState.model_validate(state)
    
    # Get matching recipes
    matching_recipes = recipe_controller.get_matching_recipes(recipe_state)
    
   
    print(matching_recipes)
    return state

# def build_recipe_graph() -> StateGraph:
#     """Build the recipe finder state graph."""
#     # Create the graph
#     workflow = StateGraph(RecipeState)
#     def is_done(state: Dict[str, Any]) -> str:
#         return "find_recipes" if state.get("done") else "collect_user_info"
    
#     workflow.add_node("collect_user_info", collect_user_info)
#     workflow.add_node("find_recipes", find_recipes)
    
#     workflow.add_edge("collect_user_info", is_done)
#     workflow.add_edge("find_recipes", END)
    
#     workflow.set_entry_point("collect_user_info")
#     return workflow.compile()


def build_recipe_graph() -> StateGraph:
    """Build the recipe finder state graph."""
    workflow = StateGraph(RecipeState)

    def is_done(state: Dict[str, Any]) -> str:
        print("Current state:", state)
        return "find_recipes" if state.ingredients  else "collect_user_info"

    workflow.add_node("collect_user_info", collect_user_info)
    workflow.add_node("find_recipes", find_recipes)

    # Use conditional logic here
    workflow.add_conditional_edges(
        "collect_user_info",
        is_done,
       {
            "find_recipes": "find_recipes",
            "collect_user_info": "collect_user_info"
        },
    )

    workflow.add_edge("find_recipes", END)

    workflow.set_entry_point("collect_user_info")
    return workflow.compile()