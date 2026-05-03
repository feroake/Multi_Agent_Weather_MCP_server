"""
Pytest configuration and fixtures for Weather MCP Server tests.
"""

from __future__ import annotations

from typing import Any

from datetime import datetime, timezone

import pytest

# Mock NWS alerts data
MOCK_NWS_ALERTS: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "id": "1-013-0006-241008153",
                "event": "Red Flag Warning",
                "headline": "Red Flag Warning issued October 10 at 8:11AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
                "description": "THE NATIONAL WEATHER SERVICE IN SAN FRANCISCO HAS ISSUED A...",
                "urgency": "expected",
                "severity": "severe",
                "certainty": "likely",
                "onset": "2024-10-10T06:11:00-07:00",
                "expires": "2024-10-11T21:00:00-07:00",
                "sent": "2024-10-10T15:11:00-07:00",
                "areaDesc": "Central Coast",
                "geometry": {
                    "coordinates": [[[-122.56, 36.73], [-122.56, 37.56], [-121.69, 37.56], [-121.69, 36.73], [-122.56, 36.73]]],
                },
            },
        },
        {
            "type": "Feature",
            "properties": {
                "id": "1-013-0006-241008154",
                "event": "Red Flag Warning",
                "headline": "Red Flag Warning issued October 10 at 9:29AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
                "description": "THE NATIONAL WEATHER SERVICE IN SAN FRANCISCO HAS ISSUED A...",
                "urgency": "expected",
                "severity": "severe",
                "certainty": "likely",
                "onset": "2024-10-10T09:29:00-07:00",
                "expires": "2024-10-11T21:00:00-07:00",
                "sent": "2024-10-10T16:29:00-07:00",
                "areaDesc": "Santa Clara",
                "geometry": {
                    "coordinates": [[[-122.02, 36.89], [-122.02, 37.72], [-121.15, 37.72], [-121.15, 36.89], [-122.02, 36.89]]],
                },
            },
        },
    ],
}


# Mock NWS weather data
MOCK_NWS_WEATHER: dict[str, Any] = {
    "properties": {
        "periods": [
            {
                "number": 1,
                "name": "Today",
                "startTime": "2024-10-10T06:00:00-07:00",
                "endTime": "2024-10-11T06:00:00-07:00",
                "isDaytime": 1,
                "icon": "sunny",
                "detailedForecast": "Sunny, with a high near 85.",
                "temperature": 85,
                "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 0},
                "dewpoint": 60,
                "windSpeed": 5,
                "windGust": 10,
            },
        ],
    },
}


# Sample California alert features
CA_ALERT_FEATURES = [
    {
        "type": "Feature",
        "properties": {
            "id": "1-013-0006-241008153",
            "event": "Red Flag Warning",
            "headline": "Red Flag Warning issued October 10 at 8:11AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
            "description": "THE NATIONAL WEATHER SERVICE IN SAN FRANCISCO HAS ISSUED A...",
            "urgency": "expected",
            "severity": "severe",
            "certainty": "likely",
            "onset": "2024-10-10T06:11:00-07:00",
            "expires": "2024-10-11T21:00:00-07:00",
            "sent": "2024-10-10T15:11:00-07:00",
            "areaDesc": "Central Coast",
            "geometry": {
                "coordinates": [[[-122.56, 36.73], [-122.56, 37.56], [-121.69, 37.56], [-121.69, 36.73], [-122.56, 36.73]]],
            },
        },
    },
    {
        "type": "Feature",
        "properties": {
            "id": "1-013-0006-241008154",
            "event": "Red Flag Warning",
            "headline": "Red Flag Warning issued October 10 at 9:29AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
            "description": "THE NATIONAL WEATHER SERVICE IN SAN FRANCISCO HAS ISSUED A...",
            "urgency": "expected",
            "severity": "severe",
            "certainty": "likely",
            "onset": "2024-10-10T09:29:00-07:00",
            "expires": "2024-10-11T21:00:00-07:00",
            "sent": "2024-10-10T16:29:00-07:00",
            "areaDesc": "Santa Clara",
            "geometry": {
                "coordinates": [[[-122.02, 36.89], [-122.02, 37.72], [-121.15, 37.72], [-121.15, 36.89], [-122.02, 36.89]]],
            },
        },
    },
]


# Mock California forecast data
MOCK_NWS_FORECAST_CA: dict[str, Any] = {
    "properties": {
        "periods": [
            {
                "number": 1,
                "name": "Today",
                "startTime": "2024-10-10T06:00:00-07:00",
                "endTime": "2024-10-11T06:00:00-07:00",
                "isDaytime": 1,
                "icon": "f01",
                "detailedForecast": "Sunny, with a high near 85.",
                "temperature": 85,
                "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 0},
                "dewpoint": 60,
                "windSpeed": 5,
                "windGust": 10,
            },
            {
                "number": 2,
                "name": "Tonight",
                "startTime": "2024-10-11T06:00:00-07:00",
                "endTime": "2024-10-12T06:00:00-07:00",
                "isDaytime": 0,
                "icon": "f10",
                "detailedForecast": "Clear, with a low around 60.",
                "temperature": 60,
                "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 0},
                "dewpoint": 55,
                "windSpeed": 3,
                "windGust": 6,
            },
            {
                "number": 3,
                "name": "Tuesday",
                "startTime": "2024-10-12T06:00:00-07:00",
                "endTime": "2024-10-13T06:00:00-07:00",
                "isDaytime": 1,
                "icon": "f01",
                "detailedForecast": "Sunny, with a high near 86.",
                "temperature": 86,
                "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 0},
                "dewpoint": 62,
                "windSpeed": 4,
                "windGust": 8,
            },
        ],
    },
}


