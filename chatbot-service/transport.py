import requests
from datetime import datetime
from typing import Literal, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class GetTransportTimeInput(BaseModel):
    start_lat: float = Field(..., description="Latitude of starting location")
    start_lon: float = Field(..., description="Longitude of starting location")
    end_lat: float = Field(..., description="Latitude of ending location")
    end_lon: float = Field(..., description="Longitude of ending location")
    transport_type: Literal[
        "public transport",
        "bus",
        "subway",
        "walk",
        "drive",
        "cycle",
    ] = Field(..., description=(
        "The transportation type specified by the user. Just use 'public transport' if the user doesn't specify one."
        "Please try to select the word that is closest to user input, rather than fill in the unsupported word or reject the user."
        "For example, you should always fill in 'drive' when the user specifies '驾车', 'driving' or 'by car'."
    ))

class GetTransportTimeTool(BaseTool):
    name: str = "get_transport_time"
    description: str = (
        "Get estimated transport time between two coordinates (latitude, longitude) in Singapore."
        "Don't ask the user if they haven't specified the transport type. We'll use 'public transport' then."
    )
    args_schema: Type[BaseModel] = GetTransportTimeInput

    _token: str = None

    def _get_token(self) -> str:
        if self._token:
            return self._token

        url = "https://www.onemap.gov.sg/api/auth/post/getToken"
        payload = {
            "email": 'e1553104@u.nus.edu',
            "password": 'kBtqIdcpB33yi4moGnH9qhC5AUv2lo6TtwbjJTm1F8zGTeQxQgkHh98iby'
        }

        resp = requests.post(url, json=payload)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get token: {resp.status_code}, {resp.text}")

        data = resp.json()

        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"Cannot retrieve access token: {data}")

        self._token = token
        return token

    def _run(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, transport_type: str) -> str:
        token = self._get_token()

        url = "https://www.onemap.gov.sg/api/public/routingsvc/route"

        params = {
            "start": f"{start_lat},{start_lon}",
            "end": f"{end_lat},{end_lon}",
            # "routeType": transport_type,
        }

        is_public_transport = True

        if transport_type in ["public transport", "subway", "bus"]:
            params["routeType"] = "pt"

            # TODO: We can adjust it by user input
            now = datetime.now()
            params["date"] = now.strftime("%m-%d-%Y")
            params["time"] = now.strftime("%H:%M:%S")

            match transport_type:
                case "public transport":
                    params["mode"] = "TRANSIT"
                case "subway":
                    params["mode"] = "RAIL"
                case "bus":
                    params["mode"] = "BUS"

        else:
            params["routeType"] = transport_type
            is_public_transport = False


        headers = {"Authorization": token}

        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            return f"Routing API request failed: {resp.status_code}"

        data = resp.json()

        try:
            if is_public_transport:
                duration = min(itinerary["duration"] for itinerary in data["plan"]["itineraries"]) / 60
            else:
                duration = data.get("route_summary").get("total_time") / 60
        except:
            return "Cannot calculate total travel time."

        return f"Estimated {transport_type} time from start to end is {duration:.1f} minutes."
