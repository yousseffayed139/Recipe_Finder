from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.state import RecipeState, initial_state
from app.Controller.llm_helper import query_llm_for_preferences
from app.agent.recipe_agent import recipe_agent


# Initialize MCP components
# recipe_controller = RecipeController()
recipe_agentt = recipe_agent
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
    recipe_state = RecipeState.model_validate(state)

    # Construct a natural language prompt using the state
    prompt = (
        f"Find me a recipe using the following ingredients: {', '.join(recipe_state.ingredients)}.\n"
        f"My dietary preferences are: {recipe_state.preferences.diet}.\n"
        f"I have allergies to: {', '.join(recipe_state.preferences.allergies)}.\n"
        f"I prefer {recipe_state.preferences.cuisine} cuisine.\n"
        f"I want something that takes less than {recipe_state.preferences.prep_time} minutes to prepare.\n"
        f"I'm craving: {recipe_state.preferences.craving}."
    )

    # Use proper chat-style input for create_react_agent
    result = recipe_agent.invoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })

    print("Agent response:\n", result)
    return state




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