import asyncio
import os
import sys

# Ensure the project root is in sys.path
sys.path.append(os.path.abspath("."))

import openai

async def main():
    # Configure the OpenAI client with the provided settings
    client = openai.AsyncClient(
        base_url="http://fcas1bcalc:8008/v1",
        api_key="token-abc123",
    )
    # Prepare the chat request
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello, what is the weather today?"}],
        timeout=30.0,
    )
    # Print the raw response object
    print("Raw LLM response:", response)
    # If there are choices, print the first message content
    if response.choices:
        print("LLM answer:", response.choices[0].message.content)

if __name__ == "__main__":
    asyncio.run(main())
