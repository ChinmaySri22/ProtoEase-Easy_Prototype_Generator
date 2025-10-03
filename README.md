## Generative AI Product Development Team

## Generative AI Product Development Team

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

1. `plan_node`

- Role: Product Manager
- Produces a concise PRD (markdown) and a file‑by‑file plan based on your request.

2. `code_node`

- Role: Senior Frontend Engineer
- Consumes the PRD (and any QA feedback) and returns a JSON map of filenames to contents.
- Writes each file to `ai_dev_team/outputs/`.
- If the model output isn’t valid JSON, a safe fallback scaffold is produced.

3. `qa_node`

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
git clone <your-repo-url>.git
cd "GenAI Project"
```

### 2) Create and activate a virtual environment (Windows PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r ai_dev_team/requirements.txt
```

### 4) Configure environment variables

Create a `.env` at the repo root (same folder as `ai_dev_team/`). You can either set a single shared provider or per‑agent providers.

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

Tip: You can avoid hand‑editing `.env` by using the Streamlit UI (below), which safely writes `USER_PRODUCT_REQUEST` and backs up the previous value to `ai_dev_team/outputs/`.

---

## Running the Pipeline

### Option A: Streamlit control panel (recommended)

`ai_dev_team/tools/streamlit_control.py` provides a small UI to:

- Enter and persist your `USER_PRODUCT_REQUEST` to `.env` (with automatic backups in `outputs/`)
- Launch the pipeline and stream logs in the browser
- Download generated artifacts

Run it:

```bash
streamlit run ai_dev_team/tools/streamlit_control.py
```

What it does under the hood:

- Validates inputs (e.g., hex color), composes a single request string, writes it to `.env`.
- Spawns the pipeline as a subprocess: `python -m ai_dev_team.main` with repo root as CWD.
- Streams stdout into the UI and, when complete, offers downloads for any files found in `ai_dev_team/outputs/`.

### Option B: Command line

```bash
python -m ai_dev_team.main
```

The script reads `USER_PRODUCT_REQUEST` from the environment, runs the graph, prints the list of generated files, and a preview of `index.html`. All artifacts are written to `ai_dev_team/outputs/`.

---

## Outputs

After a successful run, expect some of the following in `ai_dev_team/outputs/`:

- `index.html`, `style.css`, `script.js`
- `PRD.md` (when applicable) and/or `file_breakdown.json`
- `qa_log.json` (QA decision and feedback)
- `metrics.json` (iterations, pass/fail, generated file list)
- `_debug_raw_coder_output.txt` (raw model output for the coder step)
- `_debug_errors.txt` (if primary provider failed)

Open `index.html` directly in your browser to view the prototype.

---

## About `streamlit_control.py`

Located at `ai_dev_team/tools/streamlit_control.py`:

- Uses `streamlit` to render a form for your product idea and optional constraints.
- Persists `USER_PRODUCT_REQUEST` into `.env` using `python-dotenv`’s `set_key`.
- Backs up the previous request into `ai_dev_team/outputs/user_product_request_<timestamp>.txt`.
- Provides a one‑click “Start Generation” that runs the pipeline and streams logs.
- Lists and exposes download buttons for any generated artifacts.

If `.env` is not writable, it falls back to saving `ai_dev_team/outputs/user_product_request.txt` and surfaces the exception in the UI.

---

## Troubleshooting

- **No artifacts found**: Check the log output in Streamlit. See `_debug_raw_coder_output.txt` for the coder’s raw response and `_debug_errors.txt` for provider errors.
- **402 Payment Required on OpenRouter**: The system automatically retries with lower `max_tokens`. Provide a valid key or reduce generation size.
- **Empty or invalid model response**: The system falls back to Gemini when configured; otherwise, a simple scaffold is written.
- **TypeError: write() argument must be str, not None**: This is handled in `ai_dev_team/tools/file_tools.py` by coercing `None`/non‑string content to text before writing. Pull the latest code or ensure your local copy includes this fix. If it recurs, inspect `ai_dev_team/outputs/_debug_raw_coder_output.txt` to see the coder output that triggered it.
- **Firewall/Proxy issues**: Ensure Python can reach your chosen API endpoints.
- **Streamlit not launching**: Verify the virtual environment is active and `streamlit` is installed.

---

## Security & Keys

- Store API keys only in `.env` or your secret manager. Do not commit `.env`.
- The Streamlit UI reads/writes only `USER_PRODUCT_REQUEST` by default; provider keys must be added manually unless you extend the UI.

---

## Development Notes

