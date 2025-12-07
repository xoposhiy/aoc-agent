# Decisions and Observations in the Advent of Code Agent Project

## Initial Approach and Pipeline

* A large, multi-stage pipeline for solving Advent of Code was initially designed.

  * Included downloading the statement, reformulating it, extracting samples, downloading input, prompting the LLM, iterative debugging, downloading part two, etc.
* This pipeline was judged too complex and fragile.
* A decision was made to start instead with a minimalistic agent: “solve Advent of Code with these tools.”

  * Tools: download statement, download input, run code, submit answer.
* This minimal setup already worked surprisingly well.

  * Emerging issues were fixable with local prompt adjustments or small tool tweaks.

## Improvements to Agent Behavior based on frequent errors

* Handling task statements

  * The agent was explicitly told to re-fetch the statement after solving part one.
  * Later the argument `part` was added to get_statement tool to even more reduce LLM confusion.
* Ensuring proper task completion

  * Agent was instructed that computing the answer is not enough — it must submit it.
* Reporting and diagnostics

  * Added `tool.complain` to allow the agent to report environment issues.

## Input Management and File Handling

* The input should not be stored in context due to potential size.

  * Decision: input is saved to a file instead, and the agent receives the file path.
* Careful instructions were added explaining exactly where the file is located.
* The agent sometimes confused file paths.

  * The prompt was simplified, removing path-related complexity, which eliminated those errors.
* Limit output size in the run_code tool to avoid spending too many tokens on useless data in the context. 

## Runtime and Performance Adjustments

* Some complaints were about timeouts from `runCode`.

  * Added clarification that most solutions should run within ~10 seconds, and `runCode` allows up to 60 seconds.
  * This reduced brute-force attempts.
* Added explicit information about the Kotlin version required for generated code.

  * Slight quality improvements followed.

## Model-Specific Behaviors

* Report Progress tool

  * Different models used it with different frequency and consistency.
  * Some models ignored it entirely.
* Instruction-following differences

  * Smaller models (e.g., GPT-5 Nano) follow instructions worse when many rules are present.
  * Larger models follow complex instruction sets more reliably.
* Model capabilities

  * Gemini 2.5 Mini can solve a large fraction of tasks.
  * GPT-5 Nano solves some tasks but uses many more tokens.

    * Frequently fails tool calls repeatedly (missing parameters, retrying many times).
    * Eventually still manages to solve some tasks.
    * Token usage—and thus cost—is significantly higher.
  * Small models like Gemini 2.5 Flash solve simple tasks faster than large models (e.g., Gemini 3).
  * Gemini models use 2–4× more tokens than GPT-5 on average and run slower.
  * ASCII-art decoding issues, Some Advent of Code tasks produce letters rendered in ASCII graphics.
    * Small models (e.g., Gemini 2.5 Flash) struggle to recognize these letters.
    * Larger models handle ASCII recognition without difficulty.
* Occasional incorrect behavior

  * Small models sometimes output plain chat responses instead of tool calls, and these are ignored by the agent.
  * Possible need for a “tool-only” enforcement mode.


## Tooling Description Strategy

* Only docstrings are used for tool descriptions, without schemas.

  * This still works: argument names are descriptive enough for models to understand them.


## Additional Observations

* IntCode interpreter memory effect
  * In some older Advent of Code years, later puzzles depend on the IntCode interpreter introduced earlier.
  * Models did not request previous days’ statements to recall IntCode.
  * Yet they still solved the puzzles, suggesting that IntCode was part of their pretraining and they can reconstruct it from memory.
    * This behavior is interesting and suggests exploring whether agents can learn to fetch statements from other days/years when needed.
    * Additional experiments would be useful to understand these behaviors better.

## 01 December

* Add more direct instructions for the clean code: decompose, meaningful names, ...
* Instruction to add comment at the beginning of the code-file to put the big picture into the context.
* Gemini became slow and stopped working...
* No dependencies for visualization. Need more instructions about available libs or give a way to install them.
* Unknown flaky problem for gpt-5-mini: 
   ```
  Error code: 400 - {'error': {
      'message': 'Invalid prompt: your prompt was flagged as potentially violating our usage policy. Please try again with a different prompt:https://platform.openai.com/docs/guides/reasoning#advice-on-prompting', 
      'type': 'invalid_request_error', 
      'param': None, 
      'code': 'invalid_prompt'}}
   ```

## 07 December

* Radically simplify prompt.
* Switch to fs tools + simplify run_code.
* A simple hint for the agent to generate images or animations helps.
```
The report must be very visual: has at least one png, svg or gif animations demonstrating the solution / task or input. 
To do so, you can use a set of provided tools.
```
* Remove specific instructions on what tools in which order to use. 