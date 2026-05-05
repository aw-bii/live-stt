import requests
from livesttt.llm.prompts import get_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"


def refine(text: str, mode: str, model: str) -> str:
    payload = {
        "model": model,
        "prompt": get_prompt(mode, text),
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["response"].strip()
