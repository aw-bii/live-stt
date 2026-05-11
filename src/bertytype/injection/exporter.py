from pathlib import Path


def save_transcript(text: str, source_path: Path) -> Path:
    out = source_path.with_suffix(".txt")
    out.write_text(text, encoding="utf-8")
    return out
