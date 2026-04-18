from google import genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a corporate lawyer.

Return ONLY valid JSON.

Format:
{
  "score": number,
  "risks": [
    {
      "clause": "...",
      "issue": "...",
      "severity": "Low | Medium | High"
    }
  ],
  "fixes": [
    {
      "problem": "...",
      "suggestion": "..."
    }
  ]
}
"""


def call_model(prompt: str):
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config={"temperature": 0.2, "max_output_tokens": 800}
            )
            return res.text.strip()

        except Exception as e:
            if any(x in str(e) for x in ["429", "503", "UNAVAILABLE"]):
                time.sleep((2 ** attempt) * 2)
                continue
            return None

    return None


def analyze_contract(text: str):
    text = text[:2000]

    raw = call_model(f"{SYSTEM_PROMPT}\n\nCONTRACT:\n{text}")

    if not raw:
        return {
            "score": 50,
            "risks": [{
                "clause": "MODEL_UNAVAILABLE",
                "issue": "AI temporarily unavailable",
                "severity": "Medium"
            }],
            "fixes": []
        }

    try:
        return json.loads(raw)
    except:
        return {
            "status": "fallback",
            "score": 50,
            "risks": [{
                "clause": "PARSE_ERROR",
                "issue": raw[:300],
                "severity": "Medium"
            }],
            "fixes": []
        }