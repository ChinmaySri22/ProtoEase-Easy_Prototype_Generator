PRODUCT_MANAGER_PRD_PROMPT = (
    "Create a detailed Product Requirements Document (PRD) in markdown for the user's request. "
    "Include: Overview, Goals, Features, Non-Goals, User Stories, Acceptance Criteria, "
    "Architecture Overview, and a File-by-File breakdown with filenames and brief descriptions. "
    "Keep it concise but complete."
)

CODER_GENERATION_PROMPT = (
    "Given the PRD and any QA feedback, produce a JSON object mapping filenames to their file contents. "
    "Filenames should be typical web app files like index.html, style.css, script.js. "
    "Ensure runnable, minimal dependencies, and avoid placeholders."
)

QA_REVIEW_PROMPT = (
    "Review the provided code against the PRD. Identify missing features, broken logic, or placeholder text. "
    "Return ONLY JSON:{\"tests_passed\": boolean, \"feedback\": string}."
)


