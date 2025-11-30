# Advent of Code Autonomous Agent – Design Document

## 1. Project Goal

Build a simple AI agent based on an LLM that automatically solves Advent of Code (AoC) problems by using a small set of
predefined tools.

Goals:

1. Gain experience with building agentic systems while keeping the initial pipeline minimal and controlled.
2. Compare the effect of various agentic workflow patterns.
3. Compare Kotlin, C# and Python in this context.

## 2. Overview of Initial Pipeline

The first version of the system will use a straightforward agentic loop.

### 2.1. Run Input

Each **run** of the pipeline is parameterized by:

* `year`
* `day`
* `lang ∈ {Python, Kotlin, C#}`

The language is fixed by the `lang` parameter for the whole run. The agent does not choose or change the language.

### 2.2. High-Level Flow for One Run

For a given `(year, day, lang)`:

1. The external orchestrator starts a run with input `(year, day, lang)`.
2. The agent uses tools to download the problem statement and personalized input.
3. The agent works on **part 1** of the puzzle:

* reads the statement for part 1;
* generates solution code in `lang`;
* executes code via the sandbox;
* submits an answer for part 1 via the submission tool;
* may iterate (fixing code and re-running) within the global tool-call limit.

4. If part 1 is successfully solved (AoC accepts the answer):

* the system fetches the updated statement for **part 2**;
* the agent works on part 2 in the same way (generate–run–submit, possibly iterating).

5. The run ends when either:

* both parts are solved (both answers accepted by AoC), or
* the global tool-call limit is exceeded, or
* the agent stops making tool calls without having solved the remaining part(s).

6. The system records structured statistics and detailed logs for this run.

> Boundary between parts: **everything before the first successful SubmitAnswer for part 1** is counted as work on part
1. Everything after that point is counted as work on part 2.

### 2.3. Tool-Call Limit per Run

* There is a **single global limit** on the total number of tool calls per run (including `RunGeneratedCode` and all
  other tools).
* The limit value is configured in global settings (configuration), not inside the agent logic.
* If the agent exceeds this limit, the run is terminated and marked as unsuccessful.

### 2.4. Run Orchestration

* The system does **not** decide how many runs to execute for a given `(year, day, lang)`.
* Runs are started externally (manually, by a script, or by another orchestration layer).
* The responsibility of this system is to execute a single run for `(year, day, lang)` and persist all relevant data for
  analysis.

## 3. Tools (Initial Set)

The agent interacts only through the following tools:

* **DownloadProblemStatement(year, day, part)**
  Fetch AoC task description for the given `year`, `day` and `part` (1 or 2).

* **DownloadInput(year, day)**
  Download the personalized puzzle input for the given `year` and `day`.

* **RunGeneratedCode(lang, code, input)**
  Execute LLM-generated code in a controlled sandbox.

    * Input: `lang`, `code`, `input`.
    * Output: full execution result (stdout, stderr, status, error message if any).
    * The full output of this tool is returned to the LLM and becomes part of the agent context, so the agent can debug,
      modify code, and call this tool again with improved code.

* **SubmitAnswer(year, day, answer)**
  Send the computed result back to Advent of Code. This tool is called separately for part 1 and part 2; the system
  tracks internally which part is being answered based on the current stage of the run.

These tools define all allowed actions for the agent in the minimal pipeline.

## 4. Language Comparison

The system should allow running the same problem-solving pipeline in different programming languages (Python, Kotlin,
C#) by varying the `lang` parameter of the run.

For each `(year, day, lang)` combination, multiple runs can be executed externally. This enables:

* Comparing success rate per language.
* Comparing token usage per language.
* Comparing error profiles per language.

The language is an input parameter; it is not chosen by the agent.

## 5. Logging and Metrics

### 5.1. Step-Level Logging

For each run, the system logs **every step**:

* All prompts sent to the LLM.
* All LLM responses.
* All tool calls (tool name, arguments, timestamps).
* All tool outputs.
* All generated code versions.
* All submitted answers and AoC responses.

These logs are intended for later qualitative analysis and debugging of agent behavior.

### 5.2. Per-Run and Per-Part Statistics

For each run (identified by a unique `run_id`), the system stores at least:

* `year`
* `day`
* `lang`
* `run_id`

For **each part** (part 1 and part 2), the system stores structured metrics:

* `success_partX` – whether the part was successfully solved (AoC accepted the answer).
* `error_type_partX` – if the part was not successfully solved, the final error type that caused termination for this
  part (e.g. wrong answer, execution error, compile error, timeout, tool limit exceeded, or agent stopped without
  solution).
* `time_spent_partX` – wall-clock time spent on this part (from the start of work on this part to its final outcome).
* `tokens_used_partX` – total number of LLM tokens consumed while working on this part (prompt + completion).
* `tool_call_counts_partX` – counts of tool calls used while working on this part, broken down by tool type (e.g. number
  of `DownloadProblemStatement`, `DownloadInput`, `RunGeneratedCode`, `SubmitAnswer` calls).

If part 1 is not successfully solved, then:

* `success_part2` is considered false (part 2 cannot be "successful" if part 1 was not solved).
* Metrics for part 2 can either be all zero / not-attempted or reflect actual behavior, depending on implementation, but
  logically part 2 is treated as not successfully solved.

## 6. Run Success Criteria

* Success is recorded **per part**:

    * `success_part1` – true if AoC accepts the answer for part 1.
    * `success_part2` – true if AoC accepts the answer for part 2 **and** part 1 was successfully solved.
* A run can thus have the following typical states:

    * part 1 failed, part 2 not solved;
    * part 1 succeeded, part 2 failed;
    * both parts succeeded.

Aggregate “success rates” and other statistics are computed later from these per-part metrics.

## 7. Future Extensions

Additional agentic patterns may be introduced later if the basic pipeline performs poorly:

* **Statement Simplification Stage** – transform the problem into a simplified version before generating code.
* **Self-Reflection Stage** – allow the model to critique and improve its own solution.
* **Multi-step Planning** – introduce a chain of subgoals inside the agent loop.
* **Retry Logic / Self-Repair Enhancements** – more structured analysis of incorrect outputs and regeneration
  strategies.

These are optional future additions and are not part of the initial scope.

## 8. Out of Scope (for now)

* Advanced search or planning algorithms.
* Multi-agent systems.
* Long-memory reasoning or scratchpad tooling beyond code execution.
* Dedicated automatic debugging loops beyond what the LLM can already do using the existing tools within the global
  tool-call limit.

## 9. Technology Stack

Agent framework: LangChain, Python

LLM providers and models:

* Gemini models

* OpenAI Codex.

## 10. Summary

This project sets up a minimal but extendable experimental environment for observing how an LLM performs on Advent of
Code tasks when limited to a small, well-defined set of tools.

The initial version focuses on:

* A simple tool-based agent loop for a single `(year, day, lang)` run.
* Sequential solution of part 1 and part 2 within one run.
* Strict separation of metrics per part.
* Detailed logging of all steps and structured statistics per run.

The primary purpose is educational and exploratory: to gain intuition about agent design, tool interfaces, and
cross-language code generation quality, and to build a base for later experiments with more advanced agentic patterns.

