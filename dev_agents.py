from typing import Any

from crewai import Agent

# Note: Tools are not used in the main workflow, so we don't import them here


def get_product_manager_agent(llm: Any) -> Agent:
    return Agent(
        role="Expert Product Manager",
        goal=(
            "Take a user's product idea and create a detailed PRD and a file-by-file "
            "breakdown of the necessary code. Output MUST be a single, well-structured markdown string."
        ),
        backstory=(
            "You are a seasoned Product Manager with a knack for translating vague ideas "
            "into concrete development plans."
        ),
        llm=llm,
        verbose=False,
        tools=[],
    )


def get_frontend_engineer_agent(llm: Any) -> Agent:
    return Agent(
        role="Senior Frontend Engineer",
        goal=(
            "Write high-quality HTML, CSS, and JavaScript based on the PRD and file breakdown. "
            "Debug and fix code based on QA feedback."
        ),
        backstory=(
            "You are a proficient frontend developer who writes clean, efficient, and bug-free code. "
            "You can read existing code, identify issues, and fix them."
        ),
        llm=llm,
        verbose=False,
        tools=[],
    )


def get_qa_engineer_agent(llm: Any) -> Agent:
    return Agent(
        role="Quality Assurance Engineer",
        goal=(
            "Review frontend code for obvious errors and missing elements based on the PRD. "
            "Output JSON: {\"tests_passed\": boolean, \"feedback\": string}."
        ),
        backstory=(
            "You are a meticulous QA engineer with a sharp eye for detail. You rigorously test "
            "code to ensure it meets requirements and is free of bugs."
        ),
        llm=llm,
        verbose=False,
        tools=[],
    )


