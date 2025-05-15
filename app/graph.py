from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from state import RecipeState, initial_state
from Controller.llm_helper import query_llm_for_preferences
from agent.recipe_agent import recipe_agent
from agent.user_info_agent import user_info_agent
from router import is_user_info_complete
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize MCP components
# recipe_controller = RecipeController()

conversation_history = ""
collect_user_info_counter = 0


# def collect_user_info(state: Dict[str, Any]) -> Dict[str, Any]:

#     global collect_user_info_counter
#     collect_user_info_counter += 1
#     if collect_user_info_counter > 3:
#         print("Breaking loop after 3 iterations to avoid excessive API calls.")
#         return state
#     # Initialize the recipe state using the incoming state
#     recipe_state = RecipeState.model_validate(state)

#     # Construct the conversation history string
#     messages = state.get("messages", [])
#     conversation_history = "\n".join(f"{m['role']}: {m['content']}" for m in messages)


#     # Construct a prompt with the current state and conversation history
#     prompt = (
#         f"You are a helpful cooking assistant. Here is the conversation history:\n"
#         f"{conversation_history}\n"
#         f"Please tell me about your preferences.\n"
#         f"What ingredients do you have in your fridge? {', '.join(recipe_state.ingredients) if recipe_state.ingredients else 'I haven't received any ingredients yet.'}\n"
#         f"What dietary preferences do you have? (e.g., vegetarian, vegan, gluten-free, etc.)\n"
#         f"Do you have any allergies? If so, please list them.\n"
#         f"What type of cuisine do you prefer? (e.g., Italian, Mexican, etc.)\n"
#         f"What is your ideal meal prep time in minutes?\n"
#         f"Are you craving something specific?"
#     )
#     # Use the user_info_agent to gather more structured information
#     response = user_info_agent.invoke({
#     "messages": state.get("messages", [])
#     })

#     result = eval(response) if isinstance(response, str) else response

#     # Parse the agent's response, assuming structured JSON
#     # try:
#     #     result = eval(response) if isinstance(response, str) else response
#     # except Exception as e:
#     #     print("Error parsing agent output:", e)
#     #     return state

#     # Update recipe state based on the agent's structured response
#     if "ingredients" in result: recipe_state.ingredients = list(set(recipe_state.ingredients + result["ingredients"]))

#     prefs = result.get("preferences", {})
#     if prefs.get("diet"): recipe_state.preferences.diet = prefs["diet"]
#     if prefs.get("allergies"): recipe_state.preferences.allergies += prefs["allergies"]
#     if prefs.get("cuisine"): recipe_state.preferences.cuisine = prefs["cuisine"]
#     if prefs.get("prep_time"): recipe_state.preferences.prep_time = prefs["prep_time"]
#     if prefs.get("craving"): recipe_state.preferences.craving = prefs["craving"]

#     # Return the updated state
#     return recipe_state.model_dump()


# Optional: limit retries to avoid infinite loops

# def collect_user_info(state: Dict[str, Any]) -> Dict[str, Any]:
#     global collect_user_info_counter
#     collect_user_info_counter += 1
#     if collect_user_info_counter > 3:
#         print("Breaking loop after 3 iterations to avoid excessive API calls.")
#         return state

#     # Ensure messages exist in state
#     messages = state.messages
#     if not messages:
#         print("No user messages found.")
#         return state

#     # Let the agent process the conversation naturally
#     try:
#         response = user_info_agent.invoke({
#             "messages": messages
#         })
#     except Exception as e:
#         print("Agent invocation failed:", e)
#         return state

#     # Ensure we can safely parse the tool's output
#     if isinstance(response, str):
#         print("Agent returned a string, but a dict was expected.")
#         return state

#     result = response  # should be a dict directly from the tool

#     # Initialize structured recipe state object
#     recipe_state = RecipeState.model_validate(state)

#     # Safely merge new extracted preferences
#     if "ingredients" in result:
#         recipe_state.ingredients = list(set(recipe_state.ingredients + result["ingredients"]))

#     prefs = result.get("preferences", {})
#     if prefs.get("diet"):
#         recipe_state.preferences.diet = prefs["diet"]
#     if prefs.get("allergies"):
#         recipe_state.preferences.allergies = list(set(recipe_state.preferences.allergies + prefs["allergies"]))
#     if prefs.get("cuisine"):
#         recipe_state.preferences.cuisine = prefs["cuisine"]
#     if prefs.get("prep_time"):
#         recipe_state.preferences.prep_time = prefs["prep_time"]
#     if prefs.get("craving"):
#         recipe_state.preferences.craving = prefs["craving"]

