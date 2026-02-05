from dotenv import load_dotenv
import os, requests

load_dotenv()

key = os.environ["TAMU_API_KEY"]
r = requests.get(
    "https://chat-api.tamu.ai/openai/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=30,
)
r.raise_for_status()
print([m["id"] for m in r.json().get("data", [])])