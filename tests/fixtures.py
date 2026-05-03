"""
Fixtures for testing - provides mock weather data for tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Mock alert features for California
CA_ALERT_FEATURES = [
    {
        "id": "1-013-0006-241008153",
        "event": "Red Flag Warning",
        "headline": "Red Flag Warning issued October 10 at 8:11AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
        "urgency": "expected",
        "severity": "severe",
        "certainty": "likely",
        "onset": "2024-10-10T06:11:00-07:00",
        "expires": "2024-10-11T21:00:00-07:00",
        "description": "Red Flag Warning means that conditions are favorable for rapid fire growth.",
        "instruction": "Be ready to take shelter from fire and smoke.",
    },
    {
        "id": "1-013-0006-241008154",
        "event": "Red Flag Warning",
        "headline": "Red Flag Warning issued October 10 at 9:29AM PDT until October 11 at 6:00PM PDT by NWS San Francisco CA",
        "urgency": "expected",
        "severity": "severe",
        "certainty": "likely",
        "onset": "2024-10-10T09:29:00-07:00",
        "expires": "2024-10-11T21:00:00-07:00",
        "description": "Red Flag Warning means that conditions are favorable for rapid fire growth.",
        "instruction": "Be ready to take shelter from fire and smoke.",
    },
]

# Mock forecast data for California
CA_FORECAST_FEATURES = {
    "periods": [
        {
            "number": 1,
            "name": "Today",
            "startTime": "2024-10-10T06:00:00-07:00",
            "endTime": "2024-10-11T06:00:00-07:00",
            "isDaytime": 1,
            "icon": "f01",
            "detailedForecast": "Sunny, with a high near 85. Low around 60. West wind around 15 mph.",
            "temperature": 85,
            "temperatureUnit": "F",
            "probabilityOfPrecipitation": {"value": 0},
            "dewpoint": 60,
            "windSpeed": 15,
            "windGust": 25,
        },
        {
            "number": 2,
            "name": "Tonight",
            "startTime": "2024-10-11T06:00:00-07:00",
            "endTime": "2024-10-12T06:00:00-07:00",
            "isDaytime": 0,
            "icon": "f10",
            "detailedForecast": "Sunny, with a low around 60. West wind around 10 mph.",
            "temperature": 60,
            "temperatureUnit": "F",
            "probabilityOfPrecipitation": {"value": 0},
            "dewpoint": 55,
            "windSpeed": 10,
            "windGust": 15,
        },
    ],
}

# Mock alert features for Kansas (agricultural)
KS_ALERT_FEATURES = [
    {
        "id": "1-013-0006-241008160",
        "event": "Red Flag Warning",
        "headline": "Red Flag Warning issued October 10 at 8:11AM CDT until October 11 at 6:00PM CDT by NWS Goodland KS",
        "urgency": "expected",
        "severity": "severe",
        "certainty": "likely",
        "onset": "2024-10-10T06:11:00-05:00",
        "expires": "2024-10-11T21:00:00-05:00",
        "description": "Red Flag Warning means that conditions are favorable for rapid fire growth.",
        "instruction": "Be ready to take shelter from fire and smoke.",
    },
]

# Mock forecast data for Kansas
KS_FORECAST_FEATURES = {
    "periods": [
        {
            "number": 1,
            "name": "Today",
            "startTime": "2024-10-10T06:00:00-05:00",
            "endTime": "2024-10-11T06:00:00-05:00",
            "isDaytime": 1,
            "icon": "f10",
            "detailedForecast": "Sunny, with a high near 75.",
            "temperature": 75,
            "temperatureUnit": "F",
            "probabilityOfPrecipitation": {"value": 0},
            "dewpoint": 55,
            "windSpeed": 10,
            "windGust": 20,
        },
    ],
}

# Sample weather data without alerts
SAMPLE_FORECAST_WITHOUT_ALERTS = {
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
        ],
    },
}

# Sample weather data with alerts
SAMPLE_FORECAST_WITH_ALERTS = {
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
                "windSpeed": 15,
                "windGust": 25,
            },
        ],
    },
}


# Default alerts
DEFAULT_ALERTS = {
    "type": "FeatureCollection",
    "features": CA_ALERT_FEATURES,
}


# Default no alerts
DEFAULT_NO_ALERTS = {
    "type": "FeatureCollection",
    "features": [],
}


# Default forecast
DEFAULT_FORECAST = {
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
        ],
    },
}


def get_ca_alerts(state: str):
    """Return California alerts."""
    return DEFAULT_ALERTS


def get_ca_forecast(lat: float, lon: float):
    """Return California forecast."""
    return SAMPLE_FORECAST_WITH_ALERTS


def get_kansas_alerts():
    """Return Kansas alerts."""
    return {
        "type": "FeatureCollection",
        "features": KS_ALERT_FEATURES,
    }


def get_kansas_forecast():
    """Return Kansas forecast."""
    return SAMPLE_FORECAST_WITH_ALERTS


def get_co_alerts():
    """Return Colorado alerts (typically none)."""
    return DEFAULT_NO_ALERTS


def get_co_forecast():
    """Return Colorado forecast."""
    return SAMPLE_FORECAST_WITHOUT_ALERTS


def get_sample_weather_data_with_alerts():
    """Return sample weather data with alerts."""
    return {
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
                    "windSpeed": 15,
                    "windGust": 25,
                },
            ],
        },
    }


def get_sample_weather_data_without_alerts():
    """Return sample weather data without alerts."""
    return {
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
            ],
        },
    }


# Default mock data for all states
MOCK_ALERTS = DEFAULT_ALERTS
MOCK_FORECAST = SAMPLE_FORECAST_WITH_ALERTS
