import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

def generate(prompt: str, fallback: str, max_tokens: int = 600) -> tuple[str, bool]:
    """Returns a local Ollama response and whether generation succeeded."""
    if not prompt.strip():
        logger.warning("Skipped Ollama generation because the prompt was empty")
        return fallback, False
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
            timeout=15,
        )
        response = client.chat.completions.create(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
            messages=[{"role": "system", "content": "Be accurate. Never invent resume facts."}, {"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max(1, max_tokens),
            extra_body={"keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "30m")},
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip(), True
        logger.warning("Ollama returned an empty response")
    except Exception:
        logger.exception("Ollama generation failed")
    return fallback, False
