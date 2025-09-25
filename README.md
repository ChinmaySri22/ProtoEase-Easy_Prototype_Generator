## ProtoEase: Easy Protopype Generator

Turn a plain‑English product request into a runnable, single‑page web prototype (HTML/CSS/JS). This repo contains a small multi‑agent pipeline (PM → Coder → QA) orchestrated with LangGraph, a Streamlit control panel, and provider‑agnostic LLM invocation with graceful fallbacks.

### Objectives
- **Natural language → runnable prototype**: Generate `index.html`, `style.css`, `script.js` directly, with no build steps.
- **Quality guardrails**: Enforce responsiveness, accessibility, and basic QA through iterative checks.
- **Provider‑agnostic**: Work with OpenRouter, OpenAI‑compatible APIs, and Google Gemini as fallback.
- **Simple UX**: A Streamlit UI to save your request, run the pipeline, view logs, and download artifacts.

---

## Project Structure

```text
GenAI Project/
  ai_dev_team/
    __init__.py
    main.py                 # Entry point for the pipeline (LangGraph graph)
    dev_agents.py           # Optional CrewAI-style agent definitions (not used by graph)
    tasks.py                # Prompt/snippets used by agents (reference)
    tools/
      __init__.py
      streamlit_control.py  # Streamlit app to control pipeline & manage USER_PRODUCT_REQUEST
      file_tools.py         # Helpers to write/read/clear files in outputs/
    outputs/                # Generated artifacts and debug logs
      index.html, style.css, script.js, PRD.md, qa_log.json, _debug_* etc.
    requirements.txt        # Python deps
  README.md
```

Generated artifacts are written to `ai_dev_team/outputs/`.

---

## Tech Stack
- **Python** 3.9+ (tested on Windows)
- **LangGraph** for the PM→Coder→QA graph
- **requests** for HTTP calls
- **python-dotenv** for `.env` management
- **Streamlit** for the control panel
- Optional: **CrewAI** (agents defined but not required by the core graph)

---

## How it Works (Pipeline)

The core pipeline lives in `ai_dev_team/main.py` and uses a three‑node LangGraph:

1) `plan_node`
- Role: Product Manager
- Produces a concise PRD (markdown) and a file‑by‑file plan based on your request.

2) `code_node`
- Role: Senior Frontend Engineer
- Consumes the PRD (and any QA feedback) and returns a JSON map of filenames to contents.
- Writes each file to `ai_dev_team/outputs/`.
- If the model output isn’t valid JSON, a safe fallback scaffold is produced.

3) `qa_node`
- Role: QA Engineer
- Reviews generated files vs PRD and returns `{ tests_passed: boolean, feedback: string }`.
- If tests fail, the loop continues (up to 5 iterations) to let the Coder incorporate feedback.

### Multi‑Provider LLM Invocation
`MultiLLM` (in `main.py`) selects a provider by environment variables and implements fallbacks:
- Primary: `openrouter` (default), or any `openai-compatible` endpoint, or `google-gemini`.
- If the primary returns an empty/invalid response or errors, it falls back to Gemini when configured.
- For OpenRouter HTTP 402 (quota), it retries with lower `max_tokens`.

---

## Getting Started (from scratch)

### 1) Clone and enter the repo
```bash
git clone https://github.com/ChinmaySri22/ProtoEase-Easy_Prototype_Generator.git
cd "ProtoEase-Easy_Prototype_Generator"
```

### 2) Create and activate a virtual environment (Windows PowerShell)
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Configure environment variables
Create a `.env` at the repo root (same folder as `ProtoEase-Easy_Prototype_Generator`). You can either set a single shared provider or per‑agent providers.

Minimal (OpenRouter) setup:
```env
# Required for OpenRouter
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_MAX_TOKENS=1200
OPENROUTER_TEMPERATURE=0.2

# Optional app metadata
OPENROUTER_HTTP_REFERER=http://localhost
OPENROUTER_APP_TITLE=Generative AI Product Development Team

# Optional Google Gemini fallback
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash

# The user request that drives generation (can also be set via Streamlit UI)
USER_PRODUCT_REQUEST=Build a modern, responsive web app that ...
```

