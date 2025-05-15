import gradio as gr
import json
import sys
import os
import traceback
import logging
from pydantic import ValidationError

# Allow running as a script
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import build_recipe_graph
from state import RecipeState

# Set up minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("gradio_app")

graph = build_recipe_graph()

# Initialize the state with defaults
def get_initial_state():
    return RecipeState().model_dump()

# Session state for chat
def chat_interface(user_message, history, state):
    logger.info("Processing user message")
    
    # Initialize state if empty
    if not state:
        state = get_initial_state()
        logger.info("Initialized new state")
    
    # Update state with new user message
    if "messages" not in state:
        state["messages"] = []
    
    # Add the user message to the state
    state["messages"].append({"role": "user", "content": user_message})
    
    # Check if the previous state had force_pause set
    was_waiting_for_input = state.get("force_pause", False)
    if was_waiting_for_input:
        logger.info("Continuing after pause for user input")
    
    # Run the graph with increased recursion limit and proper error handling
    try:
        # First, validate the state to ensure it's compatible with our model
        valid_state = RecipeState.model_validate(state)
        
        # Run the graph with the validated state
        logger.info("Invoking graph")
        result = graph.invoke(
            valid_state.model_dump(),
            config={"recursion_limit": 5}
        )
        logger.info("Graph execution completed")
    except ValidationError as ve:
        # Try to fix common validation issues
        try:
            logger.info("Validation error, attempting to fix")
            # If we have recipe objects but they're not in the right format
            if "recipes" in state and state["recipes"] and isinstance(state["recipes"], list):
                # Make sure recipes are dictionaries
                fixed_recipes = []
                for recipe in state["recipes"]:
                    if isinstance(recipe, dict):
                        fixed_recipes.append(recipe)
                state["recipes"] = fixed_recipes
                
            # Try again with the fixed state
            valid_state = RecipeState.model_validate(state)
            result = graph.invoke(
                valid_state.model_dump(),
                config={"recursion_limit": 5}
            )
            logger.info("Successfully fixed validation error")
        except Exception:
            logger.info("Failed to fix validation error")
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": "I encountered an issue processing your information. Please try again with specific ingredients you'd like to use."})
            # Reset the state to avoid continuing problems
            state = get_initial_state()
            state["messages"] = [{"role": "user", "content": user_message}]
            return "", history, state
    except Exception:
        logger.info("Graph execution error")
        # Return a reasonable fallback response
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": "Sorry, I encountered an error processing your request. Please try again with specific ingredients you have available."})
        # Don't lose the message history
        if "messages" in state:
            messages = state["messages"]
            state = get_initial_state()
            state["messages"] = messages
        return "", history, state

    # Check if the graph is waiting for user input (force_pause flag is set)
    is_waiting_for_input = result.get("force_pause", False)
    
    # If the system is waiting for user input, display the last assistant message
    if is_waiting_for_input:
        logger.info("Paused for user input")
        assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
        
        if assistant_messages:
            latest_message = assistant_messages[-1]
            prompt_message = latest_message.get("content", "")
            
            # Add this message to the UI history
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": prompt_message})
            
            # Update the state 
            state = result
            
            return "", history, state

    # Extract the recipes from the state
    recipes = result.get("recipes", [])
    logger.info(f"Found {len(recipes)} recipes")

    # Add extracted information to the response
    extracted_info = f"I extracted the following information from our conversation:\n"
    extracted_info += f"- Ingredients: {', '.join(result.get('ingredients', []) or ['None detected'])}\n"
    
    # Get preferences safely - handle both dict and Pydantic model access
    if isinstance(result.get('preferences', {}), dict):
        # Dict access style
        prefs = result.get('preferences', {})
        diet = prefs.get('diet') or 'Not specified'
        allergies = ', '.join(prefs.get('allergies', []) or ['None'])
        cuisine = prefs.get('cuisine') or 'Not specified'
        prep_time = prefs.get('prep_time') or 'Not specified'
        craving = prefs.get('craving') or 'Not specified'
    else:
        # Pydantic model attribute access style
        prefs = result.get('preferences')
        diet = getattr(prefs, 'diet', None) or 'Not specified'
        allergies = ', '.join(getattr(prefs, 'allergies', []) or ['None'])
        cuisine = getattr(prefs, 'cuisine', None) or 'Not specified'
        prep_time = getattr(prefs, 'prep_time', None) or 'Not specified'
        craving = getattr(prefs, 'craving', None) or 'Not specified'
    
    extracted_info += f"- Diet: {diet}\n"
    extracted_info += f"- Allergies: {allergies}\n"
    extracted_info += f"- Cuisine: {cuisine}\n"
    extracted_info += f"- Prep Time: {prep_time}\n"
    extracted_info += f"- Craving: {craving}\n\n"

    # Format recipes for display
    if recipes:
        logger.info("Formatting recipes for display")
        response_message = extracted_info + f"Here are some recipes for you:\n\n"
        
        for i, recipe in enumerate(recipes):
            # Recipe title
            title = recipe.get('title', f'Recipe {i+1}')
            response_message += f"## {title}\n\n"
            
            # Recipe image
            if recipe.get('image_url'):
                response_message += f"![{title}]({recipe.get('image_url')})\n\n"
            
            # Ingredients
            if recipe.get('ingredients'):
                response_message += "### Ingredients\n"
                for ingredient in recipe.get('ingredients', []):
                    response_message += f"- {ingredient}\n"
                response_message += "\n"
            
            # Instructions
            if recipe.get('instructions'):
                response_message += "### Instructions\n"
                for j, step in enumerate(recipe.get('instructions', [])):
                    response_message += f"{j+1}. {step}\n"
                response_message += "\n"
            
            # Grocery list (items you need to buy)
            if recipe.get('grocery_list') and len(recipe.get('grocery_list')) > 0:
                response_message += "### Shopping List\n"
                response_message += "These items aren't in your ingredients list and may need to be purchased:\n"
                for item in recipe.get('grocery_list', []):
                    response_message += f"- {item}\n"
                response_message += "\n"
            
            # Calories
            if recipe.get('calories'):
                response_message += f"**Calories:** {recipe.get('calories')} kcal\n\n"
            
            response_message += "---\n\n"
    else:
        logger.info("No recipes found or waiting for more information")
        # Check if we have a prompt message in the state results
        if "messages" in result:
            assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
            if assistant_messages:
                latest_message = assistant_messages[-1]
                prompt_message = latest_message.get("content", "")
                if "ingredients" in prompt_message.lower():
                    response_message = prompt_message
                else:
                    response_message = "I need specific ingredients to suggest recipes. Please tell me what ingredients you have available in your kitchen."
            else:
                response_message = "I need specific ingredients to suggest recipes. Please tell me what ingredients you have available in your kitchen."
        else:
            response_message = extracted_info + "I couldn't find any recipes matching your criteria. Please try providing specific ingredients you'd like to use."

    # Add messages to the history in the correct format for type="messages"
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response_message})
    
    # Update the state with the most recent result
    state = result
    
    # Ensure we have the messages array and add the latest exchange
    if "messages" not in state:
        state["messages"] = []
    
    # Add this conversation to the state
    state["messages"].append({"role": "user", "content": user_message})
    state["messages"].append({"role": "assistant", "content": response_message})
    
    logger.info("Response complete, returning to user")
    return "", history, state

