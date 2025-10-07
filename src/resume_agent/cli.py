import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .generator import generate_resume


def _read_file_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    ext = path.suffix.lower()
    if ext == ".docx":
        try:
            from docx import Document  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Failed to import python-docx. Ensure it is installed."
            ) from e
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == ".pdf":
        try:
            from pdfminer.high_level import extract_text  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Failed to import pdfminer.six. Ensure it is installed."
            ) from e
        text = extract_text(str(path))
        return text or ""
    # Fallback: plain text file
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Best-effort fallback if encoding is unknown
        return path.read_text(encoding="utf-8", errors="ignore")


def _read_text_input(
    input_path: Optional[str],
    url: Optional[str] = None,
    auth_user: Optional[str] = None,
    auth_pass: Optional[str] = None,
    login_url: Optional[str] = None,
    login_user_field: str = "username",
    login_pass_field: str = "password",
    login_extra: Optional[dict] = None,
) -> str:
    if input_path:
        return _read_file_text(Path(input_path))
    if url:
        from .netfetch import get_text_from_url  # lazy import to avoid extra deps if unused
        return get_text_from_url(
            url=url,
            auth_user=auth_user,
            auth_pass=auth_pass,
            login_url=login_url,
            login_user_field=login_user_field,
            login_pass_field=login_pass_field,
            login_extra=login_extra or {},
        )
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
    # URL fetching options (optional)
    parser.add_argument("--url", type=str, default=None, help="URL to fetch resume text from (http/https)")
    parser.add_argument("--auth-user", type=str, default=None, help="Username for HTTP auth or login form")
    parser.add_argument("--auth-pass", type=str, default=None, help="Password for HTTP auth or login form")
    parser.add_argument("--login-url", type=str, default=None, help="Optional login form URL to POST credentials before fetching --url")
    parser.add_argument("--login-user-field", type=str, default="username", help="Form field name for username (default: username)")
    parser.add_argument("--login-pass-field", type=str, default="password", help="Form field name for password (default: password)")
    parser.add_argument(
        "--login-extra",
        action="append",
        default=None,
        help="Additional form fields for login as key=value (repeatable)",
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

    # Parse extra login fields into a dict
    login_extra: Optional[dict] = None
    if args.login_extra:
        login_extra = {}
        for kv in args.login_extra:
            if "=" in kv:
                k, v = kv.split("=", 1)
                login_extra[k] = v

    text = _read_text_input(
        args.input,
        url=args.url,
        auth_user=args.auth_user,
        auth_pass=args.auth_pass,
        login_url=args.login_url,
        login_user_field=args.login_user_field,
        login_pass_field=args.login_pass_field,
        login_extra=login_extra,
    )

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
