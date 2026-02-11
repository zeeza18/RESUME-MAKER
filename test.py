import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    print("❌ CLAUDE_API_KEY not found in .env file")
    raise SystemExit(1)

print("✅ API Key Loaded")

client = anthropic.Anthropic(api_key=api_key)

try:
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=80,
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
    )

    print("✅ API Key is working!")
    print("Claude says:", message.content[0].text)

except Exception as e:
    print("❌ API Key test failed")
    print("Error:", e)
