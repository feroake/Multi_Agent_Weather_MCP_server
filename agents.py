"""
Multi-Agent Pipeline for Weather MCP Server

This module implements three agent classes for orchestrating weather-related tasks:
1. WeatherAgent - Fetches alerts and forecasts using MCP tools
2. PlannerAgent - Breaks user requests into subtasks and synthesizes answers
3. EvaluatorAgent - Reviews output for factual consistency
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

# Configure logging for agent traceability
logger = logging.getLogger("weather.agents")


@dataclass
class WeatherReport:
    """Structured weather data returned by WeatherAgent."""
    alerts: list[dict[str, Any]] = field(default_factory=list)
    forecast: dict[str, Any] = field(default_factory=dict)
    alerts_data: dict[str, Any] | None = None
    forecast_data: dict[str, Any] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "alerts": self.alerts,
            "forecast": self.forecast,
            "alerts_data": self.alerts_data,
            "forecast_data": self.forecast_data,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass
class WeatherPlan:
    """Plan created by PlannerAgent."""
    subtasks: list[str]
    weather_data: WeatherReport
    intent: str
    extracted_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subtasks": self.subtasks,
            "weather_data": self.weather_data.to_dict(),
            "intent": self.intent,
            "extracted_info": self.extracted_info,
        }


@dataclass
class EvaluationResult:
    """Evaluation result from EvaluatorAgent."""
    pass_: bool  # Pass or fail
    score: int  # 0-100 confidence score
    justification: str
    weather_data: WeatherReport
    final_answer: str
    issues_found: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pass": self.pass_,
            "score": self.score,
            "justification": self.justification,
            "weather_data": self.weather_data.to_dict(),
            "final_answer": self.final_answer,
            "issues_found": self.issues_found,
        }


class WeatherAgent:
    """
    Weather Agent - Fetches weather data using MCP tools.

    Leverages the existing get_alerts and get_forecast MCP tools
    to collect weather information for a given location.
    """

    def __init__(self, get_alerts_func, get_forecast_func):
        """
        Initialize WeatherAgent with MCP tool functions or pre-fetched data.

        Args:
            get_alerts_func: Function to get weather alerts for a state, or dict with pre-fetched alerts
            get_forecast_func: Function to get forecast for lat/lon, or dict with pre-fetched forecast
        """
        # Handle pre-fetched dict responses - wrap in async callables
        if callable(get_alerts_func):
            self._get_alerts = get_alerts_func
        elif isinstance(get_alerts_func, dict):
            async def _alerts_wrapper(state, _data=get_alerts_func):
                return _data
            self._get_alerts = _alerts_wrapper
        else:
            self._get_alerts = get_alerts_func

        if callable(get_forecast_func):
            self._get_forecast = get_forecast_func
        elif isinstance(get_forecast_func, dict):
            async def _forecast_wrapper(lat, lon, _data=get_forecast_func):
                return _data
            self._get_forecast = _forecast_wrapper
        else:
            self._get_forecast = get_forecast_func

        logger.debug("WeatherAgent initialized")

    async def analyze(
        self,
        state: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        date: datetime | None = None,
    ) -> WeatherReport:
        """
        Analyze weather conditions for a location.

        Args:
            state: Two-letter US state code (e.g., "CA", "NY")
            latitude: Latitude of location
            longitude: Longitude of location
            date: Optional date for forecast (defaults to current day)

        Returns:
            WeatherReport containing alerts and forecast data
        """
        if state is None and (latitude is None or longitude is None):
            raise ValueError("Either state (for alerts) or lat/lon (for forecast) must be provided")

        weather_data = WeatherReport()

        # Fetch alerts if state is provided
        if state:
            logger.info(f"WeatherAgent: Fetching alerts for state={state}")
            try:
                alerts_raw = await self._get_alerts(state)
                weather_data.alerts_data = alerts_raw if isinstance(alerts_raw, dict) else None
                if isinstance(alerts_raw, dict) and "features" in alerts_raw:
                    weather_data.alerts = alerts_raw["features"]
                    logger.info(f"WeatherAgent: Found {len(alerts_raw['features'])} alerts for {state}")
                elif alerts_raw and isinstance(alerts_raw, list):
                    weather_data.alerts = alerts_raw
                    weather_data.alerts_data = {"features": alerts_raw}
                    logger.info(f"WeatherAgent: Found {len(alerts_raw)} alerts for {state}")
                else:
                    logger.info(f"WeatherAgent: No alerts found for {state}")
            except Exception as e:
                logger.warning(f"WeatherAgent: Failed to fetch alerts for {state}: {e}")

        # Fetch forecast if lat/lon is provided
        if latitude is not None and longitude is not None:
            logger.info(f"WeatherAgent: Fetching forecast for lat={latitude}, lon={longitude}")
            try:
                forecast_raw = await self._get_forecast(latitude, longitude)
                if forecast_raw:
                    weather_data.forecast_data = forecast_raw if isinstance(forecast_raw, dict) else None
                    if isinstance(forecast_raw, dict) and "properties" in forecast_raw:
                        weather_data.forecast = forecast_raw["properties"]
                        logger.info(f"WeatherAgent: Received forecast data with {len(forecast_raw['properties'].get('periods', []))} periods")
                    else:
                        weather_data.forecast = forecast_raw
                        logger.info(f"WeatherAgent: Received forecast data")
                else:
                    logger.warning(f"WeatherAgent: No forecast data available for {latitude}, {longitude}")
            except Exception as e:
                logger.warning(f"WeatherAgent: Failed to fetch forecast for {latitude}, {longitude}: {e}")

        weather_data.state = state
        weather_data.latitude = latitude
        weather_data.longitude = longitude

        logger.info(f"WeatherAgent: Analysis complete. Alerts: {len(weather_data.alerts)}, Forecast: {bool(weather_data.forecast)}")
        return weather_data


class PlannerAgent:
    """
    Planner Agent - Breaks user requests into subtasks and creates activity plans.

    Extracts location, date, and intent from user queries, then orchestrates
    weather data collection and synthesizes natural language responses.
    """

    def __init__(self, weather_agent: WeatherAgent):
        """
        Initialize PlannerAgent with a WeatherAgent instance.

        Args:
            weather_agent: WeatherAgent instance to use for data fetching
        """
        self.weather_agent = weather_agent
        logger.info(f"PlannerAgent initialized with WeatherAgent")

    async def plan(self, query: str, weather_report: WeatherReport) -> WeatherPlan:
        """
        Create a plan to fulfill a user request.

        Args:
            query: User's natural language query
            weather_report: Weather data from WeatherAgent

        Returns:
            WeatherPlan containing subtasks and extracted information
        """
        logger.info(f"PlannerAgent: Processing query: {query}")

        # Extract information from query
        extracted_info = self._extract_info(query)
        logger.debug(f"PlannerAgent: Extracted info: {extracted_info}")

        # Create subtasks based on intent
        subtasks = self._create_subtasks(query, weather_report, extracted_info)
        logger.debug(f"PlannerAgent: Created {len(subtasks)} subtasks")

        plan = WeatherPlan(
            subtasks=subtasks,
            weather_data=weather_report,
            intent=self._classify_intent(query),
            extracted_info=extracted_info,
        )

        logger.info(f"PlannerAgent: Plan created with intent: {plan.intent}")
        return plan

    async def synthesize(self, plan: WeatherPlan) -> str:
        """
        Synthesize a human-readable response from a plan.

        Args:
            plan: WeatherPlan with weather data and subtasks

        Returns:
            Human-readable weather response
        """
        logger.info("PlannerAgent: Synthesizing response")

        response_parts = []

        # Header based on intent
        if plan.intent == "outdoor_activity":
            response_parts.append("## Weather Assessment for Your Trip")
            response_parts.append("")
            response_parts.append(f"Based on the {', '.join(plan.subtasks)}")
        elif plan.intent == "general_inquiry":
            response_parts.append("## Weather Information")
            response_parts.append("")
        else:
            response_parts.append("## Weather Update")
            response_parts.append("")

        # Add location info
        if plan.weather_data.state:
            response_parts.append(f"**Location**: {plan.weather_data.state}")
        if plan.weather_data.latitude and plan.weather_data.longitude:
            response_parts.append(f"**Coordinates**: {plan.weather_data.latitude}, {plan.weather_data.longitude}")

        # Add alerts if present
        if plan.weather_data.alerts:
            response_parts.append("")
            response_parts.append("## ⚠️ Active Alerts")
            for alert in plan.weather_data.alerts:
                props = alert.get("properties", {})
                event = props.get("event", "Unknown")
                area = props.get("areaDesc", "Unknown")
                severity = props.get("severity", "Unknown")
                response_parts.append(f"- {event} in {area} (Severity: {severity})")
                if "description" in props:
                    response_parts.append(f"  {props['description']}")

        # Add forecast if present
        if plan.weather_data.forecast:
            response_parts.append("")
            response_parts.append("## Forecast")
            periods = plan.weather_data.forecast.get("properties", {}).get("periods", [])
            for period in periods[:5]:  # Limit to first 5 periods
                name = period.get("name", "Period")
                temp = period.get("temperature", "Unknown")
                wind = period.get("windSpeed", "Unknown")
                forecast = period.get("detailedForecast", "No forecast available")
                response_parts.append(f"- {name}: {temp}°, Wind: {wind}, {forecast}")

        # Add recommendations
        if plan.intent == "outdoor_activity":
            response_parts.extend(self._generate_recommendations(plan.weather_data))

        return "\n\n".join(response_parts)

    def _extract_info(self, query: str) -> dict[str, Any]:
        """
        Extract relevant information from user query.

        Args:
            query: User's natural language query

        Returns:
            Dictionary with extracted information
        """
        import re

        info = {}

        # Extract location (state)
        state_match = re.search(r'(?:in |for|at)\s*(\w{2})\b', query, re.IGNORECASE)
        if state_match:
            info["state"] = state_match.group(1).upper()
        else:
            # Try to infer from location name
            location_match = re.search(r'(\w+(?:\s+\w+)?)\s+(?:national\s+park|state\s+park|area)', query, re.IGNORECASE)
            if location_match:
                info["location_name"] = location_match.group(1)

        # Extract date
        date_match = re.search(r'(next\s+\w+|this\s+\w+|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', query, re.IGNORECASE)
        if date_match:
            info["date"] = date_match.group(1)

        # Extract activity type
        activity_keywords = ["camping", "hiking", "travel", "flight", "spraying", "farming"]
        for keyword in activity_keywords:
            if keyword in query.lower():
                info["activity"] = keyword
                break

        return info

    def _create_subtasks(
        self,
        query: str,
        weather_report: WeatherReport,
        extracted_info: dict[str, Any]
    ) -> list[str]:
        """
        Create subtasks based on query and available weather data.

        Args:
            query: User's original query
            weather_report: Weather data from WeatherAgent
            extracted_info: Information extracted from query

        Returns:
            List of subtask descriptions
        """
        subtasks = []

        if extracted_info.get("state") and weather_report.alerts:
            subtasks.append(f"Check active weather alerts for {extracted_info['state']}")

        if weather_report.forecast:
            subtasks.append("Retrieve current forecast grid data")
        else:
            subtasks.append("Fetch forecast for the provided location")

        if not extracted_info.get("date"):
            subtasks.append("Get forecast for current day")

        # Add intent-based subtasks
        if extracted_info.get("activity") == "spraying":
            subtasks.append("Evaluate weather conditions for crop spraying safety")
        elif extracted_info.get("activity") == "camping" or extracted_info.get("activity") == "hiking":
            subtasks.append("Assess conditions for outdoor activity")
        elif extracted_info.get("activity") == "travel":
            subtasks.append("Check for severe weather affecting travel")

        if not subtasks:
            subtasks.append("Gather comprehensive weather information")

        return subtasks

    def _classify_intent(self, query: str) -> str:
        """
        Classify the user's intent.

        Args:
            query: User's original query

        Returns:
            Intent classification string
        """
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["camping", "hiking", "hike", "camp"]):
            return "outdoor_activity"
        elif any(kw in query_lower for kw in ["flight", "fly", "travel", "drive"]):
            return "travel_inquiry"
        elif any(kw in query_lower for kw in ["spraying", "farm", "crop", "pesticide"]):
            return "agricultural_activity"
        else:
            return "general_inquiry"

    def _generate_recommendations(self, weather_data: WeatherReport) -> list[str]:
        """
        Generate recommendations based on weather data.

        Args:
            weather_data: Weather data from WeatherAgent

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if weather_data.alerts:
            recommendations.append(
                f"**⚠️ Important**: There are {len(weather_data.alerts)} active weather alert(s). "
                "Please review the alerts above before planning your activity."
            )

        if weather_data.forecast:
            periods = weather_data.forecast.get("properties", {}).get("periods", [])
            # Check for severe conditions
            severe_count = sum(
                1 for p in periods[:3]
                if p.get("detailedForecast", "").lower() in
                ["thunderstorms", "severe thunderstorms", "heavy rain", "gusty winds"]
            )
            if severe_count > 0:
                recommendations.append(
                    f"Consider postponing your outdoor activity. "
                    f"Severe weather is expected in {severe_count} of the next {severe_count} periods."
                )
            elif periods and periods[0].get("temperature", 0) < 40:
                recommendations.append(
                    "It's getting chilly - dress in layers and bring warm clothing!"
                )

        if not recommendations:
            recommendations.append("Weather looks reasonable for your planned activity.")

        return recommendations


