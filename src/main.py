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

    message = response.choices[0].message

    completion_details = response.usage.completion_tokens_details
    prompt_details = response.usage.prompt_tokens_details

    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None),
        "cached_tokens": getattr(prompt_details, "cached_tokens", None),
    }

    return message, usage
