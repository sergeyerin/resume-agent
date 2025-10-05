from src.resume_agent.generator import generate_resume


def test_generate_resume_basic(tmp_path):
    text = """
    Experienced software engineer with background in Python and data processing.
    Skills: Python, Jinja2, Testing
    - Built ETL pipelines
    - Led code review sessions
    """.strip()

    output = generate_resume(text, name="Test User")
    assert "Test User" in output
    assert "Python" in output
    assert "Built ETL pipelines" in output