- The `dev_agents.py` and `tasks.py` files contain CrewAI‑style abstractions and prompt snippets. The active pipeline in `main.py` uses LangGraph with its own prompts and does not directly import these agents.
- `file_tools.py` centralizes writing/clearing artifacts in `outputs/`.
- `file_tools.py` coerces `None` and other non‑string content to safe strings (JSON if possible) before writing, preventing crashes if a model returns unexpected types.

---

## License

Add your preferred license here.

An orchestrated, multi-agent system that turns a plain-English product request into a runnable frontend prototype. The system uses a small LangGraph workflow to coordinate three roles — Product Manager, Frontend Engineer, and QA — each powered by an LLM provider with sensible fallbacks. Generated code and artifacts are saved to `ai_dev_team/outputs/`.

### What this project does

- **Plan**: Produces a concise PRD with file-by-file breakdown from a single user request
- **Code**: Generates HTML/CSS/JS (and can scaffold a React app) based on the PRD
- **QA**: Reviews the generated code against the PRD and iterates up to a limit
- **Output**: Writes artifacts into `ai_dev_team/outputs/` (e.g., `index.html`, `style.css`, `script.js`, logs)

---

## Tech stack

- **Python**: Orchestration and agent workflow
  - `langgraph` for the state machine/graph
  - `requests` for HTTP calls to LLM providers
  - `python-dotenv` for environment configuration
- **LLM Providers** (configurable per agent)
  - Default primary: **OpenRouter** (`openrouter.ai`)
  - Fallback: **Google Gemini** (free tier capable)
  - OpenAI-compatible endpoints supported (e.g., DeepSeek)
- **Frontend (optional output)**
  - Plain HTML/CSS/JS generated by the system
  - A sample React app exists at `ai_dev_team/outputs/frontend/` (uses `react`, `react-dom`, `react-scripts`)

---

## Repository structure

```
ai_dev_team/
  main.py                 # Entry point: builds and runs the LangGraph workflow
  tasks.py                # Prompt strings for PM/FE/QA (conceptual; main has embedded prompts)
  tools/
    file_tools.py         # Helper to write/read files in outputs/
    streamlit_control.py  # One-UI controller to compose prompt and run pipeline
  outputs/                # All generated artifacts and debug logs are written here
    _debug_errors.txt
    _debug_raw_coder_output.txt
    frontend/             # Sample React app scaffold (optional)
      package.json
      src/
      public/
requirements.txt          # Python dependencies
```

---

## How it works

1. `main.py` constructs a LangGraph with nodes: `plan_node` → `code_node` → `qa_node`.
2. Each node invokes an LLM (provider configurable via env vars) through `MultiLLM`:
   - PM creates a PRD (markdown) and a file breakdown.
   - FE generates code files (expects a pure JSON mapping of filename → content).
   - QA validates output and may request fixes; loop continues until tests pass or max iterations.
   - The pipeline writes `PRD.md`, `qa_log.json`, and a summarized `metrics.json` at the end.
3. Files are written to `ai_dev_team/outputs/` using `tools/file_tools.py`.

Error handling highlights:

- If the primary provider fails or returns empty text, the system falls back to Gemini.
- If the coder returns non-JSON, a minimal runnable scaffold is generated to avoid a hard stop.
- Raw model outputs and errors are written to outputs for debugging.

---

## Prerequisites

- Windows, macOS, or Linux
- Python 3.9+ (3.10 recommended)
- Node.js 18+ and npm 9+ (only required if you want to run the React sample in `outputs/frontend/`)

---

## Setup

1. Create and activate a virtual environment (recommended).

   - Windows PowerShell:
     ```powershell
     cd "D:\SEMVII\Gen Agents\GenAI Project"
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

2. Install Python dependencies:

   ```powershell
   pip install -r ai_dev_team/requirements.txt
   ```

3. Create a `.env` file at the repo root with provider credentials. At minimum set one primary provider (OpenRouter recommended) or Gemini fallback.

   ```env
   # Primary provider: OpenRouter (recommended)
   OPENROUTER_API_KEY=sk-or-...
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1/chat/completions
   OPENROUTER_MAX_TOKENS=256
   OPENROUTER_TEMPERATURE=0.2

   # Optional: Per-agent overrides (if you want different models/providers per role)
   PRODUCT_MANAGER_PROVIDER=openrouter
   PRODUCT_MANAGER_MODEL=openrouter/auto:free
   PRODUCT_MANAGER_API_KEY=${OPENROUTER_API_KEY}
   PRODUCT_MANAGER_BASE_URL=${OPENROUTER_BASE_URL}

   CODER_PROVIDER=openrouter
   CODER_MODEL=openrouter/auto:free
   CODER_API_KEY=${OPENROUTER_API_KEY}
   CODER_BASE_URL=${OPENROUTER_BASE_URL}

   QA_PROVIDER=openrouter
   QA_MODEL=openrouter/auto:free
   QA_API_KEY=${OPENROUTER_API_KEY}
   QA_BASE_URL=${OPENROUTER_BASE_URL}

   # Fallback provider: Google Gemini
   GEMINI_API_KEY=AIza...
   GEMINI_MODEL=gemini-1.5-flash
   GEMINI_API_VERSION=v1

   # The product idea you want the team to build
   USER_PRODUCT_REQUEST=Create a simple to-do list app with add, complete, and delete features.
   ```

Environment variable notes:

- If you set `PRODUCT_MANAGER_*`, `CODER_*`, or `QA_*`, those override the respective role’s provider/model/base URL.
- If the primary provider fails (e.g., quota), the system tries Gemini automatically (if `GEMINI_API_KEY` is set).

---

## Run the generator

Two equivalent ways:

```powershell
# From repo root
python -m ai_dev_team.main

