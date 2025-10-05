import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class UserProfile:
    first_name: str
    last_name: str
    phone: str
    email: str
    # Minimal structured buckets; free-form raw_text is also provided to the model
    experiences: List[Dict[str, str]]  # each: { employer, duration, role?, highlights? }
    skills: List[str]
    tools: List[str]
    english_level: Optional[str]
    languages: List[str]


def _prompt(prompt_text: str) -> str:
    # Simple console prompt helper (non-empty)
    while True:
        val = input(prompt_text).strip()
        if val:
            return val


def _prompt_list(prompt_text: str) -> List[str]:
    raw = _prompt(prompt_text + " (comma-separated): ")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _prompt_experiences() -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    print("Enter work experiences. Leave employer empty to finish.")
    while True:
        employer = input("Employer organization: ").strip()
        if not employer:
            break
        duration = _prompt("Length of employment with this organization (e.g., 2019–2022 or 18 months): ")
        role = input("Role/Title (optional): ").strip()
        highlights = input("Key achievements/responsibilities (optional, semicolon-separated): ").strip()
        items.append({
            "employer": employer,
            "duration": duration,
            "role": role,
            "highlights": highlights,
        })
    if not items:
        # Require at least one item
        print("At least one experience is required.")
        return _prompt_experiences()
    return items


def collect_user_profile(
    raw_text: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
) -> UserProfile:
    # Always prompt for any missing required fields
    if not first_name:
        first_name = _prompt("First name: ")
    if not last_name:
        last_name = _prompt("Last name: ")
    if not phone:
        phone = _prompt("Phone number: ")
    if not email:
        email = _prompt("Email address: ")

    print("\nProvide professional details. Press Enter to skip optional prompts; you can refine later.")
    experiences = _prompt_experiences()

    skills = _prompt_list("Skills you possess")
    tools = _prompt_list("Software products/tools you can work with")
    english_level = input("English level (e.g., A2/B1/B2/C1/C2 or native): ").strip() or None
    languages = _prompt_list("Other languages you speak (exclude English if already listed)")

    return UserProfile(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        experiences=experiences,
        skills=skills,
        tools=tools,
        english_level=english_level,
        languages=languages,
    )


def _build_messages(profile: UserProfile, raw_text: str) -> List[Dict[str, str]]:
    # System prompt focuses on producing a clear, concise Markdown resume
    system = (
        "You are a resume writer. Create a concise, professional resume in Markdown. "
        "Use clear section headers. Summarize impact with strong verbs and measurable outcomes when available. "
        "Include contact info at top. Keep it to 1 page if possible."
    )

    structured = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "phone": profile.phone,
        "email": profile.email,
        "experiences": profile.experiences,
        "skills": profile.skills,
        "tools": profile.tools,
        "english_level": profile.english_level,
        "languages": profile.languages,
        "user_raw_text": raw_text,
    }

    user = (
        "Please generate a resume that accurately reflects the following structured information and the "
        "additional free-form text. Output must be valid Markdown."
        "\n\nStructured JSON:\n" + json.dumps(structured, ensure_ascii=False, indent=2)
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def generate_resume_with_openai(profile: UserProfile, raw_text: str, model: str = "gpt-4o-mini") -> str:
    messages = _build_messages(profile, raw_text)

    # Prefer the newer client API if available, fallback to legacy
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.3,
        )
        content = resp.choices[0].message.content  # type: ignore[attr-defined]
        return content or ""
    except Exception:
        # Legacy fallback (older openai package)
        try:
            import openai  # type: ignore
            # API key is taken from OPENAI_API_KEY env var by the SDK automatically; ensure not to log it.
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.3,
            )
            return completion.choices[0].message["content"]  # type: ignore[index]
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"OpenAI request failed: {e}")
