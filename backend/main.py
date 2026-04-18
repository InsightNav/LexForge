from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
import PyPDF2
import io
import time

from redactor import redact_text, restore_text_deep
from agents.lawyer import analyze_contract
from agents.coder import fix_code

load_dotenv()

app = FastAPI()


# ---------- PDF EXTRACTION ----------
def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        ).strip()
    except:
        return ""


# ---------- CONTRACT ANALYSIS ----------
@app.post("/analyze-contract")
async def analyze_contract_api(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith((".pdf", ".txt")):
            return {"error": "Only PDF or TXT allowed"}

        content = await file.read()

        if len(content) > 5_000_000:
            return {"error": "File too large (max 5MB)"}

        raw_text = extract_pdf_text(content)

        if not raw_text:
            return {
                "result": {
                    "score": 0,
                    "risks": [{
                        "clause": "EMPTY_DOCUMENT",
                        "issue": "No readable text found",
                        "severity": "High"
                    }],
                    "fixes": []
                },
                "processing_time": 0
            }

        redacted_text, mapping = redact_text(raw_text)

        start = time.time()
        result = analyze_contract(redacted_text)
        processing_time = round(time.time() - start, 2)

        result = restore_text_deep(result, mapping)

        if isinstance(result, dict):
            result.setdefault("score", 50)
            result.setdefault("risks", [])
            result.setdefault("fixes", [])
            result["total_risks"] = len(result["risks"])

        return {
            "result": result,
            "processing_time": processing_time
        }

    except Exception as e:
        return {"error": str(e)}


# ---------- CODE FIXING ----------
@app.post("/fix-code")
async def fix_code_api(file: UploadFile = File(...)):
    try:
        if not file.filename.lower().endswith((".py", ".js", ".cpp", ".java", ".txt")):
            return {"error": "Unsupported file type"}

        content = await file.read()
        code = content.decode("utf-8", errors="ignore")

        return fix_code(code, filename=file.filename)

    except Exception as e:
        return {"error": str(e)}