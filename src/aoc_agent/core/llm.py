from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from aoc_agent.agent.context import AgentContext

class TokenCollector(BaseCallbackHandler):
    def __init__(self, context: AgentContext):
        self.context = context

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        for generations in response.generations:
            for gen in generations:
                if hasattr(gen, 'message') and hasattr(gen.message, 'usage_metadata'):
                    usage = gen.message.usage_metadata
                    if usage:
                        self.context.output_tokens += usage.get('output_tokens', 0)


def create_llm(model_name: str, tools: List[Any]):
    if "gpt" in model_name or "o1" in model_name:
        return ChatOpenAI(model=model_name).bind_tools(tools, tool_choice="any")
    elif "claude" in model_name:
        return ChatAnthropic(model=model_name).bind_tools(tools, tool_choice="any")
    elif "gemini" in model_name:
        return ChatGoogleGenerativeAI(model=model_name).bind_tools(tools, tool_config={'function_calling_config': {'mode': 'ANY'}})
    else:
        return ChatOllama(model=model_name).bind_tools(tools)
