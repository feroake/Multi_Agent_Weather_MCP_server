from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


# ── Raw data fetchers (return dicts, not formatted strings) ──────────────


async def fetch_alerts_raw(state: str) -> dict[str, Any] | None:
    """Fetch raw alerts data from NWS API (returns GeoJSON dict)."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    return await make_nws_request(url)


async def fetch_forecast_raw(latitude: float, longitude: float) -> dict[str, Any] | None:
    """Fetch raw forecast data from NWS API (returns GeoJSON dict)."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    if not points_data:
        return None
    forecast_url = points_data["properties"]["forecast"]
    return await make_nws_request(forecast_url)


# ── State code validation ─────────────────────────────────────────────────

VALID_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}


def _validate_state(state: str) -> str:
    """Validate and normalize a US state code."""
    upper = state.upper()
    if upper not in VALID_US_STATES:
        raise ValueError(f"Invalid state code: {state}")
    return upper


# Approximate center coordinates for each US state (used when only state is given)
_STATE_COORDS: dict[str, tuple[float, float]] = {
    "AL": (32.8067, -86.7911), "AK": (64.2008, -149.4937),
    "AZ": (33.7298, -111.4312), "AR": (34.9697, -92.3731),
    "CA": (36.1162, -119.6816), "CO": (39.0598, -105.3111),
    "CT": (41.5978, -72.7554), "DE": (39.3185, -75.5071),
    "FL": (27.7663, -81.6868), "GA": (33.0406, -83.6431),
    "HI": (20.2927, -156.3737), "ID": (44.3509, -114.6130),
    "IL": (40.3495, -88.9861), "IN": (39.8494, -86.2583),
    "IA": (42.0115, -93.2105), "KS": (38.5266, -96.7265),
    "KY": (37.6681, -84.6701), "LA": (31.1695, -91.8678),
    "ME": (44.6939, -69.3819), "MD": (39.0639, -76.8021),
    "MA": (42.2302, -71.5301), "MI": (43.3266, -84.5361),
    "MN": (45.6945, -93.9002), "MS": (32.7416, -89.6787),
    "MO": (38.4561, -92.2884), "MT": (46.9219, -110.4544),
    "NE": (41.1254, -98.2681), "NV": (38.3135, -117.0554),
    "NH": (43.4525, -71.5639), "NJ": (40.2989, -74.5210),
    "NM": (34.8405, -106.2485), "NY": (42.1497, -74.9384),
    "NC": (35.6411, -79.8431), "ND": (47.5362, -99.7930),
    "OH": (40.2865, -82.7937), "OK": (35.5889, -97.4943),
    "OR": (43.9336, -120.5583), "PA": (40.8781, -77.7996),
    "RI": (41.5562, -71.5557), "SC": (33.8191, -80.9066),
    "SD": (44.2853, -99.4631), "TN": (35.7478, -86.6923),
    "TX": (31.0545, -97.5635), "UT": (39.3055, -111.6703),
    "VT": (44.0687, -72.6658), "VA": (37.5215, -78.8537),
    "WA": (47.3826, -120.4470), "WV": (38.6409, -80.6227),
    "WI": (44.6243, -89.9941), "WY": (42.9957, -107.5512),
    "DC": (38.8974, -77.0268),
}


def _resolve_coords(state, latitude, longitude):
    """Fill in lat/lon from state if not explicitly provided."""
    if latitude is None and longitude is None and state is not None:
        coords = _STATE_COORDS.get(state.upper())
        if coords:
            return coords[0], coords[1]
    return latitude, longitude


# ── Orchestration functions ───────────────────────────────────────────────


async def analyze(
    state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    """Analyze weather for a location. Returns a WeatherReport."""
    from agents import WeatherAgent

    if state is not None:
        state = _validate_state(state)

    latitude, longitude = _resolve_coords(state, latitude, longitude)

    agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    return await agent.analyze(state=state, latitude=latitude, longitude=longitude)


async def plan(
    query: str,
    state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    """Create a plan from a user query. Returns a WeatherPlan."""
    from agents import WeatherAgent, PlannerAgent, WeatherReport

    if state is not None:
        state = _validate_state(state)

    weather_agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    planner_agent = PlannerAgent(weather_agent)

    try:
        weather_report = await weather_agent.analyze(
            state=state, latitude=latitude, longitude=longitude
        )
    except ValueError:
        weather_report = WeatherReport()

    return await planner_agent.plan(query, weather_report)


async def sprayer_plan(state: str, query: str):
    """Create a plan for agricultural spraying. Returns a WeatherPlan."""
    from agents import WeatherAgent, PlannerAgent

    state = _validate_state(state)
    weather_agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    planner_agent = PlannerAgent(weather_agent)

    weather_report = await weather_agent.analyze(state=state)
    return await planner_agent.plan(query, weather_report)


async def forecast_only(state: str):
    """Get forecast-focused analysis for a state. Returns a WeatherReport."""
    from agents import WeatherAgent

    state = _validate_state(state)
    agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    return await agent.analyze(state=state)


async def spray_check(state: str, query: str):
    """Check spraying conditions for a state. Returns a WeatherReport."""
    from agents import WeatherAgent

    state = _validate_state(state)
    agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    return await agent.analyze(state=state)


async def forecast_check(state: str, query: str):
    """Check forecast for a state. Returns a WeatherReport."""
    from agents import WeatherAgent

    state = _validate_state(state)
    agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    return await agent.analyze(state=state)


async def run_pipeline(
    query: str,
    state: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):
    """Run the full multi-agent pipeline. Returns a WeatherReport."""
    from agents import WeatherAgent, PlannerAgent, EvaluatorAgent

    if state is not None:
        state = _validate_state(state)

    latitude, longitude = _resolve_coords(state, latitude, longitude)

    weather_agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    planner_agent = PlannerAgent(weather_agent)
    evaluator_agent = EvaluatorAgent()

    weather_report = await weather_agent.analyze(
        state=state, latitude=latitude, longitude=longitude
    )
    plan_obj = await planner_agent.plan(query, weather_report)
    final_answer = await planner_agent.synthesize(plan_obj)
    await evaluator_agent.evaluate(weather_report, final_answer)

    return weather_report


async def get_current_weather_data(state: str | None = None):
    """Get current weather data as a WeatherReport."""
    from agents import WeatherAgent

    if state is not None:
        state = _validate_state(state)

    latitude, longitude = _resolve_coords(state, None, None)

    agent = WeatherAgent(fetch_alerts_raw, fetch_forecast_raw)
    return await agent.analyze(state=state, latitude=latitude, longitude=longitude)


async def generate_alert_alert(state: str | None = None):
    """Generate alert data as a GeoJSON dict."""
    if state is not None:
        state = _validate_state(state)

    if state:
        data = await fetch_alerts_raw(state)
        if data:
            return data
    return {"type": "FeatureCollection", "features": []}


async def generate_forecast_data(state: str | None = None):
    """Generate forecast data as a GeoJSON dict."""
    if state is not None:
        state = _validate_state(state)

    if state:
        latitude, longitude = _resolve_coords(state, None, None)
        if latitude is not None and longitude is not None:
            data = await fetch_forecast_raw(latitude, longitude)
            if data:
                return data
    return {"type": "FeatureCollection", "features": []}


def main():
    # Initialize and run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()