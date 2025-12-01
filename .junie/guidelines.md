# Project Guidelines

## Tech Stack
- **Language**: Python 3.10+
- **Dependency Manager**: Poetry
- **Frameworks**: LangChain, Pydantic, Rich
- **Testing**: Pytest

## Project Structure
- `src/aoc_agent/`: Main package.
    - `agent/`: Core logic (MiniAgent, prompts, tools).
    - `core/`: Infrastructure (AoC client, runners).
    - `cli.py`: Entry point.
- `tools/`: Helper scripts (site generation).
- `data/`: Run artifacts and logs.

## Setup & Execution
1. **Install Dependencies**:
   ```bash
   poetry install
   ```
2. **Environment Variables**:
   Set `AOC_SESSION` and relevant LLM keys (`OPENAI_API_KEY`, `GOOGLE_API_KEY`) in `.env` or environment.
3. **Run Agent**:
   ```bash
   poetry run aoc-agent [args]
   ```

## Scripts
- **Site Generation**:
  ```bash
  poetry run python tools/generate_site.py
  ```

## Testing
- Place tests in `tests/` directory.
- Run tests:
  ```bash
  poetry run pytest
  ```

## Best Practices
- **Code Organization**: Keep agent logic in `agent/` and infrastructure in `core/`.
- **Dependencies**: Add new packages via `poetry add`.
- **Style**: Follow standard Python PEP 8 conventions.
