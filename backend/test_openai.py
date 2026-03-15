import logging
logging.basicConfig(level=logging.DEBUG)

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Test"}],
        max_tokens=10,
    )
    print(response)
except Exception as e:
    print("ERROR:")
    import traceback
    traceback.print_exc()
