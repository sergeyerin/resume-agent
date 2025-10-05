import argparse
import sys
from pathlib import Path

from .generator import generate_resume


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a resume from user-provided text describing experience and skills.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input text file. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="resume.md",
        help="Where to write the generated resume (default: resume.md)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name to appear at the top of the resume (optional)",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "templates" / "resume.md.j2"),
        help="Path to a Jinja2 template (default: templates/resume.md.j2)",
    )

    args = parser.parse_args()

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        # Read from stdin until EOF (Ctrl+Z then Enter on Windows, Ctrl+D on Unix)
        text = sys.stdin.read()

    output_text = generate_resume(
        user_text=text,
        name=args.name,
        template_path=args.template,
    )

    Path(args.output).write_text(output_text, encoding="utf-8")
    print(f"Resume written to {args.output}")


if __name__ == "__main__":
    main()
