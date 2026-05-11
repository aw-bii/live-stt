import requests
from concurrent.futures import ThreadPoolExecutor, Future
from bertytype.llm.prompts import get_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"

_executor = ThreadPoolExecutor(max_workers=1)


def refine(text: str, mode: str, model: str, timeout: int = 30) -> str:
    payload = {
        "model": model,
        "prompt": get_prompt(mode, text),
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["response"].strip()


def refine_async(text: str, mode: str, model: str, timeout: int = 30) -> Future:
    return _executor.submit(refine, text, mode, model, timeout)


def shutdown() -> None:
    _executor.shutdown(cancel_futures=True)
