# app/agent/recipe_agent.py

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from app.agent.tools.spoonacular_tool import spoonacular_search
from app.agent.tools.tavily_tool import tavily_search
from app.agent.tools.llm_fallback_tool import llm_fallback_tool

load_dotenv()

system_prompt = (
    "You are a helpful recipe assistant.\n"
    "Given user preferences, suggest only relevant recipes. Each recipe should include a title, a list of ingredients, and clear preparation instructions.\n"
    "Avoid tool metadata, or system messages — return only the final recipe suggestions in plain text.\n"
)

llm = ChatOpenAI(
    model="google/gemini-2.5-pro-exp-03-25",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.5
)

tools = [spoonacular_search, tavily_search, llm_fallback_tool]

# ReAct agent (no function calling needed)
recipe_agent = create_react_agent(llm, tools, prompt=system_prompt)
