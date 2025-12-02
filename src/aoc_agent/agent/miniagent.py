from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from rich import print

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain.agents.middleware import ModelRetryMiddleware

from .tools import Lang, AocToolbox
from .context import AgentContext
from ..core.aoc_client import AocClient
from .prompts import system_prompt_template, task_prompt_template
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

MODEL_ALIASES = {
    "gpt5": "gpt-5",
    "gpt5m": "gpt-5-mini",
    "g3": "gemini-3-pro-preview",
    "g25f": "gemini-2.5-flash",
    "co45": "claude-opus-4-5",
}

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

@dataclass
class MiniAgent:
    """A minimal agent with tools."""

    def run_agent(self, year: int, day: int, lang: Lang, model_name: str = "gemini-2.5-flash", no_report: bool = False):
        model_name = MODEL_ALIASES.get(model_name, model_name)
        start_time_friendly = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = start_time_friendly + "_" + str(year) + "_" + str(day) + "_" + str(lang) + "_" + model_name.replace(":","-") + "_" + str(uuid.uuid4())[:8]
        run_dir = os.path.join("data", "run", run_id)
        os.makedirs(run_dir, exist_ok=True)

        print(
            f"[bold green]AoC MiniAgent starting[/bold green]: year={year}, day={day}, lang={lang}, run_id={run_id} model={model_name}"
        )

        client = AocClient()
        context = AgentContext(run_id=run_id, start_time=(time.time()))
        toolbox = AocToolbox(client, context)
        tools = toolbox.make_tools(language=lang)

        if lang != "python":
            no_report = True

        if "gpt" in model_name or "o1" in model_name:
            llm = ChatOpenAI(model=model_name).bind_tools(tools, tool_choice="any")
        elif "claude" in model_name:
            llm = ChatAnthropic(model=model_name).bind_tools(tools, tool_choice="any")
        elif "gemini" in model_name:
            llm = ChatGoogleGenerativeAI(model=model_name).bind_tools(tools, tool_config={'function_calling_config': {'mode': 'ANY'}})
        else:
            llm = ChatOllama(model=model_name).bind_tools(tools)

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt_template.format_messages(model_name=model_name)[0].content
        )

        token_collector = TokenCollector(context)

        history_file = os.path.join(run_dir, "history.json")
        history = []
        try:
            for chunk in agent.stream({ # type: ignore
                    "messages": [
                        {
                            "role": "user",
                            "content": task_prompt_template.format_messages(year=year, day=day, lang=lang)[0].content,
                        }
                    ]
                },
                config={ # type: ignore
                    "configurable": {"run_id": run_id},
                    "callbacks": [token_collector]
                },

            ):
                history.append(chunk)
                with open(history_file, "w") as f:
                    json.dump(history, f, indent=2, default=str)
                
                if context.final_report_written:
                    print("[green]Final report written. Stopping agent.[/green]")
                    break

                if no_report and (context.part2_finished or (day == 25 and context.part1_finished)):
                    print("[green]All parts solved. Skipping final report and stopping agent.[/green]")
                    break
            print("Writing metadata.json...")

            metadata = {
                "run_id": run_id,
                "year": year,
                "day": day,
                "lang": lang,
                "model": model_name,
                "agent_name": "MiniAgent",
                "start_time": datetime.fromtimestamp(context.start_time).isoformat(),
                "part1_duration": context.part1_duration,
                "part1_output_tokens": context.part1_output_tokens,
                "part1_solved": context.part1_finished,
                "part2_solved": context.part2_finished or day == 25,
                "part12_output_tokens": context.part2_output_tokens,
                "part12_duration": context.part2_duration,
                "report_output_tokens": context.output_tokens - context.part1_output_tokens,
                "part1_incorrect": context.part1_incorrect,
                "part2_incorrect": context.part2_incorrect,
                "part1_run_code_errors": context.part1_run_code_errors,
                "part2_run_code_errors": context.part2_run_code_errors,
                "part1_run_code_success": context.part1_run_code_success,
                "part2_run_code_success": context.part2_run_code_success
            }

            with open(os.path.join(run_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
        except GeneratorExit:
            return
        except Exception as e:
            print(f"[red]Unexpected error running agent. Ignore metadata!:\n{e}[/red]")




