import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ZAI_API_KEY")
BASE_URL = "https://api.z.ai/api/anthropic"

if not API_KEY:
    raise SystemExit("ZAI_API_KEY environment variable is required")

client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

message = client.messages.create(
    model="glm-5.1",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello! Briefly introduce yourself."},
    ],
)

print(message.content[0].text)
