from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclass
class ResumeData:
    name: Optional[str] = None
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experiences: List[str] = field(default_factory=list)


def parse_user_text(text: str) -> ResumeData:
    lines = [l.strip() for l in text.splitlines()]

    summary_parts: List[str] = []
    skills: List[str] = []
    experiences: List[str] = []

    in_skills = False

    for line in lines:
        if not line:
            continue
        lower = line.lower()

        # Detect start of skills section
        if lower.startswith("skills") or lower.startswith("skill:") or lower.startswith("skills:"):
            in_skills = True
            if ":" in line:
                after = line.split(":", 1)[1]
                skills.extend([s.strip() for s in after.split(",") if s.strip()])
            continue

        # If we're inside skills block, collect bullets or comma lists
        if in_skills and (line.startswith("-") or line.startswith("*") or "," in line):
            if line.startswith("-") or line.startswith("*"):
                item = line.lstrip("-* ").strip()
                if item:
                    skills.append(item)
            else:
                skills.extend([s.strip() for s in line.split(",") if s.strip()])
            continue

        # Experiences: treat bullet lines as experience items
        if line.startswith("-") or line.startswith("*"):
            item = line.lstrip("-* ").strip()
            if item:
                experiences.append(item)
            continue

        # Otherwise, treat as part of the free-form summary
        summary_parts.append(line)

    def dedup(seq: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return ResumeData(
        summary=" ".join(summary_parts).strip(),
        skills=dedup(skills),
        experiences=dedup(experiences),
    )


def render_resume(data: ResumeData, template_path: Path) -> str:
    template_dir = template_path.parent
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_path.name)
    return template.render(
        name=data.name,
        summary=data.summary,
        skills=data.skills,
        experiences=data.experiences,
    )


def generate_resume(user_text: str, name: Optional[str] = None, template_path: Optional[str] = None) -> str:
    data = parse_user_text(user_text)
    data.name = name

    if template_path is None:
        # project_root/templates/resume.md.j2 relative to this file
        template_path = Path(__file__).resolve().parents[2] / "templates" / "resume.md.j2"
    else:
        template_path = Path(template_path)

    return render_resume(data, template_path)
