_TEMPLATES: dict[str, str] = {
    "clean_up": (
        "Clean up the following speech transcript. Fix grammar, remove filler words "
        "(um, uh, like), and add punctuation. Output only the cleaned text:\n\n{text}"
    ),
    "rewrite": (
        "Rewrite the following speech transcript as polished prose. "
        "Output only the rewritten text:\n\n{text}"
    ),
}


def _sanitize(text: str) -> str:
    return "".join(c for c in text if c.isprintable() or c in "\n\t")


def get_prompt(mode: str, text: str) -> str:
    if mode not in _TEMPLATES:
        raise ValueError(f"Unknown mode: {mode!r}. Choose from {list(_TEMPLATES)}")
    return _TEMPLATES[mode].format(text=_sanitize(text))
