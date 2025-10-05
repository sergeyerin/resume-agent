import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .generator import generate_resume


def _read_text_input(input_path: Optional[str]) -> str:
    if input_path:
        return Path(input_path).read_text(encoding="utf-8")
    # Read from stdin until EOF (Ctrl+Z then Enter on Windows, Ctrl+D on Unix)
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a resume from user-provided text. By default, uses OpenAI to generate "
            "a professional resume. You can disable OpenAI with --no-openai to use the built-in "
            "heuristic template renderer."
        ),
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
    # OpenAI-related flags and structured fields
    parser.add_argument(
        "--use-openai",
        dest="use_openai",
        action="store_true",
        default=True,
        help="Use OpenAI to generate the resume (default)",
    )
    parser.add_argument(
        "--no-openai",
        dest="use_openai",
        action="store_false",
        help="Disable OpenAI and use built-in heuristic renderer",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model to use (default: gpt-4o-mini or $OPENAI_MODEL)",
    )
    parser.add_argument("--first-name", type=str, default=None, help="User first name")
    parser.add_argument("--last-name", type=str, default=None, help="User last name")
    parser.add_argument("--phone", type=str, default=None, help="User phone number")
    parser.add_argument("--email", type=str, default=None, help="User email address")
    parser.add_argument(
        "--template",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "templates" / "resume.md.j2"),
        help="Path to a Jinja2 template (default: templates/resume.md.j2) used when --no-openai",
    )

    args = parser.parse_args()

    text = _read_text_input(args.input)

    if args.use_openai:
        # Ensure API key is present in environment
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. Set it before running with OpenAI."
            )
        # Import lazily to avoid test-time dependency when OpenAI is unused
        from .openai_resume import collect_user_profile, generate_resume_with_openai

        profile = collect_user_profile(
            raw_text=text,
            first_name=args.first_name,
            last_name=args.last_name,
            phone=args.phone,
            email=args.email,
        )
        output_text = generate_resume_with_openai(profile=profile, raw_text=text, model=args.model)
    else:
        # Fallback to built-in heuristic + template renderer
        full_name = None
        if args.first_name or args.last_name:
            full_name = f"{args.first_name or ''} {args.last_name or ''}".strip() or None
        # Maintain compatibility with previous --name flag if present in user scripts
        name_arg = full_name if full_name else None
        output_text = generate_resume(
            user_text=text,
            name=name_arg,
            template_path=args.template,
        )

    Path(args.output).write_text(output_text, encoding="utf-8")
    print(f"Resume written to {args.output}")


if __name__ == "__main__":
    main()
