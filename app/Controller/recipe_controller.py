# app/controller/recipe_controller.py
from app.agent.tools.spoonacular_tool import spoonacular_search
from app.agent.tools.tavily_tool import tavily_search

def get_recipe(user_prefs: dict) -> str:
    """
    Core logic to attempt recipe lookup via Spoonacular, then Tavily as fallback.
    """
    ingredients = user_prefs.get("ingredients", [])
    diet = user_prefs.get("diet")
    allergies = user_prefs.get("allergies")
    cuisine = user_prefs.get("cuisine")
    prep_time = user_prefs.get("prep_time")

    result = spoonacular_search.run(
        ingredients=ingredients,
        diet=diet,
        allergies=allergies,
        cuisine=cuisine,
        prep_time=prep_time
    )

    if "No matching recipes found" in result or "error" in result.lower():
        query = f"{diet or ''} {cuisine or ''} meal with {', '.join(ingredients)}"
        return tavily_search.run(query=query)

    return result
