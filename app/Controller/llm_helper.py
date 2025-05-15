# llm_helper.py
import os
import json
from state import RecipeState
from typing import Dict
from dotenv import load_dotenv
import openai
import requests


load_dotenv()

def query_llm_for_preferences(conversation_history: str) -> Dict:
    print("\n==== ENTERING query_llm_for_preferences ====")
    print(f"DEBUG: Processing conversation: {conversation_history[:100]}...")
    
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
    # OpenRouter implementation
    print("DEBUG: Calling OpenRouter API")
    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": conversation_history}
            ],
            temperature=0.3
        )
        content = response.choices[0].message.content
        print(f"DEBUG: Raw LLM response: {content[:100]}...")
    except Exception as e:
        print(f"DEBUG: OpenRouter API error: {e}")
        content = '{}'

    # Parse the JSON response
    try:
        print("DEBUG: Attempting to parse JSON")
        # Try to clean up the response if it's not valid JSON
        cleaned_content = content
        # If response contains markdown code blocks, extract just the JSON
        if "```json" in cleaned_content:
            print("DEBUG: JSON is in markdown code block, extracting")
            start = cleaned_content.find("```json") + 7
            end = cleaned_content.find("```", start)
            if end == -1:
                end = len(cleaned_content)
            cleaned_content = cleaned_content[start:end].strip()
        elif "```" in cleaned_content:
            print("DEBUG: JSON is in code block, extracting")
            start = cleaned_content.find("```") + 3
            end = cleaned_content.find("```", start)
            if end == -1:
                end = len(cleaned_content)
            cleaned_content = cleaned_content[start:end].strip()
            
        # Try to find JSON object in the text
        if "{" in cleaned_content and "}" in cleaned_content:
            print("DEBUG: Finding JSON object in text")
            start = cleaned_content.find("{")
            # Count braces to find the matching closing brace
            brace_count = 0
            for i in range(start, len(cleaned_content)):
                if cleaned_content[i] == "{":
                    brace_count += 1
                elif cleaned_content[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            cleaned_content = cleaned_content[start:end]
            
        print(f"DEBUG: Cleaned content: {cleaned_content[:100]}...")
        result = json.loads(cleaned_content)
        print(f"DEBUG: Successfully parsed JSON: {result}")
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON parse error: {e}")
        # Return a minimal valid structure
        result = {
            "ingredients": [],
            "preferences": {
                "diet": None,
                "allergies": [],
                "cuisine": None,
                "prep_time": None,
                "craving": None
            }
        }

    # Ensure result has the right structure
    if "ingredients" not in result:
        print("DEBUG: Adding missing ingredients key")
        result["ingredients"] = []
    
    if "preferences" not in result:
        print("DEBUG: Adding missing preferences key")
        result["preferences"] = {}
        
    prefs = result["preferences"]
    for field in ["diet", "cuisine", "prep_time", "craving"]:
        if field not in prefs:
            prefs[field] = None
            
    if "allergies" not in prefs:
        prefs["allergies"] = []
    
    print(f"DEBUG: Final result: {result}")
    print("==== EXITING query_llm_for_preferences ====\n")
    return result