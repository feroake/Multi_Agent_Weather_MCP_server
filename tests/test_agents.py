"""
Tests for agents.py - WeatherAgent, PlannerAgent, EvaluatorAgent.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

# Import agent classes and related functions
from agents import (
    WeatherAgent,
    PlannerAgent,
    EvaluatorAgent,
    WeatherReport,
    WeatherPlan,
    EvaluationResult,
    create_weather_agent,
    create_planner_agent,
    create_evaluator_agent,
    run_pipeline,
)

# Import fixtures
from tests.fixtures import (
    SAMPLE_FORECAST_WITH_ALERTS as SAMPLE_FORECAST_DATA,
    SAMPLE_FORECAST_WITHOUT_ALERTS,
    CA_ALERT_FEATURES,
    get_ca_alerts,
    get_ca_forecast,
    get_sample_weather_data_with_alerts,
    get_sample_weather_data_without_alerts,
)

# Mock functions for testing
MOCK_GET_ALERTS = get_ca_alerts(state="CA")
MOCK_GET_FORECAST = get_ca_forecast(lat=34.0522, lon=-118.2437)


class TestWeatherAgent:
    """Tests for WeatherAgent class."""

    @pytest.fixture
    def weather_agent(self):
        """Create WeatherAgent for testing."""
        return WeatherAgent(MOCK_GET_ALERTS, MOCK_GET_FORECAST)

    @pytest.mark.asyncio
    async def test_analyze_with_state(self, weather_agent):
        """Test WeatherAgent analysis with state parameter."""
        result = await weather_agent.analyze(state="CA")

        assert len(result.alerts) == 2
        assert result.state == "CA"
        assert result.latitude is None
        assert result.longitude is None
        assert len(result.forecast) == 0

    @pytest.mark.asyncio
    async def test_analyze_with_lat_lon(self, weather_agent):
        """Test WeatherAgent analysis with latitude/longitude."""
        result = await weather_agent.analyze(latitude=39.7392, longitude=-104.9903)

        assert result.latitude == 39.7392
        assert result.longitude == -104.9903
        assert result.state is None
        assert len(result.alerts) == 0
        assert len(result.forecast) == 1

    @pytest.mark.asyncio
    async def test_analyze_with_both_state_and_lat_lon(self, weather_agent):
        """Test WeatherAgent analysis with both parameters."""
        result = await weather_agent.analyze(
            state="CA",
            latitude=34.0522,
            longitude=-118.2437
        )

        assert result.state == "CA"
        assert result.latitude == 34.0522
        assert result.longitude == -118.2437
        assert len(result.alerts) == 2
        assert len(result.forecast) == 1

    @pytest.mark.asyncio
    async def test_analyze_with_invalid_params(self, weather_agent):
        """Test WeatherAgent analysis with neither state nor lat/lon."""
        with pytest.raises(ValueError):
            await weather_agent.analyze()

    def test_to_dict(self, weather_agent):
        """Test WeatherReport to_dict serialization."""
        result = WeatherReport(
            alerts=[{"id": "test"}],
            forecast={"periods": []},
            state="CA",
        )

        data = result.to_dict()

        assert "alerts" in data
        assert "forecast" in data
        assert "state" in data
        assert isinstance(data["alerts"][0]["id"], str)
        assert data["state"] == "CA"

    def test_weather_report_empty(self):
        """Test WeatherReport with no data."""
        report = WeatherReport()

        assert report.alerts == []
        assert report.forecast == {}
        assert report.state is None
        assert report.latitude is None
        assert report.longitude is None

    @pytest.mark.asyncio
    async def test_weather_report_with_data(self, weather_agent):
        """Test WeatherReport with all data."""
        result = await weather_agent.analyze(state="CA", latitude=34.0522, longitude=-118.2437)

        assert isinstance(result, WeatherReport)
        assert isinstance(result.to_dict(), dict)


class TestPlannerAgent:
    """Tests for PlannerAgent class."""

    @pytest.fixture
    def weather_agent(self):
        """Create WeatherAgent for testing."""
        return WeatherAgent(MOCK_GET_ALERTS, MOCK_GET_FORECAST)

    @pytest.fixture
    def planner_agent(self, weather_agent):
        """Create PlannerAgent for testing."""
        return PlannerAgent(weather_agent)

    @pytest.mark.asyncio
    async def test_plan_with_camping_query(self, planner_agent, weather_agent):
        """Test planning for a camping query."""
        query = "What are the weather conditions for camping in California?"
        weather_report = await weather_agent.analyze(state="CA")

        plan = await planner_agent.plan(query, weather_report)

        assert plan.intent == "outdoor_activity"
        assert "camping" in query.lower()
        assert "outdoor_activity" in plan.intent

    @pytest.mark.asyncio
    async def test_plan_with_travel_query(self, planner_agent, weather_agent):
        """Test planning for a travel query."""
        query = "I'm planning a flight, what's the weather like?"
        weather_report = await weather_agent.analyze(state="CA")

        plan = await planner_agent.plan(query, weather_report)

        assert plan.intent == "travel_inquiry"

    @pytest.mark.asyncio
    async def test_plan_with_spraying_query(self, planner_agent, weather_agent):
        """Test planning for a spraying query."""
        query = "Is it safe to spray crops in Kansas today?"
        weather_report = await weather_agent.analyze(state="KS")

        plan = await planner_agent.plan(query, weather_report)

        assert plan.intent == "agricultural_activity"

    @pytest.mark.asyncio
    async def test_plan_with_general_query(self, planner_agent, weather_agent):
        """Test planning for a general query."""
        query = "What's the weather in Colorado?"
        weather_report = await weather_agent.analyze(state="CO")

        plan = await planner_agent.plan(query, weather_report)

        assert plan.intent == "general_inquiry"

    @pytest.mark.asyncio
    async def test_plan_extracts_location(self, planner_agent, weather_agent):
        """Test that location is extracted from query."""
        query = "What's the weather in CA?"
        weather_report = await weather_agent.analyze(state="CA")

        plan = await planner_agent.plan(query, weather_report)

        assert plan.extracted_info.get("state") == "CA"

    @pytest.mark.asyncio
    async def test_plan_creates_subtasks(self, planner_agent, weather_agent):
        """Test that subtasks are created."""
        query = "I want to hike in Colorado"
        weather_report = await weather_agent.analyze(state="CO")

        plan = await planner_agent.plan(query, weather_report)

        assert len(plan.subtasks) > 0
        assert all(isinstance(task, str) for task in plan.subtasks)

    @pytest.mark.asyncio
    async def test_synthesize_with_alerts(self, planner_agent, weather_agent):
        """Test synthesis with alerts present."""
        query = "What's the weather in California?"
        weather_report = await weather_agent.analyze(state="CA")

        plan = await planner_agent.plan(query, weather_report)
        response = await planner_agent.synthesize(plan)

        assert "alert" in response.lower() or "warning" in response.lower()

    @pytest.mark.asyncio
    async def test_synthesize_with_forecast(self, planner_agent, weather_agent):
        """Test synthesis with forecast data."""
        query = "What's the weather in Colorado?"
        weather_report = await weather_agent.analyze(state="CO", latitude=39.7392, longitude=-104.9903)

        plan = await planner_agent.plan(query, weather_report)
        response = await planner_agent.synthesize(plan)

        # Should include forecast information
        assert "forecast" in response.lower() or "high" in response.lower() or "low" in response.lower()

    @pytest.mark.asyncio
    async def test_synthesize_no_alerts_no_forecast(self, planner_agent, weather_agent):
        """Test synthesis with minimal data."""
        # Create weather report with no alerts and no forecast
        weather_report = WeatherReport()

        query = "Weather in California"
        plan = await planner_agent.plan(query, weather_report)
        response = await planner_agent.synthesize(plan)

        # Response should be minimal
        assert len(response) < 500

    @pytest.mark.asyncio
    async def test_synthesize_recommendations(self, planner_agent, weather_agent):
        """Test that recommendations are generated."""
        query = "I'm camping in California"
        weather_report = await weather_agent.analyze(state="CA")

        plan = await planner_agent.plan(query, weather_report)
        response = await planner_agent.synthesize(plan)

        # Should include recommendations
        assert any(word in response.lower() for word in ["recommend", "consider", "weather looks", "review", "important"])


class TestEvaluatorAgent:
    """Tests for EvaluatorAgent class."""

    @pytest.fixture
    def evaluator_agent(self):
        """Create EvaluatorAgent for testing."""
        return EvaluatorAgent()

    @pytest.mark.asyncio
    async def test_evaluate_pass(self, evaluator_agent, weather_agent):
        """Test evaluation with correct answer."""
        query = "What's the weather in California?"
        weather_report = await weather_agent.analyze(state="CA")

        # Create a correct answer
        correct_answer = "California has 2 active alerts and forecast data available."

        result = await evaluator_agent.evaluate(weather_report, correct_answer)

        assert result.pass_ is True
        assert result.score == 100
        assert len(result.issues_found) == 0

    @pytest.mark.asyncio
    async def test_evaluate_fails_on_hallucination(self, evaluator_agent, weather_agent):
        """Test evaluation detects hallucinated information."""
        query = "What's the weather in California?"
        weather_report = await weather_agent.analyze(state="CA")

        # Create an answer with hallucinated temperature
        hallucinated_answer = (
            "The temperature in California is 150°F and it's extremely hot. "
            "There are no alerts, but the forecast shows perfect skies."
        )

        result = await evaluator_agent.evaluate(weather_report, hallucinated_answer)

        # Should fail due to hallucinations (temperatures don't match)
        assert result.pass_ is False
        assert len(result.issues_found) > 0

    @pytest.mark.asyncio
    async def test_evaluate_fails_on_missing_alerts(self, evaluator_agent, weather_agent):
        """Test evaluation detects missing alerts."""
        query = "What's the weather in California?"
        weather_report = await weather_agent.analyze(state="CA")

        # Create an answer that misses alerts
        answer_without_alerts = (
            "The weather in California looks great. "
            "High of 78°F and clear skies."
        )

        result = await evaluator_agent.evaluate(weather_report, answer_without_alerts)

        # Should fail due to missing alerts
        assert result.pass_ is False
        assert any("alert" in issue.lower() for issue in result.issues_found)

    @pytest.mark.asyncio
    async def test_evaluate_with_no_alerts_data(self, evaluator_agent, weather_agent):
        """Test evaluation when there are no alerts."""
        query = "What's the weather in Colorado?"
        weather_report = await weather_agent.analyze(state="CO", latitude=39.7392, longitude=-104.9903)

        # Ensure no alerts
        assert len(weather_report.alerts) == 0

        answer = "Colorado weather forecast looks good."

        result = await evaluator_agent.evaluate(weather_report, answer)

        # Should pass since there are no alerts to mention
        assert result.pass_ is True
        assert result.score == 100

    @pytest.mark.asyncio
    async def test_evaluation_result_to_dict(self, evaluator_agent, weather_agent):
        """Test EvaluationResult serialization."""
        query = "Weather in California"
        weather_report = await weather_agent.analyze(state="CA")

        answer = "California has 2 alerts."

        result = await evaluator_agent.evaluate(weather_report, answer)

        data = result.to_dict()

        assert "pass" in data
        assert "score" in data
        assert "justification" in data
        assert "weather_data" in data
        assert "final_answer" in data
        assert "issues_found" in data


class TestWeatherReport:
    """Tests for WeatherReport dataclass."""

    def test_init_defaults(self):
        """Test WeatherReport initialization with defaults."""
        report = WeatherReport()

        assert report.alerts == []
        assert report.forecast == {}
        assert report.timestamp is not None
        assert report.state is None
        assert report.latitude is None
        assert report.longitude is None

    def test_init_with_values(self):
        """Test WeatherReport initialization with values."""
        report = WeatherReport(
            alerts=[{"id": "test1"}],
            forecast={"periods": [{"temperature": 70}]},
            state="CA",
            latitude=34.0522,
            longitude=-118.2437,
        )

        assert len(report.alerts) == 1
        assert report.forecast == {"periods": [{"temperature": 70}]}
        assert report.state == "CA"
        assert report.latitude == 34.0522
        assert report.longitude == -118.2437

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all fields."""
        report = WeatherReport(
            alerts=[{"id": "1"}],
            forecast={"periods": [{"temperature": 70}]},
            state="CA",
            latitude=34.0522,
            longitude=-118.2437,
            timestamp=datetime.now(),
        )

        data = report.to_dict()

        assert data["alerts"] == [{"id": "1"}]
        assert data["forecast"] == {"periods": [{"temperature": 70}]}
        assert data["state"] == "CA"
        assert data["latitude"] == 34.0522
        assert data["longitude"] == -118.2437
        assert "timestamp" in data

    def test_to_dict_serialization(self):
        """Test that to_dict returns a JSON-serializable dict."""
        import json

        report = WeatherReport(
            alerts=[{"id": "test"}],
            forecast={"periods": []},
            state="CA",
            latitude=34.0522,
            longitude=-118.2437,
        )

        data = report.to_dict()
        json_str = json.dumps(data)

        assert json_str is not None
        assert isinstance(json_str, str)