#     return recipe_state.model_dump()
def collect_user_info(state: Dict[str, Any]) -> Dict[str, Any]:
    # Validate and hydrate state
    recipe_state = RecipeState.model_validate(state)

    # Stop if enough attempts already
    if recipe_state.iterations >= 3:
        return recipe_state.model_dump()

    # Construct conversation history
    messages = getattr(recipe_state, "messages", []) or []
    conversation_history = "\n".join([msg["content"] for msg in messages])

    # Build prompt
    prompt = (
        f"You are a helpful cooking assistant. Here is the conversation history:\n"
        f"{conversation_history}\n"
        f"Please extract or clarify user preferences.\n"
        f"Ingredients so far: {', '.join(recipe_state.ingredients) or 'None yet.'}\n"
        f"Diet: {recipe_state.preferences.diet or 'Not specified'}\n"
        f"Allergies: {', '.join(recipe_state.preferences.allergies) or 'None'}\n"
        f"Cuisine: {recipe_state.preferences.cuisine or 'Not specified'}\n"
        f"Prep Time: {recipe_state.preferences.prep_time or 'Not specified'}\n"
        f"Craving: {recipe_state.preferences.craving or 'Not specified'}"
    )

    try:
        # Try calling the agent
        response = user_info_agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })
    except Exception:
        return recipe_state.model_dump()

    # Parse the response
    try:
        # Extract the content from LangChain message format
        if isinstance(response, dict) and "messages" in response:
            # If response contains a messages array
            messages = response.get("messages", [])
            if messages and len(messages) > 0:
                # Get the last assistant message
                for msg in reversed(messages):
                    if hasattr(msg, 'content'):
                        content = msg.content
                        break
                else:
                    content = "{}"
            else:
                content = "{}"
        elif isinstance(response, str):
            content = response
        else:
            # Try to get content from other response formats
            content = getattr(response, "content", str(response))
            
        # Clean the JSON string
        content = content.strip()
        if content.startswith('```') and content.endswith('```'):
            content = content[3:-3].strip()
            if content.startswith('json'):
                content = content[4:].strip()
                
        # Handle potential JSON fragments in the text
        if "{" in content and "}" in content:
            start = content.find("{")
            brace_count = 0
            for i in range(start, len(content)):
                if content[i] == "{":
                    brace_count += 1
                elif content[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            if brace_count == 0:
                content = content[start:end]
                
        result = json.loads(content)
    except Exception:
        # Default empty structure
        result = {
            "ingredients": [],
            "preferences": {}
        }

    # Ensure result has the correct structure
    if not isinstance(result, dict):
        try:
            if isinstance(result, str):
                result = json.loads(result)
            else:
                result = {"ingredients": [], "preferences": {}}
        except:
            result = {"ingredients": [], "preferences": {}}

    # Merge info from result
    if "ingredients" in result:
        recipe_state.ingredients = list(set(recipe_state.ingredients + result["ingredients"]))

    prefs = result.get("preferences", {})
    if prefs.get("diet"): 
        recipe_state.preferences.diet = prefs["diet"]
    if prefs.get("allergies"): 
        recipe_state.preferences.allergies += prefs["allergies"]
    if prefs.get("cuisine"): 
        recipe_state.preferences.cuisine = prefs["cuisine"]
    if prefs.get("prep_time"): 
        recipe_state.preferences.prep_time = prefs["prep_time"]
    if prefs.get("craving"): 
        recipe_state.preferences.craving = prefs["craving"]

    # Increment loop counter
    recipe_state.iterations += 1
    
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
    response = recipe_agent.invoke({
        "messages": [
            {"role": "user", "content": prompt}
        ]
    })
    
    # Extract the recipes from the response
    try:
        # Parse the recipes from the response
        if isinstance(response, dict) and "messages" in response:
            # Get the last assistant message content
            messages = response.get("messages", [])
            content = ""
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content.strip()
                    break
        else:
            # Get content from string or other response format
            content = getattr(response, "content", str(response)).strip()
        
        # Extract JSON content from potential markdown or text
        if "```" in content:
            # Handle markdown code blocks
            parts = content.split("```")
            for part in parts:
                # Skip the parts outside code blocks or language indicators
                if part.strip() and not part.strip().startswith("json"):
                    # Found code block content
                    content = part.strip()
                    break
        
        # Find first [ to start of JSON array
        start_idx = content.find('[')
        if start_idx >= 0:
            # Find matching closing bracket
            bracket_count = 0
            for i in range(start_idx, len(content)):
                if content[i] == '[':
                    bracket_count += 1
                elif content[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found complete JSON array
                        json_str = content[start_idx:i+1]
                        break
            else:
                # No matching bracket found
                json_str = content[start_idx:]
        else:
            # No JSON array found
            json_str = content
            
        # Clean the JSON string - handle common issues
        json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
        json_str = json_str.replace("\\n", " ")  # Replace newlines in strings
        
        # Try to handle trailing commas
        json_str = json_str.replace(",]", "]")
        json_str = json_str.replace(",}", "}")
        
        # Use proper JSON parsing
        try:
            recipes = json.loads(json_str)
        except json.JSONDecodeError:
            # As a fallback, try Python's literal_eval which is more forgiving
            try:
                import ast
                recipes = ast.literal_eval(json_str)
                
                # Convert to proper format - handle non-string keys and values
                recipes = json.loads(json.dumps(recipes))
            except Exception:
                raise
        
        # Ensure the recipes are a list
        if not isinstance(recipes, list):
            recipes = [recipes]
        
        # Process each recipe
        for i, recipe in enumerate(recipes):
            if not isinstance(recipe, dict):
                continue
                
            # Ensure all required fields exist
            for field in ["title", "ingredients", "instructions"]:
                if field not in recipe:
                    recipe[field] = [] if field in ["ingredients", "instructions", "grocery_list"] else ""
            
            # Ensure grocery_list is present
            if "grocery_list" not in recipe:
                recipe["grocery_list"] = []
            
        # Update the state with the recipes
        recipe_state.recipes = recipes
        
    except Exception:
        # Set empty recipes list if parsing failed
        recipe_state.recipes = []
    
    return recipe_state.model_dump()


def should_continue_collecting(state: Dict[str, Any]) -> str:
    recipe_state = RecipeState.model_validate(state)

    # Stop if enough attempts already
    if recipe_state.iterations >= 2:
        return "complete"

    # Continue only if something is missing
    has_ingredients = bool(recipe_state.ingredients and len(recipe_state.ingredients) > 0)
    
    if not has_ingredients:
        return "incomplete"
    
    return "complete"
   


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

    return workflow.compile()