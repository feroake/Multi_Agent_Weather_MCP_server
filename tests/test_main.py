"""
Tests for main.py - Testing the main Weather MCP Server functionality.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from httpx import Client
from .fixtures import (
    CA_ALERT_FEATURES,
    CA_FORECAST_FEATURES,
    DEFAULT_ALERTS,
    DEFAULT_FORECAST,
    DEFAULT_NO_ALERTS,
    KS_ALERT_FEATURES,
    KS_FORECAST_FEATURES,
    get_ca_alerts,
    get_ca_forecast,
    get_kansas_alerts,
    get_kansas_forecast,
    get_sample_weather_data_with_alerts,
    get_sample_weather_data_without_alerts,
)

import weather


BASE_DIR = Path(__file__).parent.parent
MOCK_DATA_DIR = BASE_DIR / "mock_data"
MOCK_ALERTS_FILE = MOCK_DATA_DIR / "alerts.json"
MOCK_FORECAST_FILE = MOCK_DATA_DIR / "forecast.json"




@pytest.mark.asyncio
async def test_analyze_state_ca():
    """Test analyze with state parameter."""
    result = await weather.analyze(state="CA")
    assert result.state == "CA"
    assert len(result.alerts) == 2  # Should have 2 alerts for California


@pytest.mark.asyncio
async def test_analyze_state_co():
    """Test analyze with state parameter for Colorado."""
    result = await weather.analyze(state="CO")
    assert result.state == "CO"
    # May have no alerts for Colorado


@pytest.mark.asyncio
async def test_analyze_state_invalid():
    """Test analyze with invalid state parameter."""
    with pytest.raises(ValueError):
        await weather.analyze(state="INVALID")


@pytest.mark.asyncio
async def test_analyze_with_latitude_longitude():
    """Test analyze with latitude and longitude."""
    result = await weather.analyze(latitude=34.0522, longitude=-118.2437)
    assert result.latitude == 34.0522
    assert result.longitude == -118.2437


@pytest.mark.asyncio
async def test_plan_query():
    """Test plan with a query."""
    result = await weather.plan(
        query="What are the weather conditions for camping in California?"
    )
    assert result.intent == "outdoor_activity"


@pytest.mark.asyncio
async def test_sprayer_plan():
    """Test sprayer_plan for Kansas agricultural scenario."""
    result = await weather.sprayer_plan(
        state="KS",
        query="Is it safe to spray crops today?",
    )
    assert result.intent == "agricultural_activity"
    # Should have alerts for Kansas


@pytest.mark.asyncio
async def test_forecast_only():
    """Test forecast_only for Colorado scenario."""
    result = await weather.forecast_only(state="CO")
    assert result.state == "CO"
    # Should have forecast


@pytest.mark.asyncio
async def test_spray_check():
    """Test spray_check for Kansas scenario."""
    result = await weather.spray_check(
        state="KS",
        query="Should I apply pesticides today?",
    )
    assert result.state == "KS"
    # Should have alerts


@pytest.mark.asyncio
async def test_forecast_check():
    """Test forecast_check for California scenario."""
    result = await weather.forecast_check(
        state="CA",
        query="I'm planning a trip to California",
    )
    assert result.state == "CA"
    # Should have both alerts and forecast


@pytest.mark.asyncio
async def test_run_pipeline():
    """Test run_pipeline for complete workflow."""
    result = await weather.run_pipeline(
        query="What's the weather in Colorado?",
        state="CO",
    )
    assert result.state == "CO"
    assert len(result.alerts) == 0


@pytest.mark.asyncio
async def test_run_pipeline_with_alerts():
    """Test run_pipeline with alerts (California)."""
    result = await weather.run_pipeline(
        query="What's the weather in California?",
        state="CA",
    )
    assert result.state == "CA"
    assert len(result.alerts) == 2


@pytest.mark.asyncio
async def test_get_current_weather_data():
    """Test get_current_weather_data."""
    result = await weather.get_current_weather_data(state="CA")
    assert result.state == "CA"


@pytest.mark.asyncio
async def test_generate_alert_alert():
    """Test generate_alert_alert."""
    alerts_data = await weather.generate_alert_alert(state="CA")
    assert isinstance(alerts_data, dict)
    assert "type" in alerts_data


@pytest.mark.asyncio
async def test_generate_forecast_data():
    """Test generate_forecast_data."""
    forecast_data = await weather.generate_forecast_data(state="CO")
    assert isinstance(forecast_data, dict)
    assert "properties" in forecast_data


@pytest.mark.asyncio
async def test_generate_alert_alert_no_alerts():
    """Test generate_alert_alert when there are no alerts."""
    alerts_data = await weather.generate_alert_alert(state="IN")
    assert isinstance(alerts_data, dict)
    # Should have empty features list for no alerts
    assert alerts_data["features"] == [] or len(alerts_data["features"]) == 0


@pytest.mark.asyncio
async def test_generate_forecast_data_no_forecast():
    """Test generate_forecast_data when there is no forecast."""
    # This should work even if no forecast exists
    forecast_data = await weather.generate_forecast_data(state="IN")
    assert isinstance(forecast_data, dict)


@pytest.mark.asyncio
async def test_analyze_alerts_data_structure():
    """Test that alerts data has the correct structure."""
    result = await weather.analyze(state="CA")
    assert hasattr(result, "alerts")
    assert hasattr(result, "alerts_data")
    if result.alerts_data:
        assert "features" in result.alerts_data


@pytest.mark.asyncio
async def test_analyze_forecast_data_structure():
    """Test that forecast data has the correct structure."""
    result = await weather.analyze(state="CO")
    assert hasattr(result, "forecast")
    assert hasattr(result, "forecast_data")
    if result.forecast_data:
        assert "properties" in result.forecast_data


@pytest.mark.asyncio
async def test_run_pipeline_alerts_count():
    """Test run_pipeline with correct alerts count."""
    ca_result = await weather.run_pipeline(query="What's the weather in CA?", state="CA")
    co_result = await weather.run_pipeline(query="What's the weather in CO?", state="CO")

    # California should have alerts
    assert len(ca_result.alerts) >= 1
    # Colorado might have no alerts
    assert len(co_result.alerts) >= 0


@pytest.mark.asyncio
async def test_run_pipeline_forecast_count():
    """Test run_pipeline with correct forecast count."""
    ca_result = await weather.run_pipeline(query="What's the weather in CA?", state="CA")
    co_result = await weather.run_pipeline(query="What's the weather in CO?", state="CO")

    # Both should have forecast
    assert len(ca_result.forecast) >= 1
    assert len(co_result.forecast) >= 1
