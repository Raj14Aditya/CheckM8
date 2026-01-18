import os, json, re
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
search = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

PROMPT = """
You are a professional fact checker and editor.

Given a CLAIM and EVIDENCE:

1. Classify the claim as:
- VERIFIED
- INACCURATE (outdated or partial)
- FALSE

2. If INACCURATE or FALSE, suggest a corrected sentence suitable for publication.

Return STRICT JSON only:
{
 "verdict": "VERIFIED|INACCURATE|FALSE",
 "explanation": "...",
 "correct_info": "corrected version of the claim",
 "confidence": 0.0
}
"""

# ---------- clean markdown & code blocks ----------
def clean_llm_text(text: str):
    text = text.replace("```json", "").replace("```", "").strip()
    return text


# ---------- robust parser ----------
def parse_llm_output(raw: str):
    raw = clean_llm_text(raw)

    # Try strict JSON
    try:
        result = json.loads(raw)
    except:
        result = None

    if isinstance(result, dict):
        verdict = str(result.get("verdict", "")).upper()

        if verdict == "TRUE":
            verdict = "VERIFIED"
        elif verdict not in ["VERIFIED", "INACCURATE", "FALSE"]:
            verdict = "INCONCLUSIVE"

        result["verdict"] = verdict
        result["explanation"] = str(result.get("explanation", "")).strip()
        result["correct_info"] = str(result.get("correct_info", "")).strip()
        return result

    # Fallback text detection
    verdict = "INCONCLUSIVE"

    if re.search(r"\bverified\b|\btrue\b|\bcorrect\b", raw, re.I):
        verdict = "VERIFIED"
    elif re.search(r"\bfalse\b|\bwrong\b", raw, re.I):
        verdict = "FALSE"
    elif re.search(r"\binaccurate\b|\boutdated\b|\bpartially\b", raw, re.I):
        verdict = "INACCURATE"

    return {
        "verdict": verdict,
        "explanation": raw.strip()[:500],
        "correct_info": "",
        "confidence": 0.0
    }


# ---------- main verifier ----------
def verify_claim(claim: str):
    res = search.search(query=claim, search_depth="advanced", max_results=5)

    evidence = []
    sources = []

    for r in res.get("results", []):
        evidence.append(r.get("content", ""))
        sources.append(r.get("url", ""))

    evidence_text = "\n\n".join(evidence)[:12000]

    completion = llm.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"CLAIM:\n{claim}\n\nEVIDENCE:\n{evidence_text}"}
        ],
        temperature=0,
        max_tokens=1024,
    )

    raw = completion.choices[0].message.content.strip()

    result = parse_llm_output(raw)
    result["sources"] = sources[:3]

    return result
