[2025-12-02 13:14] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "language support",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN repository lacks Lean language support THEN implement LeanRunner and register language"
}

[2025-12-02 14:34] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "naming conventions",
    "ERROR": "Used language id \"lean\" instead of \"lean4\"",
    "NEW INSTRUCTION": "WHEN referencing Lean language in codebase THEN use identifier \"lean4\" consistently"
}

[2025-12-02 20:17] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report charts",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN rendering Token Usage Comparison XY charts THEN cap canvas size to 500px square"
}

[2025-12-02 21:37] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report charts",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN generating Model Comparison XY charts THEN set axes to models, plot days as points using averaged output tokens"
}

[2025-12-02 21:55] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report comparisons",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN building report containing Language Head-to-Head section THEN add Models Head-to-Head pairwise comparison table"
}

[2025-12-07 11:47] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "runners interface",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN modifying language runners THEN align API with CodeRunner interface and signatures"
}

[2025-12-07 11:57] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "tools interface",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN final report is ready THEN provide submit_report tool, end loop, write metadata.json"
}

[2025-12-07 12:09] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "refactor run_code",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN editing AocToolbox.run_code implementation THEN extract shared runner logic into a reusable helper"
}

[2025-12-07 12:23] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "agent context",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN accessing agent working directory THEN use AgentContext.working_dir instead of recomputing"
}

[2025-12-07 12:27] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "puzzle input",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN after download_puzzle_input saves input.txt THEN copy input.txt into AgentContext.working_dir"
}

[2025-12-07 17:45] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report sections",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN building website reports THEN add Code Executions section with executed runs summary table"
}

[2025-12-08 23:56] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report tables",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN generating Token Usage Comparison table THEN render per-column scales, sort columns by filled count, constrain table width"
}

[2025-12-09 00:22] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "report tables",
    "ERROR": "Used minimum tokens instead of average",
    "NEW INSTRUCTION": "WHEN generating Token Usage Comparison table THEN compute per-cell average tokens over both-parts-solved runs"
}

[2025-12-10 00:24] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "report tables",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN generating Token Usage Comparison table THEN filter runs to lang == \"python\" before aggregations"
}

[2025-12-10 15:58] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "agents architecture",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN creating MiniAgent runnable THEN construct required tools internally and do not require external tools"
}

[2025-12-10 16:07] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "llm configuration",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN binding tools for OpenAI or Anthropic models THEN set tool_choice to \"any\""
}

[2025-12-10 16:47] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "tools creation",
    "ERROR": "AgentRunner is creating and managing tools",
    "NEW INSTRUCTION": "WHEN preparing agent runnable in AgentRunner THEN avoid tool creation; let MiniAgent construct and bind tools"
}

[2025-12-10 21:39] - Updated by Junie
{
    "TYPE": "new instructions",
    "CATEGORY": "agents architecture",
    "ERROR": "-",
    "NEW INSTRUCTION": "WHEN running agent loop in AgentRunner THEN call MiniAgent.stream which manages TokenCollector"
}

[2025-12-10 21:45] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "typing annotations",
    "ERROR": "Passed dict to agent_runnable.stream causing InputT type mismatch",
    "NEW INSTRUCTION": "WHEN calling agent_runnable.stream with dict state THEN cast input to Any before call"
}

[2025-12-10 21:46] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "typing annotations",
    "ERROR": "Passed plain dict as config to stream",
    "NEW INSTRUCTION": "WHEN calling agent_runnable.stream with config dict THEN cast config to RunnableConfig or Any"
}

[2025-12-10 22:39] - Updated by Junie
{
    "TYPE": "correction",
    "CATEGORY": "cli constants",
    "ERROR": "Placed MODEL_ALIASES in core/constants instead of cli",
    "NEW INSTRUCTION": "WHEN resolving model names in CLI THEN define MODEL_ALIASES in cli and map inputs accordingly"
}

