from langchain_core.tools import BaseTool
import requests

class GetCoordinatesTool(BaseTool):
    name: str = "get_coordinates"
    description: str = (
        "Get coordinates (latitude and longitude) from specified place name."
        "For example, query 'Chinese Garden', return 'The coordinates of Chinese Garden is: latitude 1.3423978; longitude 103.7325440.'"
    )

    def _run(self, location: str):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "countrycodes": "SG",
        }
        headers = {"User-Agent": "LangGraphGeoBot/1.0"}
        resp = requests.get(url, params=params, headers=headers)

        if resp.status_code != 200:
            return f"Request Failed: API return code {resp.status_code}."

        data = resp.json()
        if not data:
            return f"Request Failed: Cannot find the coordinates of '{location}'."

        lat, lon = data[0]["lat"], data[0]["lon"]
        return f"The coordinates of {location} is: latitude {lat}; longitude {lon}."