class TestWeatherPlan:
    """Tests for WeatherPlan dataclass."""

    def test_init_defaults(self):
        """Test WeatherPlan initialization with defaults."""
        report = WeatherReport()

        plan = WeatherPlan(
            subtasks=[],
            weather_data=report,
            intent="general_inquiry",
            extracted_info={},
        )

        assert plan.subtasks == []
        assert plan.weather_data == report
        assert plan.intent == "general_inquiry"
        assert plan.extracted_info == {}

    def test_to_dict(self):
        """Test WeatherPlan serialization."""
        report = WeatherReport(
            alerts=[{"id": "1"}],
            forecast={"periods": []},
            state="CA",
        )

        plan = WeatherPlan(
            subtasks=["Task 1", "Task 2"],
            weather_data=report,
            intent="outdoor_activity",
            extracted_info={"state": "CA"},
        )

        data = plan.to_dict()

        assert data["subtasks"] == ["Task 1", "Task 2"]
        assert data["intent"] == "outdoor_activity"
        assert data["extracted_info"] == {"state": "CA"}
        assert data["weather_data"]["state"] == "CA"

    @pytest.mark.asyncio
    async def test_init_with_all_values(self, weather_agent):
        """Test WeatherPlan initialization with all values."""
        import asyncio

        weather_report = await weather_agent.analyze(
            state="CA",
            latitude=34.0522,
            longitude=-118.2437,
        )

        plan = WeatherPlan(
            subtasks=["Get alerts", "Get forecast", "Synthesize"],
            weather_data=weather_report,
            intent="outdoor_activity",
            extracted_info={"activity": "camping"},
        )

        data = plan.to_dict()
        assert data["subtasks"] == ["Get alerts", "Get forecast", "Synthesize"]


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_init_defaults(self):
        """Test EvaluationResult initialization with defaults."""
        result = EvaluationResult(
            pass_=True,
            score=100,
            justification="All checks passed",
            weather_data=WeatherReport(),
            final_answer="Test answer",
            issues_found=[],
        )

        assert result.pass_ is True
        assert result.score == 100
        assert result.justification == "All checks passed"
        assert result.issues_found == []

    def test_to_dict(self):
        """Test EvaluationResult serialization."""
        result = EvaluationResult(
            pass_=False,
            score=70,
            justification="Missing alerts",
            weather_data=WeatherReport(),
            final_answer="Test answer",
            issues_found=["Missing alerts", "Missing forecast"],
        )

        data = result.to_dict()

        assert data["pass"] is False
        assert data["score"] == 70
        assert data["justification"] == "Missing alerts"
        assert data["issues_found"] == ["Missing alerts", "Missing forecast"]

    def test_init_with_pass_false(self):
        """Test EvaluationResult with pass=False."""
        result = EvaluationResult(
            pass_=False,
            score=50,
            justification="Hallucinated temperature",
            weather_data=WeatherReport(),
            final_answer="Answer",
            issues_found=["Temperature hallucination"],
        )

        assert result.pass_ is False
        assert result.score == 50
