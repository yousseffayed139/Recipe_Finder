# app/agent/tools/llm_fallback_tool.py
from langchain_core.tools import tool


@tool
def llm_fallback_tool(question: str) -> str:
    """
    Use the LLM to provide a general recipe suggestion when APIs fail.
    Inputs:
        - question: Freeform user query about what they want to eat.
    Returns:
        - A simple recipe or food suggestion.
    """
    return f"I'm not sure what to find from APIs, but here's a creative suggestion:\n" \
           f"How about making a dish using: {question}?\nTry combining your ingredients in a stir-fry or salad!"
