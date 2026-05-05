import requests

def get_airport_info(icao_code: str) -> dict:
    """
    Fetches real-time METAR weather data for a given airport.
    Uses the free AviationWeather.gov API — no key required.
    """
    url = f"https://aviationweather.gov/api/data/metar?ids={icao_code}&format=json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return {"error": f"No data found for airport {icao_code}"}
        
        metar = data[0]
        
        return {
            "airport": icao_code,
            "temperature_c": metar.get("temp"),
            "wind_speed_kt": metar.get("wspd"),
            "wind_direction": metar.get("wdir"),
            "visibility_miles": metar.get("visib"),
            "conditions": metar.get("wxString", "Clear"),
            "flight_category": metar.get("fltcat", "Unknown"),
            "raw_metar": metar.get("rawOb", "")
        }
    
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. AviationWeather.gov may be unavailable."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch airport data: {str(e)}"}


# OpenAI function definition for function calling (U4)
AIRPORT_INFO_FUNCTION = {
    "type": "function",
    "function": {
        "name": "get_airport_info",
        "description": "Get real-time weather and flight conditions for an airport using its ICAO code. Use this to inform the passenger about current airport conditions that may affect their layover.",
        "parameters": {
            "type": "object",
            "properties": {
                "icao_code": {
                    "type": "string",
                    "description": "The ICAO 4-letter airport code (e.g. KJFK for JFK, KLAX for LAX, KMIA for Miami)"
                }
            },
            "required": ["icao_code"]
        }
    }
}