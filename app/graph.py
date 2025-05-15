from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from state import RecipeState, initial_state
from Controller.llm_helper import query_llm_for_preferences
from agent.recipe_agent import recipe_agent
from agent.user_info_agent import user_info_agent
from router import is_user_info_complete
import json
from json_repair import repair_json
from dotenv import load_dotenv
import logging

load_dotenv()

# Set up minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("recipe_finder")

# Initialize MCP components
# recipe_controller = RecipeController()

conversation_history = ""



#     return recipe_state.model_dump()
def collect_user_info(state: Dict[str, Any]) -> Dict[str, Any]:
    # Validate and hydrate state
    recipe_state = RecipeState.model_validate(state)
    
    # If we previously paused for user input, process the new message
    if recipe_state.force_pause:
        logger.info("Processing user input after pause")
        # Reset the flag now that we've received a new message
        recipe_state.force_pause = False
        
        # Get the latest user message to extract ingredients
        messages = getattr(recipe_state, "messages", []) or []
        latest_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                latest_user_message = msg.get("content", "")
                break
        
        # Extract ingredients from the user message by calling the agent directly
        if latest_user_message:
            try:
                prompt = (
                    f"ONLY extract specific food ingredients from this message. DO NOT add any ingredients that weren't explicitly mentioned:\n"
                    f"{latest_user_message}\n\n"
                    f"Return ONLY a valid JSON array of ingredients. Example: [\"chicken\", \"rice\", \"onions\"]\n"
                    f"If no ingredients are found, return an empty array []"
                )
                
                response = user_info_agent.invoke({
                    "messages": [{"role": "user", "content": prompt}]
                })
                
                # Try to parse ingredients directly
                ingredients_result = parse_agent_json(response)
                
                # Handle different response formats
                if isinstance(ingredients_result, list):
                    # Direct array of ingredients 
                    new_ingredients = ingredients_result
                elif isinstance(ingredients_result, dict) and "ingredients" in ingredients_result:
                    # Response contains an ingredients key
                    new_ingredients = ingredients_result.get("ingredients", [])
                else:
                    # Try to find any array in the response
                    for key, value in ingredients_result.items() if isinstance(ingredients_result, dict) else {}:
                        if isinstance(value, list) and value:
                            new_ingredients = value
                            break
                    else:
                        new_ingredients = []
                
                # Filter out any empty ingredients
                new_ingredients = [ing for ing in new_ingredients if ing and isinstance(ing, str)]
                
                if new_ingredients:
                    logger.info(f"Extracted ingredients: {new_ingredients}")
                    recipe_state.ingredients = new_ingredients
                else:
                    logger.info("No ingredients found in user message, asking again")
                    # Add a message asking for ingredients again, more explicitly
                    messages.append({
                        "role": "assistant", 
                        "content": "I still need to know what specific ingredients you have. Please list them clearly, for example: 'I have chicken, rice, and carrots.'"
                    })
                    recipe_state.messages = messages
                    recipe_state.force_pause = True
                    return recipe_state.model_dump()
            except Exception:
                pass
        
        # If we successfully got ingredients, proceed with the flow
        if recipe_state.ingredients:
            return recipe_state.model_dump()
    
    # Regular flow for initial message or if we already have ingredients
    
    # Stop if enough attempts already
    if recipe_state.iterations >= 3:
        return recipe_state.model_dump()

    # Construct conversation history
    messages = getattr(recipe_state, "messages", []) or []
    conversation_history = "\n".join([msg["content"] for msg in messages])

    # Get the last message from user to check context
    last_user_message = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break
    
    # If we have no ingredients but have iterated at least once, add a direct prompt
    # and set the force_pause flag to true to wait for user input
    if not recipe_state.ingredients and recipe_state.iterations >= 1:
        logger.info("No ingredients found, pausing for user input")
        # Add a message prompting the user to provide ingredients
        messages.append({
            "role": "assistant", 
            "content": "I need specific ingredients to suggest recipes. Please tell me what ingredients you have available in your kitchen, and I'll find perfect recipes for you. For example: 'I have chicken, potatoes, and carrots.'"
        })
        recipe_state.messages = messages
        recipe_state.iterations += 1
        # Set force_pause flag to true to prevent further processing until user responds
        recipe_state.force_pause = True
        return recipe_state.model_dump()

    # Build prompt
    prompt = (
        f"You are a helpful cooking assistant. Here is the conversation history:\n"
        f"{conversation_history}\n"
        f"Please extract or clarify user preferences.\n"
        f"CRITICALLY IMPORTANT: ONLY include ingredients the user has EXPLICITLY mentioned. Do NOT suggest ingredients or make assumptions about what the user has.\n"
        f"Ingredients so far: {', '.join(recipe_state.ingredients) or 'None yet.'}\n"
        f"Diet: {recipe_state.preferences.diet or 'Not specified'}\n"
        f"Allergies: {', '.join(recipe_state.preferences.allergies) or 'None'}\n"
        f"Cuisine: {recipe_state.preferences.cuisine or 'Not specified'}\n"
        f"Prep Time: {recipe_state.preferences.prep_time or 'Not specified'}\n"
        f"Craving: {recipe_state.preferences.craving or 'Not specified'}"
    )

    try:
        # Call the agent
        response = user_info_agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })
    except Exception:
        return recipe_state.model_dump()

    # Parse and extract JSON using json-repair
    result = parse_agent_json(response)
    
    # Set default empty structure if parsing failed
    if not result or not isinstance(result, dict):
        result = {"ingredients": [], "preferences": {}}

    # Process ingredients - handle carefully
    if "ingredients" in result and isinstance(result["ingredients"], list):
        new_ingredients = [ing for ing in result["ingredients"] if ing]
        if new_ingredients:
            logger.info(f"First pass extracted ingredients: {new_ingredients}")
            recipe_state.ingredients = new_ingredients

    # Process preferences - handle carefully with null checking
    prefs = result.get("preferences", {}) or {}
    if prefs and isinstance(prefs, dict):
        if prefs.get("diet") not in (None, "null", ""):
            recipe_state.preferences.diet = prefs["diet"]
            
        if prefs.get("allergies") and isinstance(prefs["allergies"], list):
            new_allergies = [a for a in prefs["allergies"] if a not in (None, "null", "")]
            recipe_state.preferences.allergies += new_allergies
            
        if prefs.get("cuisine") not in (None, "null", ""):
            recipe_state.preferences.cuisine = prefs["cuisine"]
            
        if prefs.get("prep_time") not in (None, "null", ""):
            recipe_state.preferences.prep_time = prefs["prep_time"]
            
        if prefs.get("craving") not in (None, "null", ""):
            recipe_state.preferences.craving = prefs["craving"]

    # Increment loop counter
    recipe_state.iterations += 1
    
    return recipe_state.model_dump()


