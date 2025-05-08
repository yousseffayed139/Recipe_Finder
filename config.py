OPENROUTER_API_KEY = "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"

from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    model="openrouter/qwen/qwen3-235b-a22b:free",
    openai_api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)
