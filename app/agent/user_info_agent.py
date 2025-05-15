# app/agent/user_info_agent.py

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import json

from agent.tools.extract_preferences import extract_preferences_from_convo

load_dotenv()

system_prompt = (
    "You are a friendly and helpful chef's assistant named Sous-Chef who engages in natural conversation with users to discover their cooking preferences and available ingredients.\n\n"
    
    "CONVERSATIONAL GUIDELINES:\n"
    "1. Be warm, friendly, and use a casual tone like a helpful friend who loves cooking\n"
    "2. Ask thoughtful follow-up questions to gather missing information in a natural way\n"
    "3. Acknowledge and validate the user's preferences (e.g., 'Great choice! Italian cuisine has so many delicious options.')\n"
    "4. If the user seems unsure, offer gentle suggestions (e.g., 'Do you have any vegetables like carrots or bell peppers that could work well?')\n"
    "5. Respond naturally to small talk but gently guide conversation back to recipe needs\n"
    "6. Use inclusive language that assumes diverse cooking skill levels\n\n"
    
    "INFORMATION TO COLLECT:\n"
    "- Available ingredients (essential to gather)\n"
    "- Dietary restrictions (vegetarian, vegan, gluten-free, etc.)\n"
    "- Food allergies or intolerances\n"
    "- Preferred cuisine types (Italian, Mexican, Thai, etc.)\n"
    "- Time constraints for meal preparation\n"
    "- Specific cravings or dish types\n\n"
    
    "CRITICAL RULES:\n"
    "1. NEVER suggest or include ingredients that the user hasn't explicitly mentioned\n"
    "2. NEVER make assumptions about what ingredients the user has available\n"
    "3. If the user mentions preferences (like 'high protein' or 'low carb') without listing specific ingredients, you MUST ask them what ingredients they have available\n"
    "4. The ingredients list should ONLY contain items explicitly mentioned by the user\n"
    "5. Leave the ingredients list EMPTY if the user hasn't explicitly mentioned any ingredients\n\n"
    
    "IMPORTANT: You MUST use the extract_preferences_from_convo tool to extract structured data before providing a response to the user. This lets you respond naturally while ensuring structured data is captured. Every response must include both:\n"
    "1. A natural conversational reply to the user that feels like a real dialogue\n"
    "2. Hidden structured data that follows the required format\n\n"
    
    "STRUCTURED DATA FORMAT RULES:\n"
    "You must append this JSON at the very end of your response, prefixed with <structured_data> and followed by </structured_data>. This section will be removed before showing to the user:\n"
    "{\n"
    "  \"ingredients\": [list of ingredients mentioned by user],\n"
    "  \"preferences\": {\n"
    "    \"diet\": \"specific diet mentioned or null\",\n"
    "    \"allergies\": [list of allergies mentioned],\n"
    "    \"cuisine\": \"specific cuisine type mentioned or null\",\n"
    "    \"prep_time\": \"number of minutes or null\",\n"
    "    \"craving\": \"specific craving mentioned or null\"\n"
    "  }\n"
    "}\n\n"
    
    "Example response format (when user only mentions preferences but no ingredients):\n"
    "'I understand you're looking for a high protein, low carb meal. That's a great choice! To help you find the perfect recipe, could you tell me what ingredients you have available to work with?'\n"
    "<structured_data>{\"ingredients\": [], \"preferences\": {\"diet\": \"low carb, high protein\", \"allergies\": [], \"cuisine\": null, \"prep_time\": null, \"craving\": null}}</structured_data>"
)

# Create the model with appropriate settings for conversation
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct:free",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0.7  # Slightly higher temperature for more conversational responses
)

tools = [extract_preferences_from_convo]

user_info_agent = create_react_agent(llm, tools, prompt=system_prompt)

# Function to extract structured data from response
def extract_structured_data(response):
    """Extract structured data from between the <structured_data> tags"""
    try:
        if isinstance(response, dict) and "messages" in response:
            # Extract from LangChain message format
            messages = response.get("messages", [])
            content = ""
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content.strip()
                    break
        elif isinstance(response, str):
            content = response.strip()
        else:
            # Get content from other formats
            content = getattr(response, "content", str(response)).strip()
        
        # Extract the structured data
        import re
        match = re.search(r'<structured_data>(.*?)</structured_data>', content, re.DOTALL)
        if match:
            data_str = match.group(1).strip()
            return json.loads(data_str)
        
        return {}
    except Exception:
        return {}
        
# Function to get only the conversational part of a response
def get_conversation_response(response):
    """Get only the conversational part of a response, removing the structured data"""
    try:
        if isinstance(response, dict) and "messages" in response:
            # Extract from LangChain message format
            messages = response.get("messages", [])
            content = ""
            for msg in reversed(messages):
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content.strip()
                    break
        elif isinstance(response, str):
            content = response.strip()
        else:
            # Get content from other formats
            content = getattr(response, "content", str(response)).strip()
        
        # Remove the structured data
        import re
        result = re.sub(r'<structured_data>.*?</structured_data>', '', content, flags=re.DOTALL).strip()
        return result
    except Exception:
        if 'content' in locals():
            return content  # Return the original content if there's an error
        else:
            return str(response)
