from google import genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

WORKSPACE = "./workspace"


def write_to_disk(filename: str, content: str):
    os.makedirs(WORKSPACE, exist_ok=True)

    safe_name = os.path.basename(filename)

    if safe_name in ["main.py", "app.py"]:
        safe_name = "fixed_" + safe_name

    path = os.path.join(WORKSPACE, safe_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "status": "saved",
        "file": path,
        "preview": content[:300]
    }


def call_model(prompt: str):
    for attempt in range(3):
        try:
            res = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config={"temperature": 0.2, "max_output_tokens": 800}
            )
            return res.text
        except Exception as e:
            if "429" in str(e):
                time.sleep(2 ** attempt)
                continue
            raise e
    return None


def clean_json(raw: str):
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
    return raw.strip()


def fix_code(code: str, filename="fixed_file.py"):
    prompt = f"""
Fix this code.

Return ONLY JSON:
{{
  "action": "write" or "none",
  "filename": "{filename}",
  "content": "fixed code"
}}

CODE:
{code}
"""

    raw = call_model(prompt)

    if not raw:
        return {"status": "error", "message": "AI unavailable"}

    raw = clean_json(raw)

    try:
        data = json.loads(raw)
    except:
        return {"status": "parse_error", "raw": raw}

    if data.get("action") == "write":
        return write_to_disk(
            data.get("filename", filename),
            data.get("content", "")
        )

    return {"status": "no_changes"}