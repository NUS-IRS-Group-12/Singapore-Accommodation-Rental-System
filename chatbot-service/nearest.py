from typing import Type, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from geopy.distance import geodesic
import requests

class FindNearestPlaceInput(BaseModel):
    latitude: float = Field(..., description="latitude")
    longitude: float = Field(..., description="longitude")
    place_type: Literal[
        # Just amenity
        "hospital",
        "clinic",
        "dentist",
        "pharmacy",
        "cafe",
        "bar",
        "nightclub",
        "cinema",
        "post_box",
        "post_depot",
        "post_office",
        "mailroom",
        "fuel",
        "library",
        "bus_station",
        "car_wash",
        "bank",
        "marketplace",
        "fast_food",
        "restaurant",
        # We have to process differently
        "subway", # station:subway
        "MRT", # station:subway # Why AI doesn't know MRT is subway sometimes
        "bus_stop", # highway:bus_stop
        # Beliefs
        "mosque", # amenity:place_of_worship,religion=muslim
        "church", # amenity:place_of_worship,religion=christian
        "temple", # amenity:place_of_worship,religion=buddhist
        # shop
        "shop", # shop:convenience
        "supermarket", # shop:supermarket
        "furniture store", # shop:furniture
    ] = Field(..., description=(
        "Type of the nearest place to look for."
        "Please try to select the word that is closest to the user input, rather than fill in the unsupported word or reject the user."
        "For example, 'fast food restaurant' is closer to 'fast food' than 'restaurant'."
        "There may be potential type information in the user's input, such as '711' suggests this is a shop while 'KFC' suggests this is a fast food restaurant."
        "Filling in unsupported word, or leaving it blank is strictly prohibited."
    ))
    place_name: str = Field(..., description=(
        "Brand name or other restrictive noun, such as FairPrice, IKEA and halal."
        "Please fill in the complete official English name, for example, 711 should be 'Seven Eleven'."
        "If the user does not give an obvious name or restrictive noun, fill in a blank string here directly."
    ))

def translate_type(place_type):
    match place_type:
        case "subway":
            return "[station=subway]"
        case "MRT":
            return "[station=subway]"
        case "bus_stop":
            return "[highway=bus_stop]"
        case "mosque":
            return "[amenity=place_of_worship][religion=muslim]"
        case "church":
            return "[amenity=place_of_worship][religion=christian]"
        case "temple":
            return "[amenity=place_of_worship][religion=buddhist]"
        case "shop":
            return "[shop=convenience]"
        case "supermarket":
            return "[shop=supermarket]"
        case "furniture store":
            return "[shop=furniture]"
        case _:
            return f"[amenity={place_type}]"

def translate_name(place_name):
    if place_name != "":
        return f"[name~'{place_name}', i]"
    else:
        return ""

class FindNearestPlaceTool(BaseTool):
    name: str = "find_nearest_place"
    description: str = "Find the nearest designated place of locations (hospitals, subways, cafes, etc) near the specified coordinate (latitude and longitude)"
    args_schema: Type[BaseModel] = FindNearestPlaceInput

    def _run(self, latitude: float, longitude: float, place_type: str, place_name: str):
        overpass_url = "https://overpass-api.de/api/interpreter"

        query = f"""
        [out:json];
        node(around:5000,{latitude},{longitude}){translate_type(place_type)}{translate_name(place_name)};
        out center;
        """
        resp = requests.get(overpass_url, params={"data": query})
        data = resp.json()

        if not data["elements"]:
            return f"No {place_type} is found within 5 kilometer range."

        min_node = min(
            data["elements"],
            key=lambda e: geodesic(
                (latitude, longitude),
                (e["lat"], e["lon"])
            ).meters,
        )

        dist = geodesic(
            (latitude, longitude),
            (min_node["lat"], min_node["lon"])
        ).meters

        name = min_node.get("tags", {}).get("name", "unnamed")
        return f"The nearest {place_type} is {name}, with a linear distance of {dist:.0f} meters"