# No alerts (empty features)
MOCK_NWS_ALERTS_NO_ALERTS: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [],
}


# Sample Colorado forecast (no alerts)
MOCK_NWS_FORECAST_CO: dict[str, Any] = {
    "properties": {
        "periods": [
            {
                "number": 1,
                "name": "Today",
                "startTime": "2024-10-10T06:00:00-06:00",
                "endTime": "2024-10-11T06:00:00-06:00",
                "isDaytime": 1,
                "icon": "f02",
                "detailedForecast": "Partly cloudy, with a high near 70.",
                "temperature": 70,
                "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 0},
                "dewpoint": 45,
                "windSpeed": 8,
                "windGust": 12,
            },
        ],
    },
}


def parse_iso_format(dt_str: str) -> datetime:
    """Parse ISO format datetime string (with or without timezone)."""
    if dt_str.endswith("Z"):
        # UTC timezone
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    elif "+" in dt_str or dt_str.count("-") > 2:
        # Local timezone
        return datetime.fromisoformat(dt_str)
    else:
        # Assume UTC for strings without timezone
        return datetime.fromisoformat(dt_str)


def get_current_iso() -> str:
    """Get current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def mock_alerts():
    """Fixture to provide mock alerts data."""
    return MOCK_NWS_ALERTS


@pytest.fixture
def mock_weather():
    """Fixture to provide mock weather data."""
    return MOCK_NWS_WEATHER


@pytest.fixture
def mock_alerts_ca():
    """Fixture for California alerts."""
    return MOCK_NWS_ALERTS


@pytest.fixture
def mock_forecast_ca():
    """Fixture for California forecast."""
    return MOCK_NWS_FORECAST_CA


@pytest.fixture
def mock_alerts_no_alerts():
    """Fixture for no alerts."""
    return MOCK_NWS_ALERTS_NO_ALERTS


@pytest.fixture
def mock_forecast_co():
    """Fixture for Colorado forecast (no alerts)."""
    return MOCK_NWS_FORECAST_CO


@pytest.fixture
def mock_current_time():
    """Fixture for current time in ISO format."""
    return get_current_iso()


@pytest.fixture
def mock_parse_iso():
    """Fixture for ISO format parser."""
    return parse_iso_format


@pytest.fixture
def weather_agent(mock_alerts_ca, mock_forecast_ca, mock_alerts_no_alerts, mock_forecast_co):
    """Fixture to create WeatherAgent instance with state-aware mocks."""
    from agents import WeatherAgent

    async def alerts_func(state: str):
        if state.upper() == "CO":
            return mock_alerts_no_alerts
        return mock_alerts_ca

    async def forecast_func(lat: float, lon: float):
        return mock_forecast_ca

    return WeatherAgent(alerts_func, forecast_func)


@pytest.fixture
def evaluator_agent():
    """Fixture to create EvaluatorAgent instance."""
    from agents import EvaluatorAgent
    return EvaluatorAgent()


@pytest.fixture(autouse=True)
def mock_nws_requests(monkeypatch):
    """Mock weather.make_nws_request for all tests that use weather.* orchestration."""
    async def mock_request(url: str) -> dict[str, Any] | None:
        # Alerts endpoint
        if "alerts/active/area" in url:
            state = url.rsplit("/", 1)[-1].upper()
            if state == "CA":
                return MOCK_NWS_ALERTS
            elif state == "KS":
                return {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "id": "1-013-0006-241008160",
                                "event": "Red Flag Warning",
                                "headline": "Red Flag Warning issued by NWS Goodland KS",
                                "description": "Red Flag Warning means conditions are favorable for rapid fire growth.",
                                "severity": "severe",
                                "areaDesc": "Kansas area",
                            },
                        },
                    ],
                }
            elif state in ("CO", "IN"):
                return MOCK_NWS_ALERTS_NO_ALERTS
            else:
                return MOCK_NWS_ALERTS_NO_ALERTS

        # Points endpoint (metadata → forecast URL)
        if "/points/" in url:
            return {
                "properties": {
                    "forecast": "https://api.weather.gov/gridpoints/TEST/1,1/forecast",
                },
            }

        # Forecast endpoint
        if "forecast" in url:
            # Determine state from context — default to CA forecast
            return MOCK_NWS_FORECAST_CA

        return None

    import weather
    monkeypatch.setattr(weather, "make_nws_request", mock_request)