def find_recipes(state: Dict[str, Any]) -> Dict[str, Any]:
    recipe_state = RecipeState.model_validate(state)
    logger.info(f"Finding recipes with: {recipe_state.ingredients}")

    # If we previously paused but now have ingredients, we can clear the flag
    if recipe_state.force_pause and recipe_state.ingredients:
        logger.info("Clearing pause flag - ingredients available")
        recipe_state.force_pause = False

    # If we're waiting for user input and don't have ingredients, don't process yet
    if recipe_state.force_pause and not recipe_state.ingredients:
        logger.info("Paused - waiting for user ingredients")
        return recipe_state.model_dump()

    # Safety check - ensure we have ingredients
    if not recipe_state.ingredients:
        logger.info("No ingredients available, requesting user input")
        recipe_state.recipes = []
        
        # Add a message to the state asking for specific ingredients
        messages = getattr(recipe_state, "messages", []) or []
        messages.append({
            "role": "assistant", 
            "content": "I need specific ingredients to suggest recipes. Please tell me what ingredients you have available in your kitchen, and I'll find perfect recipes for you. For example: 'I have chicken, potatoes, and carrots.'"
        })
        recipe_state.messages = messages
        recipe_state.force_pause = True
        
        return recipe_state.model_dump()

    # Construct a natural language prompt using the state
    prompt = (
        f"Find me a recipe using the following ingredients: {', '.join(recipe_state.ingredients)}.\n"
        f"My dietary preferences are: {recipe_state.preferences.diet or 'None'}.\n"
        f"I have allergies to: {', '.join(recipe_state.preferences.allergies) or 'None'}.\n"
        f"I prefer {recipe_state.preferences.cuisine or 'any'} cuisine.\n"
        f"I want something that takes less than {recipe_state.preferences.prep_time or '60'} minutes to prepare.\n"
        f"I'm craving: {recipe_state.preferences.craving or 'anything tasty'}."
    )

    try:
        # Use proper chat-style input for create_react_agent
        response = recipe_agent.invoke({
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })
        
        # Parse and extract recipes using json-repair
        recipes_data = parse_agent_json(response)
        
        # Ensure the recipes are a list
        if not isinstance(recipes_data, list):
            if isinstance(recipes_data, dict):
                # Single recipe as a dict - put it in a list
                recipes_data = [recipes_data]
            else:
                # Empty or invalid data
                recipes_data = []
        
        # Process each recipe to ensure required fields and proper format
        formatted_recipes = []
        for recipe in recipes_data:
            if not isinstance(recipe, dict):
                continue
                
            # Create a properly formatted recipe dict with all required fields
            formatted_recipe = {
                "title": recipe.get("title", "Untitled Recipe"),
                "image_url": recipe.get("image_url", ""),
                "ingredients": recipe.get("ingredients", []),
                "instructions": recipe.get("instructions", []),
                "grocery_list": recipe.get("grocery_list", []),
                "calories": recipe.get("calories", None)
            }
            
            # Validate types for key fields
            if not isinstance(formatted_recipe["ingredients"], list):
                formatted_recipe["ingredients"] = [str(formatted_recipe["ingredients"])]
                
            if not isinstance(formatted_recipe["instructions"], list):
                formatted_recipe["instructions"] = [str(formatted_recipe["instructions"])]
                
            if not isinstance(formatted_recipe["grocery_list"], list):
                formatted_recipe["grocery_list"] = [str(formatted_recipe["grocery_list"])]
            
            # Add any additional fields from the original recipe
            for key, value in recipe.items():
                if key not in formatted_recipe:
                    formatted_recipe[key] = value
                    
            formatted_recipes.append(formatted_recipe)
            
        # Update the state with the formatted recipes
        recipe_state.recipes = formatted_recipes
        logger.info(f"Found {len(formatted_recipes)} recipes")
        
    except Exception:
        # Set empty recipes list if parsing failed
        recipe_state.recipes = []
        logger.info("Error finding recipes")
    
    return recipe_state.model_dump()


