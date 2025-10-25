import os
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.tools import tool, ToolRuntime
from langchain_core.callbacks.stdout import StdOutCallbackHandler
from geopy.distance import geodesic

import requests
from dataclasses import dataclass
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from coordinates import GetCoordinatesTool
from nearest import FindNearestPlaceTool
from transport import GetTransportTimeTool

@dataclass
class Context:
    user_id: str

class Item(BaseModel):
    user_id: int
    prompt: str

@dataclass
class ResponseFormat:
    response: str
    ids: str

@tool
def get_likes(runtime: ToolRuntime[Context]):
    """Get the list of housing listings that the user has favourites and liked
    """
    user_id = runtime.context.user_id
    response = requests.post('http://backend:8000/liked-properties',json={'user_id':user_id})
    data = response.json()
    return data

@tool
def get_house(runtime: ToolRuntime[Context]):
    """Get the list of housing listings that is recommended to user based on his likings
    """
    user_id = runtime.context.user_id
    response = requests.post('http://backend:8000/recommend',json={'user_id':user_id})
    data = response.json()
    return data

@tool
def get_house_by_location(runtime: ToolRuntime[Context], latitude: float, longitude: float, distance: float):
    """Get the list of housing listings recommendations based on location and user likings

    Args:
        latitude: latitude of the location
        longitude: longitude of the location
        distance: surrounding distance of the location. If the user is only talking about "nearby", fill in 1 here.
    """
    user_id = runtime.context.user_id
    response = requests.post('http://backend:8000/recommend',json={
                             'user_id': user_id,
                             'location': {
                                 'latitude': latitude,
                                 'longitude': longitude,
                                 'distance': distance,
                             },
                         })
    data = response.json()
    return data

@tool
def calculate_distance_between_places(latitude: float, longitude: float, latitude2: float, longitude2: float):
    """Calculate the distance between 2 places, given the latitude and longitude of both places.

    Args:
        latitude: latitude of starting point
        longitude: longitude of starting point
        latitude2: latitude of ending point
        longitude2: longitude of ending point
    """
    dist = geodesic((latitude, longitude),(latitude2, longitude2)).meters
    return f'Distance is {dist}'

SYSTEM_PROMPT = '''
You need to act as an professional intermediary working on a rental platform.
Your main responsibility is helping users analyze issues related to renting a house.
Use tools to perform necessary lookups.
Try to communicate with your customers in the language they use.
Try to avoid conversations that are not related to your responsibilities.
If specific houses are included in the result, add the house ID to the ids field.
If there are multiple houses, seperate each Id with a , in a string format.
Do not include any image URL in any of your answers. 
'''

checkpointer = InMemorySaver()
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    callbacks=[StdOutCallbackHandler()],
) # lite is faster but sometimes it doesn't reply

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT, 
    tools=[
        GetCoordinatesTool(),
        FindNearestPlaceTool(),
        GetTransportTimeTool(),
        get_house,
        calculate_distance_between_places,
        get_house_by_location,
        get_likes
    ],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(item: Item):
    user_id = str(item.user_id)
    config = {"configurable": {"thread_id": {user_id}}}
    result = agent.invoke({"messages": [{"role": "user", "content": {item.prompt}}]},config=config, context=Context(user_id=user_id))
    return result['messages'][-1].content