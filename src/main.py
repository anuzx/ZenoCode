from openai import OpenAI

from src import config
from src.tools import TOOL_SCHEMAS

client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)


def call_llm(messages, tools=None):
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=messages,
        tools=tools or TOOL_SCHEMAS,
    )
    usage = response.usage.model_dump()
    flat = {k: v for k, v in usage.items() if isinstance(v, int)}
    return response.choices[0].message, flat
