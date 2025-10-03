import os
from pathlib import Path
import json
import requests
from typing import TypedDict, Dict, Any, List

from dotenv import load_dotenv

# LangGraph
from langgraph.graph import StateGraph, END

# Local tools (support both package and script execution)
try:
    from .tools.file_tools import ensure_outputs_dir, write_file_to_outputs
    from .tools.metrics import write_prd, write_qa_log, write_metrics
except ImportError:  # Running as script: `python -m main` from inside folder
    from tools.file_tools import ensure_outputs_dir, write_file_to_outputs
    from tools.metrics import write_prd, write_qa_log, write_metrics


# Ensure we load the .env from the repository root deterministically
try:
    REPO_ROOT = Path(__file__).resolve().parents[1]  # repo root
    env_path = REPO_ROOT / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))
    else:
        load_dotenv()
except Exception:
    load_dotenv()


class MultiLLM:
    def __init__(self, env_prefix: str):
        # Primary provider config
        self.provider = os.getenv(f"{env_prefix}_PROVIDER", "openrouter")
        self.model_name = os.getenv(f"{env_prefix}_MODEL", "openrouter/auto:free")
        self.api_key = os.getenv(f"{env_prefix}_API_KEY", os.getenv("OPENROUTER_API_KEY"))
        self.base_url = os.getenv(
            f"{env_prefix}_BASE_URL",
            os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
        )
        self.max_tokens = int(os.getenv(f"{env_prefix}_MAX_TOKENS", os.getenv("OPENROUTER_MAX_TOKENS", "1200")))
        self.temperature = float(os.getenv(f"{env_prefix}_TEMPERATURE", os.getenv("OPENROUTER_TEMPERATURE", "0.2")))

        # Fallback to Google Gemini (free tier) if primary fails
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def _invoke_openrouter(self, messages: List[Dict[str, Any]]) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set in environment.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost"),
            "X-Title": os.getenv("OPENROUTER_APP_TITLE", "Generative AI Product Development Team"),
        }
        data = json.dumps({
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        })
        response = requests.post(self.base_url, headers=headers, data=data, timeout=120)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            detail = None
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            if response.status_code == 402:
                for reduced in (96, 64, 48):
                    try:
                        data2 = json.dumps({
                            "model": self.model_name,
                            "messages": messages,
                            "max_tokens": reduced,
                            "temperature": self.temperature,
                        })
                        response3 = requests.post(self.base_url, headers=headers, data=data2, timeout=120)
                        response3.raise_for_status()
                        return response3.json()["choices"][0]["message"]["content"]
                    except Exception:
                        continue
            raise requests.HTTPError(f"OpenRouter request failed: {e}; detail: {detail}") from e
        return response.json()["choices"][0]["message"]["content"]

    def _invoke_openai_compatible(self, messages: List[Dict[str, Any]]) -> str:
        # For providers like DeepSeek or other OpenAI-compatible endpoints
        if not self.api_key:
            raise RuntimeError(f"{self.provider} API key is not set.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = self.base_url or "https://api.deepseek.com/chat/completions"
        data = json.dumps({
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        })
        response = requests.post(url, headers=headers, data=data, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _invoke_gemini(self, messages: List[Dict[str, Any]]) -> str:
        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        # Convert OpenAI-format messages to Gemini contents
        contents: List[Dict[str, Any]] = []
        for msg in messages:
            role_in = msg.get("role", "user")
            text = msg.get("content", "")
            # Map roles: system->user, user->user, assistant->model
            role_out = "user"
            if role_in == "assistant":
                role_out = "model"
            contents.append({
                "role": role_out,
                "parts": [{"text": text}],
            })

        api_version = os.getenv("GEMINI_API_VERSION", "v1")
        headers = {"Content-Type": "application/json"}

        def try_call(model_id: str, version: str) -> str:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model_id}:generateContent?key={self.gemini_api_key}"
            payload = json.dumps({"contents": contents})
            resp = requests.post(url, headers=headers, data=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return json.dumps(data)

        # Try user-configured model and version
        try:
            return try_call(self.gemini_model, api_version)
        except requests.HTTPError:
            pass
        # Retry with stable v1 if not already
        if api_version != "v1":
            try:
                return try_call(self.gemini_model, "v1")
            except requests.HTTPError:
                pass
        # Retry with broadly available model names
        for fallback_model in ("gemini-1.5-flash", "gemini-1.5-pro"):
            if fallback_model != self.gemini_model:
                try:
                    return try_call(fallback_model, "v1")
                except requests.HTTPError:
                    continue
        # If all fail, re-raise a generic error
        raise requests.HTTPError("Gemini request failed after retries.")

    def invoke(self, messages: List[Dict[str, Any]]):
        try:
            result: str = ""
            provider_lower = self.provider.lower()
            if provider_lower == "openrouter":
                result = self._invoke_openrouter(messages)
            elif provider_lower in ("deepseek", "openai-compatible", "openai"):
                result = self._invoke_openai_compatible(messages)
            elif provider_lower in ("google-gemini", "gemini", "google"):
                result = self._invoke_gemini(messages)
            else:
                result = self._invoke_openai_compatible(messages)

            # Treat empty/whitespace-only responses as failure and fallback to Gemini
            if not isinstance(result, str) or not result.strip():
                return self._invoke_gemini(messages)
            return result
        except Exception as e:
            # Fallback to Gemini if configured; also write error to outputs for debugging
            try:
                write_file_to_outputs(file_path="_debug_errors.txt", content=f"Primary provider {self.provider} failed: {str(e)}")
            except Exception:
                pass
            return self._invoke_gemini(messages)


# Per-agent configurable providers
product_manager_llm = MultiLLM(env_prefix="PRODUCT_MANAGER")
coder_llm = MultiLLM(env_prefix="CODER")
qa_llm = MultiLLM(env_prefix="QA")


class GraphState(TypedDict, total=False):
    product_requirements: str
    code_files: Dict[str, str]
    qa_feedback: str
    iterations: int
    user_request: str


def plan_node(state: GraphState) -> GraphState:
    user_request = state.get("user_request", "Create a simple to-do list app")
    system_prompt = (
        "You are an elite Product Manager. Create a concise, actionable PRD that raises the bar on quality. "
        "Focus on: clear scope, user stories with acceptance criteria, accessibility (ARIA, focus, keyboard), "
        "responsiveness (mobile-first), and performance. Provide a file-by-file plan (HTML/CSS/JS only unless the user requests a framework). "
        "Favor modern visual design (spacing, elevation, motion) while keeping the code simple to run locally. "
        "Output MUST be a single, well-structured markdown string."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_request},
    ]
    prd_markdown = product_manager_llm.invoke(messages)
    # Persist PRD for transparency/debugging
    try:
        write_prd(prd_markdown)
    except Exception:
        pass
    return {
        **state,
        "product_requirements": prd_markdown,
        "iterations": 0,
    }


def _extract_json_block(text: str) -> str:
    # Heuristic to extract the first JSON object from text
    # 1) Prefer fenced ```json blocks
    fence_json_start = text.find("```json")
    if fence_json_start != -1:
        fence_content_start = fence_json_start + len("```json")
        fence_end = text.find("```", fence_content_start)
        if fence_end != -1:
            candidate = text[fence_content_start:fence_end].strip()
            if candidate:
                return candidate

    # 2) Fallback to any fenced block
    fence_any_start = text.find("```")
    if fence_any_start != -1:
        fence_any_content_start = fence_any_start + len("```")
        fence_any_end = text.find("```", fence_any_content_start)
        if fence_any_end != -1:
            candidate = text[fence_any_content_start:fence_any_end].strip()
            if candidate.startswith("{") and candidate.rstrip().endswith("}"):
                return candidate

    # 3) As a last resort, grab the first {...} span
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    
    # If no JSON found, try to find code blocks or create a simple structure
    if "html" in text.lower() or "css" in text.lower() or "javascript" in text.lower():
        # Create a simple structure from the text
        return json.dumps({
            "index.html": f"<!-- Generated from: {text[:200]}... -->\n<html><body><h1>Generated App</h1><p>Content: {text}</p></body></html>",
            "style.css": "body { font-family: Arial, sans-serif; margin: 20px; }",
            "script.js": "console.log('App loaded');"
        })
    
    return text


def code_node(state: GraphState) -> GraphState:
    ensure_outputs_dir()
    # Optional: clear previous core artifacts so each run overwrites cleanly
    try:
        from .tools.file_tools import clear_outputs_dir  # type: ignore
    except Exception:
        try:
            from tools.file_tools import clear_outputs_dir  # type: ignore
        except Exception:
            clear_outputs_dir = None
    if clear_outputs_dir:
        # Selective clean to avoid stale files interfering with new generation
        clear_outputs_dir(remove_all=False)
    prd = state.get("product_requirements", "")
    qa_feedback = state.get("qa_feedback", "")

    system_prompt = (
        "You are a Senior Frontend Engineer. Based on the PRD, produce production-quality HTML/CSS/JS. "
        "Requirements: responsive layout (mobile-first), strong accessibility (labels, roles, ARIA, focus states), "
        "clean architecture (small modular functions), graceful error handling, smooth micro-interactions (CSS transitions), "
        "modern visual design (Poppins or user-specified font; CSS variables; consistent spacing; elevation/shadows). "
        "No heavy frameworks unless explicitly requested. Do not reference external build steps; must work by opening index.html. "
        "If QA feedback is included, apply changes. Respond ONLY with a JSON object mapping filenames to file contents. "
        "Example: {\"index.html\": \"...\", \"style.css\": \"...\", \"script.js\": \"...\"}"
    )
    user_prompt = (
        f"PRD (markdown):\n{prd}\n\n"
        f"QA feedback (JSON or text, may be empty):\n{qa_feedback}\n\n"
        "Return ONLY the JSON object mapping filenames to contents."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw = coder_llm.invoke(messages)
    if not isinstance(raw, str) or not raw.strip():
        # Retry once with a stricter instruction
        strict_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + "\n\nIMPORTANT: Return ONLY a valid JSON object mapping filenames to contents. No prose, no code fences."},
        ]
        try:
            raw_retry = coder_llm.invoke(strict_messages)
            if isinstance(raw_retry, str) and raw_retry.strip():
                raw = raw_retry
        except Exception as e:
            try:
                write_file_to_outputs(file_path="_debug_errors.txt", content=f"Coder strict retry failed: {str(e)}")
            except Exception:
                pass
    # Persist raw output before any parsing to aid debugging
    try:
        debug_payload = raw if isinstance(raw, str) else json.dumps(raw)
        if not debug_payload:
            debug_payload = "<empty response from coder model>"
        write_file_to_outputs(file_path="_debug_raw_coder_output.txt", content=debug_payload)
    except Exception:
        pass
    json_text = _extract_json_block(raw)
    try:
        files: Dict[str, str] = json.loads(json_text)
    except Exception as e:
        # Fallback: create a neutral scaffold instead of a to-do app
        files = {
            "index.html": """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Generated App</title>
    <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>
    <div class=\"container\">
        <h1>Generated App</h1>
        <p>This is a minimal scaffold generated as a fallback.</p>
        <div id=\"app\"></div>
    </div>
    <script src=\"script.js\"></script>
    <!-- Fallback was triggered because model output could not be parsed as JSON. -->
    <!-- Error: {e} -->
</body>
</html>""",
            "style.css": """body {
    font-family: Arial, sans-serif;
    background-color: #fafafa;
    margin: 0;
    padding: 24px;
}

.container {
    max-width: 720px;
    margin: 0 auto;
    background: #ffffff;
    padding: 24px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}

h1 { color: #222; }
p { color: #555; }
""",
            "script.js": """document.addEventListener('DOMContentLoaded', function() {
    const appRoot = document.getElementById('app');
    const info = document.createElement('pre');
    info.textContent = 'Fallback scaffold is active. Provide a valid USER_PRODUCT_REQUEST and ensure the model returns valid JSON.';
    appRoot.appendChild(info);
});"""
        }

    # Write files to outputs and update state
    for path, content in files.items():
        write_file_to_outputs(file_path=path, content=content)

    current = dict(state.get("code_files", {}))
    current.update(files)
    return {**state, "code_files": current}


