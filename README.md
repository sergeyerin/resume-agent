# Resume Agent

An agent that formulates and writes a resume based on user-provided text describing experience and skills.

It reads raw text from a file or stdin, heuristically extracts key sections (summary, skills, experiences), and renders a resume using a Jinja2 template.

## Quickstart

- Run without installing (from project root):
  - Using a file as input (Windows):
    - `type input.txt | python -m src.resume_agent.cli --output resume.md --name "Jane Doe"`
  - Or specify an input file:
    - `python -m src.resume_agent.cli --input input.txt --output resume.md --name "Jane Doe"`

- Template output defaults to Markdown using `templates/resume.md.j2`.

## CLI usage

```
python -m src.resume_agent.cli \
  --input <path-to-text> \
  --output resume.md \
  --name "Your Name" \
  [--template templates/resume.md.j2]
```

If `--input` is omitted, the program reads from stdin until EOF.

## Project structure

- `src/resume_agent/` — source code
- `templates/` — Jinja2 resume template(s)
- `tests/` — basic tests

## Notes

This is a minimal scaffold to get started. The parsing logic is intentionally simple and can be improved to better structure experience and skills.
