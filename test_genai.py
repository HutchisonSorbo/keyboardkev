import asyncio
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv('.env')

async def main():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents='hello',
        config=types.GenerateContentConfig(
            system_instruction='talk like a pirate',
        )
    )
    print(response.text)

asyncio.run(main())
