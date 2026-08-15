from pathlib import Path


def test_agent_handover_documents_are_present_and_linked() -> None:
    expected_documents = (
        "docs/ai/START_HERE.md",
        "docs/ai/AGENT_WORKFLOW.md",
        "docs/implementation/current-state.md",
        "docs/implementation/risk-register.md",
        "docs/implementation/definition-of-done.md",
        "docs/implementation/handoffs/phase-1.md",
        "docs/implementation/dependency-baseline.md",
        "docs/implementation/phases/phase-0.md",
    )

    for document in expected_documents:
        assert Path(document).is_file()

    instructions = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "docs/ai/START_HERE.md" in instructions
    assert "docs/implementation/definition-of-done.md" in instructions