# or
python ai_dev_team/main.py
```

On success, you’ll see a list of generated files and a preview of `index.html` in the console. All artifacts live in `ai_dev_team/outputs/`.

Open the generated prototype directly in a browser:

- Double-click `ai_dev_team/outputs/index.html`, or
- Serve the `outputs/` folder from a simple HTTP server.

---

## Using the sample React app (optional)

A sample React app is included under `ai_dev_team/outputs/frontend/`. It is independent of the generator and can be used as a starting point if you prefer React.

Install and run:

```powershell
cd ai_dev_team/outputs/frontend
npm ci
npm start
```

Notes:

- The app uses `react`, `react-dom`, and `react-scripts`.
- If `react-scripts` is not found, ensure the `node_modules` directory exists (run `npm ci`).

---

## Configuration reference

`MultiLLM` honors the following environment variables (by prefix; all optional unless noted):

- Global defaults (used if per-agent not provided):

  - `OPENROUTER_API_KEY` (required to use OpenRouter)
  - `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1/chat/completions`)
  - `OPENROUTER_MAX_TOKENS` (default: 128)
  - `OPENROUTER_TEMPERATURE` (default: 0.2)
  - `GEMINI_API_KEY` (required to use fallback)
  - `GEMINI_MODEL` (default: `gemini-1.5-flash`)
  - `GEMINI_API_VERSION` (default: `v1`)

- Per-agent overrides (prefix = `PRODUCT_MANAGER_`, `CODER_`, `QA_`):
  - `<PREFIX>PROVIDER` (e.g., `openrouter`, `openai-compatible`, `google-gemini`)
  - `<PREFIX>MODEL`
  - `<PREFIX>API_KEY`
  - `<PREFIX>BASE_URL`
  - `<PREFIX>MAX_TOKENS`
  - `<PREFIX>TEMPERATURE`

Other app settings:

- `USER_PRODUCT_REQUEST`: The high-level request that drives the PM → FE → QA pipeline.
- Iterations: QA loop runs up to 5 times or stops early if `tests_passed` is true.

---

## Troubleshooting

- Missing/empty outputs:
  - Check `ai_dev_team/outputs/_debug_errors.txt` and `_debug_raw_coder_output.txt`.
  - Ensure at least one provider is configured and the API key is valid.
- Provider 402/Quota errors:
  - The app will try to reduce `max_tokens`, then fall back to Gemini if configured.
- Non-JSON coder output:
  - The app auto-extracts JSON from code fences; if it still fails, a safe fallback scaffold is generated.
- Windows PowerShell execution policy:
  - If venv activation fails, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current shell.

---

## Development tips

- Keep your `.env` out of version control.
- To change the product idea without editing code, modify `USER_PRODUCT_REQUEST` and re-run.
- New providers that are OpenAI-compatible can be used via `<PREFIX>PROVIDER=openai-compatible` and `<PREFIX>BASE_URL`.

---

## License

This repository does not include an explicit license. Add one if you plan to distribute.

---

## Tests and Metrics (new)

### Quick checks

1. Run the pipeline once to generate artifacts:

```powershell
python -m ai_dev_team.main
```

2. Run tests:

```powershell
pytest -q
```

What gets checked:

- Core files `index.html`, `style.css`, `script.js` are present
- `index.html` parses and contains an `#app` root
- If present, `qa_log.json` has a timestamp and QA payload
- If present, `metrics.json` includes a `latest` section with generated file list

Artifacts written by the pipeline:

- `PRD.md`: Product requirements from the PM step
- `qa_log.json`: QA result `{ tests_passed, feedback }` with timestamp
- `metrics.json`: `{ iterations, tests_passed, generated_files }` summarized under `latest`
