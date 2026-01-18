import os, json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """
Extract ONLY verifiable factual claims containing:
- statistics
- dates
- financial figures
- technical specs

Ignore opinions and generic statements.

Return STRICT JSON list:
[
  {"claim": "...", "category": "statistic|date|financial|technical|other"}
]
"""

def extract_claims(text: str):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text[:12000]}
        ],
        temperature=0,
        max_tokens=2048,
    )

    raw = completion.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except:
        return []
