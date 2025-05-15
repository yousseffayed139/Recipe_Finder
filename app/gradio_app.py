import gradio as gr
import ast
import json
import sys
import os

# Allow running as a script
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph import build_recipe_graph
from state import initial_state, RecipeState

# Helper to parse agent output (list of recipes as JSON-like string)
def parse_recipes(agent_response):
    try:
        if isinstance(agent_response, list):
            return agent_response
        # Try to parse as Python list of dicts
        if isinstance(agent_response, str):
            # Convert single quotes to double quotes for JSON parsing
            clean_json = agent_response.replace("'", '"')
            return json.loads(clean_json)
    except Exception as e:
        print(f"DEBUG: Error parsing recipe JSON: {e}")
    return []

graph = build_recipe_graph()

# Session state for chat
def chat_interface(user_message, history, state):
    # Update state with user message
    if "messages" not in state:
        state["messages"] = []
    state["messages"].append({"role": "user", "content": user_message})

    # Run the graph with increased recursion limit
    try:
        result = graph.invoke(
            RecipeState.model_validate(state).model_dump(),
            config={"recursion_limit": 5}
        )
    except Exception:
        # Return a reasonable fallback response
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": "Sorry, I encountered an error processing your request. Please try again with more specific information about ingredients and preferences."})
        return "", history, state

    # Extract the recipes from the state
    recipes = result.get("recipes", [])

    # Show extracted ingredients and preferences in the response
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
        response_message = extracted_info + "I couldn't find any recipes matching your criteria. Please try providing more ingredients or different preferences."

    # Add messages to the history in the correct format for type="messages"
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response_message})
    
    return "", history, state

with gr.Blocks() as demo:
    gr.Markdown("# 🥗 Recipe Finder Chatbot")
    gr.Markdown("Ask me to find recipes based on ingredients you have. For example: 'I have chicken, pasta, and tomatoes. Can you suggest an Italian dish?'")
    
    # Use a simpler Chatbot configuration compatible with older Gradio versions
    chatbot = gr.Chatbot(
        type="messages",
        height=600,
        show_label=False
    )
    
    state = gr.State({})  # Initialize state
    
    with gr.Row():
        user_input = gr.Textbox(
            placeholder="Type your ingredients and preferences here...",
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

demo.launch() 