# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- Stack: Python (>=3.9), setuptools build, src/ layout. Minimal dependency: jinja2.
- Purpose: Generate a resume from free-form text by heuristically extracting sections and rendering via a Jinja2 template.
- Entry points:
  - Module: python -m src.resume_agent.cli
  - Installed console script: resume-agent (defined in [project.scripts] in pyproject.toml)

Development commands (Windows PowerShell friendly)
- Install (editable) for local development:
  - python -m pip install -e .
- Run CLI without installing (from repo root):
  - Using a file: python -m src.resume_agent.cli --input input.txt --output resume.md --name "Jane Doe"
  - From stdin: type input.txt | python -m src.resume_agent.cli --output resume.md --name "Jane Doe"
    - Note: When typing interactively, end stdin with Ctrl+Z then Enter.
- Run CLI after installing (exposes the console script):
  - resume-agent --input input.txt --output resume.md --name "Jane Doe"
  - You can still pass a custom template with --template <path-to-template.j2>.
- Tests (pytest):
  - Install test tooling: python -m pip install pytest
  - Run all tests: python -m pytest -q
  - Run a single file: python -m pytest tests/test_generator.py -q
  - Run a single test: python -m pytest tests/test_generator.py::test_generate_resume_basic -q
- Build distributables (optional):
  - python -m pip install build
  - python -m build
  - Artifacts: dist/*.whl and dist/*.tar.gz
- Lint/format: None configured in this repo.

High-level architecture and code structure
- CLI layer (src/resume_agent/cli.py)
  - Parses arguments: --input, --output, --name, --template.
  - Reads from a file if --input is provided; otherwise reads stdin (Windows EOF: Ctrl+Z then Enter).
  - Calls generate_resume(...) and writes the resulting text to --output.
- Core domain (src/resume_agent/generator.py)
  - Data model: ResumeData dataclass (name, summary, skills, experiences).
  - parse_user_text(text) heuristics:
    - Splits into lines, trims, ignores blanks.
    - Detects a skills section ("skills", "skill:", or "skills:") and aggregates comma-separated or bulleted items.
    - Treats bulleted lines ("-"/"*") outside skills as experience items.
    - Everything else contributes to a free-form summary.
    - De-duplicates skills and experiences while preserving order.
  - render_resume(data, template_path):
    - Creates a Jinja2 Environment with FileSystemLoader on the template directory.
    - Auto-escapes only for html/xml templates, trims/lstrips blocks.
    - Renders with variables: name, summary, skills, experiences.
  - generate_resume(user_text, name=None, template_path=None):
    - Orchestrates parse_user_text and render_resume.
    - Default template path: <repo_root>/templates/resume.md.j2 if template_path is not provided.
- Tests (tests/test_generator.py)
  - Pytest-based check that generate_resume includes the provided name, a skill, and an experience in the output.

Repository layout
- src/resume_agent/: CLI and core logic (cli.py, generator.py, __init__.py)
- tests/: pytest tests
- pyproject.toml: build system (setuptools), project metadata, console script mapping
- templates/: expected location for Jinja2 templates (e.g., resume.md.j2). If missing, provide --template explicitly when running.

Important notes and nuances
- Template file: By default the code looks for templates/resume.md.j2 relative to the repo root. If this file is not present, pass --template with a valid path to a Jinja2 template.
- Namespace import pattern: Tests and CLI run from the project root using the src/ layout (e.g., python -m src.resume_agent.cli). After installation (pip install -e .), the console script resume-agent is the preferred entry point.
- No project-specific AI assistant rules detected: No CLAUDE.md, Cursor rules, or Copilot instructions were found.

Key references from README.md (incorporated here)
- Quickstart examples use:
  - type input.txt | python -m src.resume_agent.cli --output resume.md --name "Jane Doe"
  - python -m src.resume_agent.cli --input input.txt --output resume.md --name "Jane Doe"
- Default template path is templates/resume.md.j2 and output defaults to resume.md.
