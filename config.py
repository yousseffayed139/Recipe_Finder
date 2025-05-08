import os

from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    model="openrouter/qwen/qwen3-235b-a22b:free",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)
