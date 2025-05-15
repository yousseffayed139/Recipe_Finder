# app/agent/tools/llm_fallback_tool.py
from langchain_core.tools import tool


@tool
def llm_fallback_tool(ingredients_and_preferences: str) -> str:
    """
    Use creative thinking to generate a complete recipe when APIs fail to find suitable matches.
    
    Inputs:
        - ingredients_and_preferences: A string containing ingredients and any preferences like 
          diet, allergies, cuisine type, or other restrictions.
          
    Returns:
        - A complete recipe suggestion with ingredients, measurements, and detailed instructions.
          The recipe should be realistic, with proper cooking techniques and reasonable amounts.
    """
    return (
        f"Based on your ingredients and preferences ({ingredients_and_preferences}), "
        f"I'll help you create a complete recipe. "
        f"Consider how these ingredients work together, the cooking methods that would bring out their flavors, "
        f"and how to structure a cohesive dish. "
        f"Be sure to include specific measurements, cooking times, temperatures, and detailed step-by-step instructions. "
        f"The recipe should follow proper culinary techniques and be formatted as a complete JSON recipe object."
    )
