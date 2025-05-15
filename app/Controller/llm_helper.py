# llm_helper.py
import os
import json
from state import RecipeState
from typing import Dict
from dotenv import load_dotenv
import openai
import requests
import logging

# Get logger
logger = logging.getLogger("recipe_finder")

load_dotenv()

def query_llm_for_preferences(conversation_history: str) -> Dict:
    """Uses LLM to extract structured user preferences from conversation."""
    logger.info("Querying LLM for preferences")
    prompt = f"""
You are a helpful cooking assistant. Extract the following fields from the user's conversation:
- Ingredients (a list of individual ingredients)
- Preferences (diet, allergies, cuisine, prep_time, craving)

VERY IMPORTANT ABOUT INGREDIENTS: 
1. Extract ALL information across the entire conversation history - both initial messages and follow-up messages
2. Use context to determine whether to REPLACE or COMBINE ingredients:

   REPLACE ingredients when:
   - User clearly expresses dissatisfaction with previous recipe (e.g., "I'm not in the mood for this")
   - User explicitly mentions replacement (e.g., "I'd like to use X instead")
   - User signals a complete change in direction (e.g., "Let's try something completely different")
   
   COMBINE ingredients when:
   - User simply mentions new ingredients without indicating replacement (e.g., "What about bacon?")
   - User explicitly mentions addition (e.g., "I also have X")
   - User is expanding options without rejecting previous ones (e.g., "I found some X in my fridge")

3. When in doubt about whether to replace or combine, prefer COMBINING ingredients unless there's a clear signal to replace

4. When a user expresses dissatisfaction with a recipe (e.g., "I'm not in the mood for this") and then mentions new ingredients:
   - This is a clear signal to REPLACE previous ingredients

EXAMPLE CONVERSATIONS AND EXPECTED EXTRACTION:
1. User: "I have chicken and rice"
   Later: "I'm not in the mood for this. I have shrimp and pasta"
   Result: ingredients = ["shrimp", "pasta"] (REPLACE)

2. User: "I have eggs"
   Later: "What about bacon?"
   Result: ingredients = ["eggs", "bacon"] (COMBINE)
   
3. User: "I have tomatoes"
   Later: "I'd prefer to use cucumbers instead"
   Result: ingredients = ["cucumbers"] (REPLACE)
   
4. User: "I have flour and sugar"
   Later: "I also found some chocolate chips"
   Result: ingredients = ["flour", "sugar", "chocolate chips"] (COMBINE)

VERY IMPORTANT ABOUT ALLERGIES AND PREFERENCES:
1. Pay special attention to allergies - if the user mentions being allergic to something, make sure to include it
2. If the user mentions "I'm allergic to X" or "I can't eat X" or "I don't like X", add X to the allergies list

Important notes:
- prep_time must be a number (e.g., "30" for 30 minutes) or null if not specified
- allergies should be a list of specific allergies or disliked foods
- diet should be a specific diet type (e.g., "vegetarian", "vegan", "halal", "Keto", "zero sugar", "low sugar", "low carb")
- cuisine should be a specific cuisine type (e.g., "Italian", "Chinese", "Mexican")

Conversation:
{conversation_history}

STRICT JSON FORMAT RULES:
1. Return ONLY a valid JSON object - NO explanations, markdown or additional text
2. Use double quotes for all keys and string values, not single quotes
3. All arrays and objects must be properly formatted
4. Ensure the output is directly parseable by JSON.loads()
5. DO NOT use code blocks (```) or any other formatting
6. DO NOT include any introductory text like "Here are the extracted preferences"
7. For missing fields, use null instead of empty strings/arrays
8. Avoid trailing commas and other JSON syntax errors
9. DO NOT include comments (lines with #) in your JSON output

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
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
        logger.info("Received LLM response")
    except Exception:
        logger.info("Error calling OpenRouter API")
        content = '{}'

    # Parse the JSON response
    try:
        # Try to clean up the response if it's not valid JSON
        cleaned_content = content
        # If response contains markdown code blocks, extract just the JSON
        if "```json" in cleaned_content:
            start = cleaned_content.find("```json") + 7
            end = cleaned_content.find("```", start)
            if end == -1:
                end = len(cleaned_content)
            cleaned_content = cleaned_content[start:end].strip()
        elif "```" in cleaned_content:
            start = cleaned_content.find("```") + 3
            end = cleaned_content.find("```", start)
            if end == -1:
                end = len(cleaned_content)
            cleaned_content = cleaned_content[start:end].strip()
            
        # Try to find JSON object in the text
        if "{" in cleaned_content and "}" in cleaned_content:
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
            
        result = json.loads(cleaned_content)
        logger.info("Successfully parsed LLM JSON response")
    except json.JSONDecodeError:
        logger.info("JSON parsing error, using default structure")
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
        result["ingredients"] = []
    
    if "preferences" not in result:
        result["preferences"] = {}
        
    prefs = result["preferences"]
    for field in ["diet", "cuisine", "prep_time", "craving"]:
        if field not in prefs:
            prefs[field] = None
            
    if "allergies" not in prefs:
        prefs["allergies"] = []
    
    return result