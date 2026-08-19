from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv("../.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        http_options=types.HttpOptions(timeout=60000)  # 60 seconds
    )
)
print("Sending message...")
response = chat.send_message("Say hi in one word")
print("Response:", response.text)
