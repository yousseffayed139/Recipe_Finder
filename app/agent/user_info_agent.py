# app/agent/user_info_agent.py

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from agent.tools.extract_preferences import extract_preferences_from_convo

load_dotenv()

system_prompt = (
    "You are a helpful assistant that extracts cooking preferences from a user conversation.\n"
    "Your goal is to gather information such as dietary restrictions, preferred cuisines, disliked ingredients, and available ingredients.\n"
    "ALWAYS use the extract_preferences_from_convo tool to process the conversation input.\n"
    "DO NOT make up information that isn't mentioned by the user.\n"
    "The output from the tool should be in the exact format:\n"
    "{\n"
    "  \"ingredients\": [list of ingredients mentioned by user],\n"
    "  \"preferences\": {\n"
    "    \"diet\": \"specific diet mentioned or null\",\n"
    "    \"allergies\": [list of allergies mentioned],\n"
    "    \"cuisine\": \"specific cuisine type mentioned or null\",\n"
    "    \"prep_time\": \"number of minutes or null\",\n"
    "    \"craving\": \"specific craving mentioned or null\"\n"
    "  }\n"
    "}\n"
    "Return ONLY this structured data, with no additional explanations or text."
)

print(f"DEBUG: Initialized user_info_agent with system prompt: {system_prompt}")

llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct:free",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.3
)

tools = [extract_preferences_from_convo]

user_info_agent = create_react_agent(llm, tools, prompt=system_prompt)
