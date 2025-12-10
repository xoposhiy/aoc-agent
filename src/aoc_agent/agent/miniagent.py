from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterator, cast

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_community.agent_toolkits import FileManagementToolkit

from ..core.aoc_client import AocClient
from ..core.llm import create_llm, TokenCollector
from .context import AgentContext
from .tools import Lang, AocToolbox
from langchain_core.prompts import ChatPromptTemplate


system_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an expert in algorithms and educator, who participate in Advent of Code event 
            solving tasks just to write engaging educational reports for computer science students.
            Try to make it entertaining, fun and educative! Jokes, smart sarcastic comments, 
            memes and puns and are appreciated (if they are funny and unexpected!)
            
            ## Solving
            
            First of all brainstorm ideas and approaches to solve the task. 
            Write the most viable ideas_part1.md into ideas.md and ideas_part2.md files.
              
            You can write small programs to analyze input data, if you need to choose between several approaches.
                        
            Use tools 'run_code' and 'submit_result' to solve the tasks.
            
            ## Report
            
            The report MUST be an Markdown file named 'final_report.md', in the same directory as the code files and input.txt
            The report MUST be written in RUSSIAN language.
            The report must be very visual: has at least one png, svg or gif animations demonstrating the solution / task or input. 
            You may use one of the libraries: Pillow Matplotlib NetworkX imageio.
            
            To do so, you can use a set of provided tools.
            
            Review your final report after writing it and verify:
            - Is there more than one approach to the same task?
            - Are there any interesting insights or "gotchas" encountered?
            - Are there any visualizations that you think are interesting and entertaining?
            - Are there any jokes or puns or quotes that you think are funny and unexpected?
            - Is Narrative engaging and educative?
            - Language is clear and pleasant to read?
            - Logical structure of the text is easy to follow and fits educative goal?
            
            Create a file critique.md with your critique of the report and suggestions for improvement.
            
            After that improve report according to your critique and write it again.
            
            ## Fast Code
            
            All tasks can be solved with efficient algorithms in less than 10 seconds. 
            Your code should not work significantly longer than that.
            Be sure your implementation is optimized enough to fit in 10 seconds, avoid naive brute force.

            ## Complain if environment is broken
            
            Use tool 'complain' to report if something goes unexpectedly wrong with the environment: 
            problem statement does not contain statement, run_code tool is not working, etc.
            """
        )
    ]
)

task_prompt_template = ChatPromptTemplate.from_template(
    "Solve the task of year {year}, day {day} with programming language {lang}. Submit answers and write a report!"
)


@dataclass
class MiniAgent:
    """A minimal agent with tools."""

    def execute(self, client: AocClient, context: AgentContext) -> Iterator[Any]:
        toolbox = AocToolbox(client, context)
        fs_toolkit = FileManagementToolkit(root_dir=context.working_dir)
        tools = fs_toolkit.get_tools() + toolbox.make_tools()
        llm = create_llm(context.model_name, tools)
        agent_runnable = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt.format_messages()[0].content
        )
        lang = cast(Lang, context.language)
        initial_state : dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": task_prompt_template.format_messages(year=context.year, day=context.day, lang=lang)[0].content,
                }
            ]
        }

        return agent_runnable.stream(
            cast(Any, initial_state),
            config=cast(RunnableConfig, {
                "configurable": {"run_id": context.run_id},
                "callbacks": [TokenCollector(context)]
            }),
        )