Per‑agent overrides (optional):
```env
# PRODUCT_MANAGER, CODER, QA each honor _PROVIDER, _MODEL, _API_KEY, _BASE_URL, _MAX_TOKENS, _TEMPERATURE
PRODUCT_MANAGER_PROVIDER=openrouter
CODER_PROVIDER=openrouter
QA_PROVIDER=openrouter

# Example for an OpenAI‑compatible endpoint (DeepSeek/etc.)
CODER_PROVIDER=openai-compatible
CODER_API_KEY=sk-...
CODER_BASE_URL=https://api.deepseek.com/chat/completions
CODER_MODEL=deepseek-chat
```

Tip: You can avoid hand‑editing `.env` by using the Streamlit UI (below), which safely writes `USER_PRODUCT_REQUEST` and backs up the previous value to `ProtoEase-Easy_Prototype_Generator/outputs/`.

---

## Running the Pipeline

### Option A: Streamlit control panel (recommended)

`ProtoEase-Easy_Prototype_Generator/tools/streamlit_control.py` provides a small UI to:
- Enter and persist your `USER_PRODUCT_REQUEST` to `.env` (with automatic backups in `outputs/`)
- Launch the pipeline and stream logs in the browser
- Download generated artifacts

Run it:
```bash
streamlit run ProtoEase-Easy_Prototype_Generator/tools/streamlit_control.py
```

What it does under the hood:
- Validates inputs (e.g., hex color), composes a single request string, writes it to `.env`.
- Spawns the pipeline as a subprocess: `python -m ProtoEase-Easy_Prototype_Generator.main` with repo root as CWD.
- Streams stdout into the UI and, when complete, offers downloads for any files found in `ProtoEase-Easy_Prototype_Generator/outputs/`.

### Option B: Command line
```bash
python -m ProtoEase-Easy_Prototype_Generator.main
```
The script reads `USER_PRODUCT_REQUEST` from the environment, runs the graph, prints the list of generated files, and a preview of `index.html`. All artifacts are written to `ai_dev_team/outputs/`.

---

## Outputs
After a successful run, expect some of the following in `ProtoEase-Easy_Prototype_Generator/outputs/`:
- `index.html`, `style.css`, `script.js`
- `PRD.md` (when applicable) and/or `file_breakdown.json`
- `qa_log.json` (QA decision and feedback)
- `_debug_raw_coder_output.txt` (raw model output for the coder step)
- `_debug_errors.txt` (if primary provider failed)

Open `index.html` directly in your browser to view the prototype.

---

## About `streamlit_control.py`

Located at `ProtoEase-Easy_Prototype_Generator/tools/streamlit_control.py`:
- Uses `streamlit` to render a form for your product idea and optional constraints.
- Persists `USER_PRODUCT_REQUEST` into `.env` using `python-dotenv`’s `set_key`.
- Backs up the previous request into `ProtoEase-Easy_Prototype_Generator/outputs/user_product_request_<timestamp>.txt`.
- Provides a one‑click “Start Generation” that runs the pipeline and streams logs.
- Lists and exposes download buttons for any generated artifacts.

If `.env` is not writable, it falls back to saving `ProtoEase-Easy_Prototype_Generator/outputs/user_product_request.txt` and surfaces the exception in the UI.

---

## Troubleshooting
- **No artifacts found**: Check the log output in Streamlit. See `_debug_raw_coder_output.txt` for the coder’s raw response and `_debug_errors.txt` for provider errors.
- **402 Payment Required on OpenRouter**: The system automatically retries with lower `max_tokens`. Provide a valid key or reduce generation size.
- **Empty or invalid model response**: The system falls back to Gemini when configured; otherwise, a simple scaffold is written.
- **Firewall/Proxy issues**: Ensure Python can reach your chosen API endpoints.
- **Streamlit not launching**: Verify the virtual environment is active and `streamlit` is installed.

---

## Security & Keys
- Store API keys only in `.env` or your secret manager. Do not commit `.env`.
- The Streamlit UI reads/writes only `USER_PRODUCT_REQUEST` by default; provider keys must be added manually unless you extend the UI.

---
