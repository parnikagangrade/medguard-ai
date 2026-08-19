from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv("../.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_weather(city: str) -> str:
    """Returns the current weather for a given city. This is a fake test function."""
    return f"It's sunny in {city}."

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        tools=[get_weather],
        http_options=types.HttpOptions(timeout=60000)
    )
)

print("Sending message...")
response = chat.send_message("What's the weather like in Mumbai?")
print("Response:", response.text)