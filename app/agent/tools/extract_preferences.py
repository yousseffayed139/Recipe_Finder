# tools.py
from typing import Dict
from langchain_core.tools import tool
from llm_helper import query_llm_for_preferences

@tool
def extract_preferences_from_convo(conversation: str) -> Dict:
    """
    Extract structured user preferences (ingredients, diet, allergies, etc.) from conversation text.
    """
    return query_llm_for_preferences(conversation)
