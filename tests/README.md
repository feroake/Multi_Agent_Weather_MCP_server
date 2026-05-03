# Weather MCP Server Tests

This directory contains unit and integration tests for the Weather MCP Server.

## Running Tests

### Run all tests:
```bash
uv run pytest tests/ -v
```

### Run with coverage:
```bash
uv run pytest tests/ -v --cov=weather --cov-report=html
```

### Run specific test file:
```bash
uv run pytest tests/test_main.py -v
```

### Run specific test class:
```bash
uv run pytest tests/test_agents.py::TestWeatherAgent -v
```

### Run with verbose output and show slowest tests:
```bash
uv run pytest tests/ -v -s --durations=5
```

## Test Structure

### test_main.py
- Tests for `weather.py` functions:
  - `analyze()` - Analyze weather for a state
  - `plan()` - Generate plan for weather-related queries
  - `sprayer_plan()` - Generate plan for agricultural spraying
  - `forecast_only()` - Get only forecast data
  - `spray_check()` - Check if spraying is safe
  - `forecast_check()` - Check forecast for a state
  - `run_pipeline()` - Run complete weather pipeline
  - `get_current_weather_data()` - Get current weather data
  - `generate_alert_alert()` - Generate alert data
  - `generate_forecast_data()` - Generate forecast data

### test_agents.py
- Tests for agent classes:
  - `WeatherAgent` - Analyze weather data
  - `PlannerAgent` - Plan weather-related activities
  - `EvaluatorAgent` - Evaluate weather-related answers
  - `WeatherReport` - Weather data container
  - `WeatherPlan` - Plan container
  - `EvaluationResult` - Evaluation result container

### fixtures.py
- Mock weather data for testing
- Mock alert data
- Mock forecast data
- Helper functions for test fixtures

### conftest.py
- Pytest configuration
- Shared fixtures for tests

## Test Fixtures

The tests use mock data to avoid making real API calls:

- `MOCK_NWS_ALERTS` - Mock NWS alerts data
- `MOCK_NWS_WEATHER` - Mock NWS weather data
- `get_ca_alerts()` - California alerts mock
- `get_ca_forecast()` - California forecast mock
- `get_no_alerts()` - Empty alerts mock

## Testing Scenarios

1. **California Alerts Test**: Tests that alerts are returned for California
2. **Colorado Forecast Test**: Tests that forecast is returned without alerts for Colorado
3. **Kansas Spraying Test**: Tests that agricultural alerts are checked for Kansas
4. **Pipeline Test**: Tests the complete weather analysis pipeline

## Test Coverage

Tests cover:
- API function calls with valid inputs
- Error handling for invalid inputs
- Data serialization (to_dict, to_json)
- Alert and forecast data processing
- Pipeline integration tests
