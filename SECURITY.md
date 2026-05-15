# BertyType Security Disclosure

**Project:** BertyType  
**Date:** 2026-05-12  
**Version:** 1.0

---

## Security Assumptions

BertyType operates under the following trust model:

- **User account**: The primary trust boundary. All users sharing the same OS account are considered trusted.
- **Local network**: Ollama runs locally; no network data leaves the machine unless the user configures remote access.
- **Ollama instance**: The local Ollama service is trusted to execute models faithfully.
- **OS-level access**: BertyType assumes a non-adversarial local environment. Malicious processes with OS-level access can already compromise the system regardless of application-level controls.

---

## Design Limitations

The following limitations are inherent to BertyType's architecture and cannot be fixed without breaking core functionality or requiring OS-level changes.

---

### I-01: No Authentication Around Injection Mechanism

**Location:** `src/bertytype/injection/injector.py:6-9`

**Description:**  
The `inject()` function writes text to the active window via `pyperclip.copy()` + `pyautogui.hotkey("ctrl", "v")`. There is no confirmation prompt or authentication check. Any code path within BertyType can trigger injection at any time.

**Impact:**  
If BertyType is compromised (e.g., via a malicious configuration or dependency供应链 attack), it could silently inject arbitrary text into any focused window.

**Why it cannot be fixed:**  
This is inherent to the desktop automation design. Adding a confirmation prompt would break the real-time UX contract. Adding authentication would require OS-level sandboxing, which is outside the scope of an application-layer tool.

**Workaround:**  
Run BertyType in a dedicated user account with limited permissions.

---

### I-02: Global Hotkey Registration

**Location:** `src/bertytype/hotkeys/daemon.py:8`

**Description:**  
`keyboard.add_hotkey()` registers global hotkeys via the OS-level keyboard hook. Any process running under the same user account can register the same or overlapping hotkeys. A keylogger with the same OS-level privileges can observe all keyboard input regardless of what BertyType registers.

**Impact:**  
Keyloggers running under the same user account can intercept all input, including the push-to-talk hotkey sequence.

**Why it cannot be fixed:**  
Global hotkey registration is a fundamental OS service. BertyType has no mechanism to prevent other processes from registering the same hotkeys or observing keyboard events, as this would require OS-level access control beyond what a desktop application can enforce.

**Workaround:**  
Ensure the operating system is free of keyloggers and untrusted processes.

---

### I-03: LLM Refinement Requires Trust in Ollama

**Location:** `src/bertytype/llm/client.py:10-18`

**Description:**  
The `refine()` function sends raw transcripts to the local Ollama instance (`http://localhost:11434`). Ollama executes the model (`gemma4:e2b`) locally, but the model artifact is loaded from Ollama's registry — a third-party source. The model code is not audited by the BertyType project.

**Impact:**  
If the Ollama model is tampered with (e.g., a supply-chain compromise of the `gemma4:e2b` tag), the refined output could be adversarially altered. Additionally, Ollama runs as a network service, so if the user has configured Ollama to listen on the local network, other machines could send inference requests.

**Why it cannot be fixed:**  
BertyType depends on the Ollama model for text refinement. Replacing this with a fully self-hosted solution would require significant architectural changes. There is no mechanism in the current design to verify model integrity or restrict Ollama to loopback only.

**Workaround:**  
- Verify the Ollama model hash before use.  
- Configure Ollama to bind exclusively to `127.0.0.1` (not `0.0.0.0`).  
- Review Ollama's network configuration regularly.

---

### I-04: Non-Atomic Config Save

**Location:** `src/bertytype/config.py:81-83`

**Description:**  
The `save()` function writes directly to `config.json` using `write_text()`. There is no write-to-temp-then-rename pattern. If two BertyType instances write simultaneously, the last write wins, and partial writes could corrupt the file.

**Impact:**  
Running two instances simultaneously could cause config corruption. However, single-instance usage makes this unlikely in practice.

**Why it cannot be fixed:**  
Adding atomic writes would introduce complexity and a small window where the temp file exists unlinked on disk. The single-instance constraint (enforced by the system tray launcher) is the intended mitigation.

**Workaround:**  
Run only one instance of BertyType at a time. Back up `config.json` periodically.

---

## Report a Vulnerability

If you discover a security issue not listed above that falls within BertyType's control (i.e., not an OS-level or third-party service issue), please open an issue on the repository with:

- A clear description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigations (optional)

For OS-level issues (keyloggers, process isolation) or Ollama model integrity concerns, please report directly to the relevant upstream project.