# Launch the gradio app
with gr.Blocks() as demo:
    gr.Markdown("# 🥗 Recipe Finder Chatbot")
    gr.Markdown("Tell me what **specific ingredients** you have available and I'll suggest recipes. For example: 'I have chicken, pasta, and tomatoes. Can you suggest an Italian dish?'")
    
    # Use a simpler Chatbot configuration compatible with older Gradio versions
    chatbot = gr.Chatbot(
        type="messages",
        height=600,
        show_label=False
    )
    
    state = gr.State(get_initial_state())  # Initialize state properly
    
    with gr.Row():
        user_input = gr.Textbox(
            placeholder="List your ingredients here (e.g., 'I have eggs, cheese, spinach and want something quick')",
            show_label=False,
            scale=9
        )
        send_btn = gr.Button("Send", scale=1)

    gr.Examples(
        [
            "I have chicken, rice, and bell peppers. Looking for something spicy.",
            "I need a vegetarian pasta dish with mushrooms and spinach.",
            "I have eggs, cheese, and potatoes. Something quick for breakfast."
        ],
        user_input
    )
    
    send_btn.click(chat_interface, [user_input, chatbot, state], [user_input, chatbot, state])
    user_input.submit(chat_interface, [user_input, chatbot, state], [user_input, chatbot, state])

    logger.info("Gradio app initialized")

logger.info("Starting Gradio server")
demo.launch() 