class EvaluatorAgent:
    """
    Evaluator Agent - Reviews Planner output for factual consistency.

    Checks that the final answer:
    - Includes all relevant weather data
    - Contains no hallucinated information
    - Is factually consistent with raw weather data
    """

    def __init__(self):
        logger.info("EvaluatorAgent initialized")

    async def evaluate(
        self,
        weather_report: WeatherReport,
        final_answer: str,
    ) -> EvaluationResult:
        """
        Evaluate the Planner's output for factual consistency.

        Args:
            weather_report: Original weather data from WeatherAgent
            final_answer: Planner's synthesized response

        Returns:
            EvaluationResult with pass/fail, score, and justification
        """
        logger.info("EvaluatorAgent: Starting evaluation")

        issues_found: list[str] = []
        issues_found_raw: list[str] = []  # For JSON serialization

        # Check for hallucinations
        hallucinations = self._check_hallucinations(final_answer, weather_report)
        issues_found.extend(hallucinations)
        issues_found_raw.extend(hallucinations)

        # Check for missing critical information
        missing_info = self._check_missing_info(final_answer, weather_report)
        issues_found.extend(missing_info)
        issues_found_raw.extend(missing_info)

        # Check for contradictory statements
        contradictions = self._check_contradictions(final_answer, weather_report)
        issues_found.extend(contradictions)
        issues_found_raw.extend(contradictions)

        # Calculate score and generate justification
        score, justification = self._calculate_score_and_justification(
            weather_report, final_answer, issues_found_raw
        )

        pass_ = len(issues_found) == 0  # Pass only if no issues

        result = EvaluationResult(
            pass_=pass_,
            score=score,
            justification=justification,
            weather_data=weather_report,
            final_answer=final_answer,
            issues_found=issues_found_raw,
        )

        logger.info(
            f"EvaluatorAgent: Evaluation complete. "
            f"Pass: {pass_}, Score: {score}, Issues: {len(issues_found)}"
        )
        return result

    def _check_hallucinations(
        self,
        final_answer: str,
        weather_report: WeatherReport,
    ) -> list[str]:
        """
        Check for hallucinated information in the final answer.

        Args:
            final_answer: Planner's response
            weather_report: Original weather data

        Returns:
            List of hallucination issues found
        """
        issues: list[str] = []

        # Check for invented temperature values
        import re
        temp_pattern = r"([+-]?\d+\.?\d*)°"
        found_temps_in_answer = re.findall(temp_pattern, final_answer)

        if found_temps_in_answer and not weather_report.forecast:
            issues.append("Answer contains specific temperature values but no forecast data was available")
        elif found_temps_in_answer:
            # Check if temperatures match the actual forecast
            actual_temps = []
            periods = weather_report.forecast.get("properties", {}).get("periods", [])
            for period in periods:
                temp = period.get("temperature")
                if temp is not None:
                    actual_temps.append(temp)

            answer_temps = [float(t) for t in found_temps_in_answer]
            if answer_temps != actual_temps[:len(answer_temps)]:
                issues.append("Temperature values in answer do not match available forecast data")

        # Check for invented alert details
        if not weather_report.alerts and "alert" in final_answer.lower() or "warning" in final_answer.lower():
            issues.append("Answer mentions alerts or warnings when none are available")

        # Check for invented location names
        location_keywords = ["grand canyon", "denver", "los angeles", "new york"]
        actual_state = weather_report.state
        for keyword in location_keywords:
            if keyword in final_answer.lower() and actual_state is None:
                issues.append(f"Answer references '{keyword}' but no state was specified in the original query")
                break

        return issues

    def _check_missing_info(
        self,
        final_answer: str,
        weather_report: WeatherReport,
    ) -> list[str]:
        """
        Check for missing critical information in the final answer.

        Args:
            final_answer: Planner's response
            weather_report: Original weather data

        Returns:
            List of missing information issues found
        """
        issues: list[str] = []

        # If there are alerts, they should be mentioned
        if weather_report.alerts and "alert" not in final_answer.lower() and "warning" not in final_answer.lower():
            issues.append("Active weather alerts were not mentioned in the answer")

        # If forecast is available, some forecast info should be present
        if weather_report.forecast and "forecast" not in final_answer.lower():
            issues.append("Available forecast data was not included in the answer")

        return issues

    def _check_contradictions(
        self,
        final_answer: str,
        weather_report: WeatherReport,
    ) -> list[str]:
        """
        Check for contradictory statements in the final answer.

        Args:
            final_answer: Planner's response
            weather_report: Original weather data

        Returns:
            List of contradiction issues found
        """
        issues: list[str] = []

        # Check for contradictory conditions
        # e.g., saying "no alerts" when alerts exist
        if weather_report.alerts:
            if "no alerts" in final_answer.lower() or "clear skies" in final_answer.lower():
                # Double check - might be referring to specific conditions
                import re
                alerts_mentioned = len(re.findall(r"alert|warning|storm", final_answer, re.IGNORECASE))
                if alerts_mentioned == 0:
                    issues.append("Answer claims no alerts/severe conditions when alerts are present")

        return issues

    def _calculate_score_and_justification(
        self,
        weather_report: WeatherReport,
        final_answer: str,
        issues_found: list[str],
    ) -> tuple[int, str]:
        """
        Calculate confidence score and justification.

        Args:
            weather_report: Original weather data
            final_answer: Planner's response
            issues_found: List of issues found

        Returns:
            Tuple of (score, justification)
        """
        # Base score
        score = 100

        # Deduct points per issue
        severity_map = {
            "hallucination": 30,  # Invented information is serious
            "missing_info": 10,   # Missing info is less critical
            "contradiction": 20,  # Contradictions are problematic
        }

        for issue in issues_found:
            if "invented" in issue.lower() or "fake" in issue.lower():
                score -= 30
            elif "alert" in issue.lower() or "warning" in issue.lower():
                score -= 25
            elif "temperature" in issue.lower():
                score -= 20
            elif "contradiction" in issue.lower():
                score -= 25
            else:
                score -= 10

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Generate justification
        if not issues_found:
            justification = (
                "The answer is factually consistent with the weather data. "
                "No hallucinations, missing information, or contradictions detected."
            )
        else:
            justification_parts = [
                "The answer has the following issues:"
            ]

            if any("invented" in i.lower() for i in issues_found):
                justification_parts.append("- Contains hallucinated or invented information")

            if any("alert" in i.lower() for i in issues_found):
                justification_parts.append("- Fails to mention relevant weather alerts")

            if any("temperature" in i.lower() for i in issues_found):
                justification_parts.append("- Contains incorrect temperature values")

            if any("missing" in i.lower() for i in issues_found):
                justification_parts.append("- Does not include available weather data")

            justification_parts.append(
                f"Confidence score: {score}/100 based on {len(issues_found)} issue(s) found."
            )
            justification = " ".join(justification_parts)

        return score, justification


