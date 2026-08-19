print("Starting...")
from google import genai
from dotenv import load_dotenv
import os

load_dotenv("../.env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
print("Sending request...")

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Say hi in one word"
)
print("Response:", response.text)