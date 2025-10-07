from __future__ import annotations

import io
import mimetypes
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup


def _infer_mime(url: str, headers: Dict[str, str]) -> str:
    ctype = headers.get("Content-Type", "").split(";")[0].strip().lower()
    if ctype:
        return ctype
    guess, _ = mimetypes.guess_type(url)
    return (guess or "text/plain").lower()


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    # Normalize whitespace lines
    lines = [ln.strip() for ln in text.splitlines()]
    # Collapse multiple blank lines
    out = []
    prev_blank = False
    for ln in lines:
        is_blank = len(ln) == 0
        if is_blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = is_blank
    return "\n".join(out).strip()


def _extract_text_from_bytes(url: str, content: bytes, content_type: str) -> str:
    ct = content_type
    if ct in ("application/pdf",):
        from pdfminer.high_level import extract_text  # lazy import
        return extract_text(io.BytesIO(content)) or ""
    if ct in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or url.lower().endswith(".docx"):
        from docx import Document  # type: ignore
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    if ct.startswith("text/") or ct in ("application/xhtml+xml", "application/xml"):
        try:
            # Decode as UTF-8 with errors ignored
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = content.decode(errors="ignore")
        if ct in ("text/html", "application/xhtml+xml"):
            return _html_to_text(text)
        return text
    # Fallback: attempt UTF-8 decode and treat as text
    try:
        return content.decode("utf-8")
    except Exception:
        return content.decode("utf-8", errors="ignore")


def _perform_form_login(
    session: requests.Session,
    login_url: str,
    user: str,
    password: str,
    user_field: str,
    pass_field: str,
    extra: Optional[Dict[str, str]] = None,
) -> None:
    payload = {user_field: user, pass_field: password}
    if extra:
        payload.update(extra)
    # Do not print or log secrets
    resp = session.post(login_url, data=payload, allow_redirects=True, timeout=30)
    resp.raise_for_status()


def get_text_from_url(
    url: str,
    auth_user: Optional[str] = None,
    auth_pass: Optional[str] = None,
    login_url: Optional[str] = None,
    login_user_field: str = "username",
    login_pass_field: str = "password",
    login_extra: Optional[Dict[str, str]] = None,
) -> str:
    """
    Fetches text content from a URL using optional authentication.

    Supports:
    - Direct GET with optional HTTP Basic auth (auth_user/auth_pass)
    - Optional form-based login (login_url) before fetching the URL, posting user/pass
      plus any extra form fields. Cookies are preserved via the session.
    - Extracts text from HTML, PDF, and DOCX content types.
    """
    session = requests.Session()

    # If form login is provided, perform it first
    if login_url and auth_user and auth_pass:
        _perform_form_login(
            session,
            login_url,
            auth_user,
            auth_pass,
            login_user_field,
            login_pass_field,
            extra=login_extra,
        )

    auth = (auth_user, auth_pass) if (auth_user and auth_pass and not login_url) else None

    resp = session.get(url, auth=auth, allow_redirects=True, timeout=60)
    resp.raise_for_status()

    content_type = _infer_mime(url, resp.headers)
    return _extract_text_from_bytes(url, resp.content, content_type)