def should_continue_collecting(state: Dict[str, Any]) -> str:
    recipe_state = RecipeState.model_validate(state)
    iterations = recipe_state.iterations
    ingredients = recipe_state.ingredients
    force_pause = recipe_state.force_pause
    
    logger.info(f"Flow check - Iter: {iterations}, Ingredients: {len(ingredients) if ingredients else 0}, Pause: {force_pause}")

    # If force_pause is set but we have no ingredients, wait for user input
    if force_pause and not ingredients:
        logger.info("Paused - waiting for user input")
        return "incomplete"

    # If we have ingredients, always move to recipe finding
    has_ingredients = bool(ingredients and len(ingredients) > 0)
    if has_ingredients:
        logger.info("Found ingredients, moving to recipe finding")
        return "complete"

    # Stop if maximum iterations reached
    if iterations >= 2:
        logger.info(f"Max iterations reached ({iterations}), moving to recipe finding")
        return "complete"
    
    logger.info("No ingredients yet, continuing collection")
    return "incomplete"
   

def build_recipe_graph():
    """Builds the recipe graph using a custom router node."""
    workflow = StateGraph(RecipeState)

    # Add main function nodes
    workflow.add_node("collect_user_info", collect_user_info)
    workflow.add_node("find_recipes", find_recipes)

    # Add the routing logic
    workflow.add_conditional_edges(
        "collect_user_info",
        should_continue_collecting,
        {
            "incomplete": "collect_user_info",
            "complete": "find_recipes"
        }
    )

    workflow.add_edge("find_recipes", END)
    workflow.set_entry_point("collect_user_info")
    
    logger.info("Recipe graph built and compiled")
    return workflow.compile()

def parse_agent_json(response: Any) -> Dict:
    """
    Extract and repair JSON from an agent response using json-repair.
    Handles various agent response formats and returns a parsed dictionary.
    """
    try:
        # First, extract the text content from different response formats
        if isinstance(response, dict) and "messages" in response:
            # Extract from LangChain message format
            messages = response.get("messages", [])
            content = ""
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content.strip()
                    break
        elif isinstance(response, str):
            content = response.strip()
        else:
            # Get content from other formats
            content = getattr(response, "content", str(response)).strip()
            
        # Clean up markdown code blocks
        if "```" in content:
            parts = content.split("```")
            # Look for code block content
            for part in parts:
                if part.strip() and not part.strip().startswith("json"):
                    content = part.strip()
                    break
        
        # Extract only the JSON part if there's explanatory text
        import re
        json_match = re.search(r'(\[.*\]|\{.*\})', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
                    
        # Try to repair and parse the JSON
        repaired_json = repair_json(content)
        result = json.loads(repaired_json)
        
        # If result is a list (like in the error case we saw or direct ingredients array), handle it
        if isinstance(result, list):
            # Check if this looks like an ingredients list (list of strings)
            if all(isinstance(item, str) for item in result if item):
                logger.info("Parsed direct ingredients list")
                return result
            # Otherwise, take the first dict element
            elif len(result) > 0 and isinstance(result[0], dict):
                result = result[0]
            
        # Ensure we're not including ingredients that haven't been explicitly mentioned
        # by checking if the result has an unreasonably large number of ingredients
        if isinstance(result, dict) and "ingredients" in result:
            ingredients = result.get("ingredients", [])
            if (isinstance(ingredients, list) and len(ingredients) > 10) or not isinstance(ingredients, list):
                # Too many ingredients - likely includes suggestions rather than explicit mentions
                result["ingredients"] = []
                
        return result
    except Exception:
        # Return empty structure if parsing fails
        logger.info("JSON parsing failed")
        return {"ingredients": [], "preferences": {}}