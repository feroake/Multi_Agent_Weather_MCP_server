# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project Overview

This is a weather-focused MCP (Model Context Protocol) server built with Python and the FastMCP library. It integrates with Claude Code on desktop to provide weather-related tools including weather alerts and forecasts.

# Architecture

The project uses a modular structure:

- **weather.py**: Main MCP server implementation containing:
  - `mcp`: FastMCP server instance
  - HTTP client for NWS (National Weather Service) API integration
  - Two main tools: `get_alerts` (by state) and `get_forecast` (by lat/lon)
  - Helper functions for API requests and data formatting

- **main.py**: Entry point that calls `main()` which starts the MCP server via `mcp.run(transport="stdio")`

- **pyproject.toml**: Project configuration with uv as package manager

Key architectural pattern: The server uses async HTTP requests through httpx to fetch data from weather.gov's API, which returns GeoJSON responses. Error handling is built-in via try/except blocks that return None on failures.

# Commands

## Setup and Development

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run python main.py

# Run a single test (if tests exist)
uv run pytest tests/test_weather.py -v

# Run all tests
uv run pytest -v

# Run a specific test
uv run pytest -k test_name

# Check code style (if linting configured)
uv run ruff check .

# Format code
uv run ruff format .
```

## Development Workflow

1. Activate virtual environment (if needed): `.venv\Scripts\activate`
2. Make changes to weather.py
3. Run `uv run python main.py` to test the server
4. Send messages through the MCP interface to Claude

# Dependencies

- httpx: Async HTTP client for NWS API requests
- mcp[cli]: Model Context Protocol library with CLI support

# API Integration

The server uses NOAA's National Weather Service API (weather.gov):

- **Alerts**: `GET /alerts/active/area/{state}` - Returns active weather alerts by state
- **Forecast**: Multi-step endpoint:
  1. `GET /points/{lat},{lon}` - Get grid metadata
  2. Follow redirect to actual forecast endpoint
- All requests use `application/geo+json` accept header
- User-Agent header is set to "weather-app/1.0"

# Tools Available

1. **get_alerts(state)**: Fetch active weather alerts for a US state (e.g., "CA", "NY")
2. **get_forecast(latitude, longitude)**: Get weather forecast for a geographic location

# Common Issues

- API requests may fail due to network issues or rate limiting - the server handles this gracefully
- Some locations may not have forecast data available (returns error message)
- State codes must be valid two-letter US state codes

# Python Environment

- Python 3.14+ required
- Uses `uv` for package management
- Virtual environment at `.venv`


## Multi‑Agent Pipeline Expansion (Weather + Planning + Evaluation)

Extend the existing NWS Weather MCP server into a multi‑agent system with three distinct agents:

1. **Weather Agent** – the existing MCP server that fetches alerts and forecasts from the National Weather Service API. Keep it as a dedicated tool‑calling agent.

2. **Planner Agent** – a new agent that:
   - Accepts high‑level user requests like "Plan a safe hiking day in Colorado next Tuesday" or "Should I delay my crop spraying in Kansas?"
   - Breaks the request into subtasks (e.g., “get forecast for location X on date Y”, “check alerts for that area”).
   - Calls the Weather Agent via MCP to retrieve the required data.
   - Synthesizes the raw weather data into a human‑readable answer or recommendation.

3. **Evaluator Agent** – a third agent that:
   - Reviews the Planner’s final output (the answer/recommendation).
   - Checks for factual consistency against the raw weather data returned by the Weather Agent.
   - Flags hallucinations, missing alerts, or contradictory statements.
   - Returns a pass/fail or confidence score (e.g., 0–100) plus a short justification.

**Implementation requirements:**
- All three agents must run as separate logical components (can be implemented as separate functions/classes or separate MCP servers).
- Use structured logging so each agent’s inputs and outputs are traceable.
- Provide a simple orchestration script that:
  - Takes a user query.
  - Runs Planner → Weather → Evaluator in sequence.
  - Prints the Planner’s response and the Evaluator’s score/comment.
- Add a `tests/` folder with at least three end‑to‑end test cases where the Evaluator correctly accepts good outputs and rejects bad ones (e.g., intentionally swap a wrong forecast to test hallucination detection).

**Example user query to support:**
> “I’m camping in Grand Canyon National Park this Saturday. What’s the weather and any alerts I should know about?”

Expected flow:
- Planner extracts: location=Grand Canyon, date=Saturday, needs=forecast+alerts.
- Weather Agent fetches actual NWS data.
- Planner writes a natural response.
- Evaluator verifies that the response includes both forecast and alerts (or explicitly states none) and that no invented numbers appear.