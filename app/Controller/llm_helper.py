# llm_helper.py
import os
import json
from app.state import RecipeState
from typing import Dict
from dotenv import load_dotenv
import openai


load_dotenv()

def query_llm_for_preferences(conversation_history: str) -> Dict:
    """Uses LLM to extract structured user preferences from conversation."""
    prompt = f"""
You are a helpful cooking assistant. Extract the following fields from the user's conversation:
- Ingredients (a list of individual ingredients)
- Preferences (diet, allergies, cuisine, prep_time, craving)

Important notes:
- prep_time must be a number (e.g., "30" for 30 minutes) or null if not specified
- allergies should be a list of specific allergies
- diet should be a specific diet type (e.g., "vegetarian", "vegan", "halal", "Keto", "zero sugar", "low sugar", "low carb")
- cuisine should be a specific cuisine type (e.g., "Italian", "Chinese", "Mexican")

Conversation:
{conversation_history}

Respond with a JSON like this:
{{
  "ingredients": [...],
  "preferences": {{
    "diet": "...",
    "allergies": [...],
    "cuisine": "...",
    "prep_time": "...",  # Must be a number or null
    "craving": "..."
  }}
}}
Only include fields if user has mentioned them. If prep_time is not specified, use null.
"""
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[
            {"role": "system", "content": "You are a helpful cooking assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    # Extract the generated text from the response
    content = response.choices[0].message.content

    # Parse the JSON response
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # If not valid JSON, return empty result
        result = {
            "ingredients": [],
            "preferences": {}
        }

    return result