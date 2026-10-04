import os
from dotenv import load_dotenv
load_dotenv()

def generate(prompt: str, fallback: str) -> tuple[str, bool]:
    """Returns response and whether it came from a configured LLM."""
    key = os.getenv("OPENAI_API_KEY")
    if not key: return fallback, False
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": "Be accurate. Never invent resume facts."}, {"role": "user", "content": prompt}], temperature=0.3)
        return response.choices[0].message.content, True
    except Exception as exc:
        return f"LLM request unavailable ({exc}).\n\n{fallback}", False
