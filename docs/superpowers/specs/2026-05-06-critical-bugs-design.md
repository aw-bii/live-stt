# Critical Bugs Fix - Design Spec

**Date:** 2026-05-06
**Scope:** 6 critical bugs, single branch/PR
**Files touched:** `src/livesttt/__main__.py`, `src/livesttt/stt/vibevoice_local.py`, `src/livesttt/llm/client.py`, `launch.py` (delete)

---

## Overview

Six critical bugs fixed in one PR. The theme: the app must start cleanly, run safely under concurrent access, and shut down completely.

Three micro-themes:

| Micro-theme | Bugs |
| --- | --- |
| Shutdown correctness | Health monitor stop event, executor shutdown |
| Thread safety | `_health` race condition |
| Behavioral correctness | PTT hotkey combo, `is_available()` model load, `launch.py` |

---

## Fix 1 - PTT Hotkey Strips Modifiers

**File:** `src/livesttt/__main__.py:198`

**Problem:** The current code splits the hotkey string on `"+"` and passes only the last token (e.g. `"space"`) to `register_ptt` with `suppress=True`. This intercepts every spacebar keypress system-wide, ignoring any modifier keys in the combo.

**Fix:** Replace the split logic with a direct `keyboard.add_hotkey(_cfg.hotkey, _on_ptt_press, suppress=True)` call at the call site in `__main__.py`. The `keyboard` library natively parses full combo strings like `"ctrl+shift+space"`, so no changes to `register_ptt` are needed.

---

## Fix 2 - `is_available()` Loads the Full Model

**File:** `src/livesttt/stt/vibevoice_local.py:42-47`

**Problem:** `is_available()` calls `_get_model()`, which triggers a multi-GB Transformers download on first call. It is invoked 3x at startup and every 60 s by the health monitor, making startup slow and health checks expensive.

**Fix:** Replace the `_get_model()` call with a lightweight import check:

```python
def is_available() -> bool:
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False
```

Model loading stays deferred to the first `transcribe()` call only.

---

## Fix 3 - Health Monitor Thread is Unstoppable

**File:** `src/livesttt/__main__.py:173`

**Problem:** The health monitor loop creates a fresh `threading.Event()` each iteration, so `_on_quit` setting `.set()` on a different object never reaches the sleeping thread.

**Fix:** Promote to a module-level `_quit_event = threading.Event()`. The `_periodic_health_check` loop uses `_quit_event.wait(timeout=60)` as its sleep. `_on_quit` calls `_quit_event.set()` before joining the monitor thread, guaranteeing it wakes and exits.

---

## Fix 4 - Race Condition on `_health` Dict

**File:** `src/livesttt/__main__.py:54,67,171`

**Problem:** The monitor thread reassigns the `_health` module global while worker threads read it concurrently. No synchronization.

**Fix:** Add a module-level `_health_lock = threading.Lock()`. All three access sites acquire it:

- Monitor thread wraps reassignment in `with _health_lock`
- `_capture_and_process` and `_on_transcribe_file` call `_health.copy()` under the lock before reading

No structural changes - consistent lock acquisition at the three existing access points.

---

## Fix 5 - `refine_async` ThreadPoolExecutor Never Shut Down

**File:** `src/livesttt/llm/client.py:7`

**Problem:** The module-level `ThreadPoolExecutor` is never shut down on quit, which can hang the process on Windows. Queued refinements can also inject stale text after a new recording starts.

**Fix:** Expose a `shutdown()` function from `llm/client.py` that calls `_executor.shutdown(cancel_futures=True)`. `_on_quit` in `__main__.py` calls this before the tray stops, draining in-flight work and preventing stale injection.

---

## Fix 6 - Stray `launch.py` Shadows Real Entry Point

**File:** `launch.py` (repo root, untracked)

**Problem:** An untracked `launch.py` exists with broken behavior (bare `except`, no settings/quit/tray wiring). It shadows the real entry point and misleads contributors.

**Fix:** Delete the file. The documented entry points (`python -m livesttt`, `__main__.py`) are sufficient.

---

## Testing

**New tests (2):**

1. **Health monitor stop** - Patch `_quit_event`, call `_on_quit`, assert the monitor thread exits within a timeout. Covers the one shutdown path with no prior test coverage.

2. **`is_available()` cheapness** - Update `test_is_available_returns_true_when_model_loads` to mock the `transformers` import rather than `_get_model`. Confirms no model load occurs during the check.

**Unchanged coverage:** Fixes 1, 4, 5, 6 are covered by the existing test suite plus a manual smoke test (launch, record, quit cleanly).

---

## Out of Scope

- Important bugs and polish items from TODO.md (deferred to a separate plan)
- Any refactoring beyond the minimum needed for each fix
