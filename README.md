# 🥗 Recipe Finder

A conversational AI application that suggests recipes based on ingredients you have available and your dietary preferences.

## Features

- 🍳 **Ingredient-based Recipe Suggestions**: Provide the ingredients you have, and get recipe suggestions
- 🥦 **Dietary Preference Support**: Specify dietary restrictions, allergies, cuisine types, and more
- ⏱️ **Time-sensitive Recommendations**: Filter recipes based on preparation time
- 🧠 **Conversational Interface**: Natural dialogue to understand your needs
- 🍕 **Recipe Details**: Get detailed ingredients, instructions, and even grocery lists for items you might need to buy

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- OpenRouter API key (for LLM access)
- Tavily API key (optional, for web search capabilities)
- Spoonacular API key (optional, for additional recipe data)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yousseffayed139/Recipe_Finder.git
   cd Recipe_Finder
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your API keys:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key
   TAVILY_API_KEY=your_tavily_api_key
   SPOONACULAR_API_KEY=your_spoonacular_api_key
   ```

### Running the Application

Start the application with:

```
python run.py
```

Or directly:

```
python app/gradio_app.py
```

The application will be available at http://localhost:7860 in your browser.

## Usage Guide

1. **Start by sharing your ingredients**: Tell the chatbot what ingredients you have available
   
   Example: "I have chicken, pasta, and tomatoes."

2. **Add preferences if desired**: Mention dietary preferences, cuisines, or cravings
   
   Example: "I'd like a low-carb Italian dish."

3. **Provide additional details when prompted**: The system may ask clarifying questions

4. **View your recipes**: The system will display matching recipes with instructions and details

## Project Structure

- `app/`: Main application code
  - `gradio_app.py`: Gradio web interface
  - `graph.py`: LangGraph workflow definition
  - `state.py`: State management and data models
  - `router.py`: Routing logic for the conversation flow
  - `agent/`: LLM agents for different tasks
  - `Controller/`: Backend logic and API integrations

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | API key for OpenRouter (required) |
| `TAVILY_API_KEY` | API key for Tavily search (optional) |
| `SPOONACULAR_API_KEY` | API key for Spoonacular recipe API (optional) |

## License

[MIT License](LICENSE)

## Acknowledgements

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph)
- UI created with [Gradio](https://github.com/gradio-app/gradio)