def qa_node(state: GraphState) -> GraphState:
    code_files = state.get("code_files", {})
    prd = state.get("product_requirements", "")
    system_prompt = (
        "You are a meticulous QA Engineer. Validate functionality against user stories and acceptance criteria. "
        "Check: responsive layout (various widths), accessibility (labels, roles, landmarks, keyboard, focus), "
        "visual quality (consistent spacing, color contrast), resilience (empty/invalid input, storage failures), and performance. "
        "Fail for placeholder content or low fidelity. Output MUST be JSON: {tests_passed: boolean, feedback: string}."
    )
    user_prompt = (
        "PRD (markdown):\n" + prd + "\n\n" +
        "Code files (JSON mapping filename->content):\n" + json.dumps(code_files) + "\n\n" +
        "Return ONLY the JSON, nothing else."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    raw = qa_llm.invoke(messages)
    json_text = _extract_json_block(raw)
    try:
        parsed = json.loads(json_text)
        qa_json = json.dumps(parsed)
        # Write QA log artifact
        try:
            write_qa_log(parsed)
        except Exception:
            pass
    except Exception:
        fallback = {
            "tests_passed": False,
            "feedback": f"QA output not valid JSON. Raw: {json_text[:500]}"
        }
        qa_json = json.dumps(fallback)
        try:
            write_qa_log(fallback)
        except Exception:
            pass

    iterations = (state.get("iterations") or 0) + 1
    return {**state, "qa_feedback": qa_json, "iterations": iterations}


def should_continue(state: GraphState):
    max_iters = 5
    iterations = state.get("iterations", 0)
    if iterations >= max_iters:
        return END
    qa_feedback = state.get("qa_feedback", "")
    try:
        parsed = json.loads(qa_feedback) if isinstance(qa_feedback, str) else qa_feedback
        if parsed.get("tests_passed") is True:
            return END
    except Exception:
        # If QA feedback malformed, continue loop to attempt fixes
        pass
    return "code_node"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("plan_node", plan_node)
    graph.add_node("code_node", code_node)
    graph.add_node("qa_node", qa_node)

    graph.set_entry_point("plan_node")
    graph.add_edge("plan_node", "code_node")
    graph.add_edge("code_node", "qa_node")
    graph.add_conditional_edges("qa_node", should_continue)
    return graph


if __name__ == "__main__":
    ensure_outputs_dir()
    # Always prefer the full user-authored request; no baked-in defaults
    user_high_level_request = os.getenv("USER_PRODUCT_REQUEST", "Build a small web application per my description.")

    graph = build_graph()
    app = graph.compile()

    initial_input: GraphState = {
        "user_request": user_high_level_request,
        "code_files": {},
        "iterations": 0,
    }
    final_state: GraphState = app.invoke(initial_input)

    code_files = final_state.get("code_files", {})
    qa_feedback_raw = final_state.get("qa_feedback", "{}")
    iterations_final = final_state.get("iterations", 0)
    tests_passed = False
    try:
        qa_obj = json.loads(qa_feedback_raw) if isinstance(qa_feedback_raw, str) else qa_feedback_raw
        tests_passed = bool(qa_obj.get("tests_passed", False))
    except Exception:
        pass

    # Write simple run metrics
    try:
        write_metrics({
            "iterations": iterations_final,
            "tests_passed": tests_passed,
            "generated_files": list(code_files.keys()),
        })
    except Exception:
        pass
    print("Generated files:")
    for name in code_files:
        print(f" - {name}")
    print("\nindex.html preview:\n")
    print(code_files.get("index.html", "<no index.html generated>")[:1000])


