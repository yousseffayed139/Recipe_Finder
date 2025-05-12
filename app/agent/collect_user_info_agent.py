# agents.py
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from tools import extract_preferences_from_convo

# Init LLM
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="mistralai/mistral-7b-instruct:free",
    temperature=0.3
)

# Create the ReAct-style agent
collect_user_info_agent = initialize_agent(
    tools=[extract_preferences_from_convo],
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