# Factory functions for convenience

def create_weather_agent(get_alerts_func, get_forecast_func) -> WeatherAgent:
    """Create a WeatherAgent instance."""
    return WeatherAgent(get_alerts_func, get_forecast_func)


def create_planner_agent(weather_agent: WeatherAgent) -> PlannerAgent:
    """Create a PlannerAgent instance."""
    return PlannerAgent(weather_agent)


def create_evaluator_agent() -> EvaluatorAgent:
    """Create an EvaluatorAgent instance."""
    return EvaluatorAgent()


async def run_pipeline(
    query: str,
    state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Run the full multi-agent pipeline.

    Args:
        query: User's natural language query
        state: Two-letter US state code (for alerts)
        latitude: Latitude of location (for forecast)
        longitude: Longitude of location (for forecast)

    Returns:
        Tuple of (planner's final answer, evaluation result dict)

    Note: This function requires the weather module to be imported to access
    the MCP tool functions. See weather.py for usage.
    """
    from weather import get_alerts, get_forecast

    # Create agents
    weather_agent = create_weather_agent(get_alerts, get_forecast)
    planner_agent = create_planner_agent(weather_agent)
    evaluator_agent = create_evaluator_agent()

    # Run pipeline
    logger.info(f"Running pipeline for query: {query}")

    # Step 1: WeatherAgent
    weather_report = await weather_agent.analyze(
        state=state,
        latitude=latitude,
        longitude=longitude,
    )
    logger.debug(f"WeatherAgent complete. Alerts: {len(weather_report.alerts)}, Forecast: {bool(weather_report.forecast)}")

    # Step 2: PlannerAgent
    plan = await planner_agent.plan(query, weather_report)
    final_answer = await planner_agent.synthesize(plan)
    logger.debug(f"PlannerAgent complete. Answer length: {len(final_answer)}")

    # Step 3: EvaluatorAgent
    evaluation = await evaluator_agent.evaluate(weather_report, final_answer)
    logger.debug(f"EvaluatorAgent complete. Pass: {evaluation.pass_}, Score: {evaluation.score}")

    return final_answer, evaluation.to_dict()
