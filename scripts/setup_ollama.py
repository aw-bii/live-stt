#!/usr/bin/env python3
"""First-run helper: checks Ollama installation and pulls the gemma4:2b model."""
import subprocess
import sys

MODEL = "gemma4:2b"
OLLAMA_URL = "http://localhost:11434/api/tags"


def _ollama_running() -> bool:
    try:
        import requests
        return requests.get(OLLAMA_URL, timeout=5).status_code == 200
    except Exception:
        return False


def main() -> None:
    print("live-stt Ollama setup")
    print("---------------------")

    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("Ollama found.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Ollama not found. Install it from https://ollama.com then re-run this script.")
        sys.exit(1)

    if not _ollama_running():
        print("Ollama is installed but not running. Start it with: ollama serve")
        sys.exit(1)

    print(f"Pulling {MODEL} (approx 1.5 GB one-time download)...")
    result = subprocess.run(["ollama", "pull", MODEL])
    if result.returncode == 0:
        print(f"\n{MODEL} is ready. LLM refinement will be enabled on next launch.")
    else:
        print(f"\nPull failed. Run manually: ollama pull {MODEL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
