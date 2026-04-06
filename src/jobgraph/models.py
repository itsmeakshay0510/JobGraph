from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ExperienceItem:
    company: str
    title: str
    start: str
    end: str
    location: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProjectItem:
    name: str
    technologies: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    link: str = ""


@dataclass(slots=True)
class EducationItem:
    school: str
    degree: str
    graduation: str
    location: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CandidateProfile:
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    years_experience: float = 0.8
    summary_seed: str = ""
    role_keywords: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    experience: list[ExperienceItem] = field(default_factory=list)
    projects: list[ProjectItem] = field(default_factory=list)
    education: list[EducationItem] = field(default_factory=list)

    @property
    def contact_line(self) -> str:
        parts = [self.email, self.phone, self.location]
        for value in (self.linkedin, self.github, self.portfolio):
            if value:
                parts.append(value)
        return " | ".join(part for part in parts if part)


@dataclass(slots=True)
class CompanySource:
    company: str
    source_type: str
    enabled: bool = True
    careers_url: str = ""
    board_token: str = ""
    company_id: str = ""
    list_url: str = ""
    detail_url_template: str = ""
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    selectors: dict[str, str] = field(default_factory=dict)
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LlmSettings:
    model: str = "qwen2.5:7b-instruct"
    endpoint: str = "http://127.0.0.1:11434"
    temperature: float = 0.2
    timeout_seconds: int = 180


@dataclass(slots=True)
class FilterSettings:
    max_experience_years: float = 1.0
    max_roles_per_run: int = 6
    preferred_role_keywords: list[str] = field(default_factory=list)
    blocked_title_keywords: list[str] = field(default_factory=list)
    entry_title_keywords: list[str] = field(default_factory=list)
    allow_unknown_experience: bool = False


@dataclass(slots=True)
class EmailSettings:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password_env: str = "JOBGRAPH_SMTP_PASSWORD"
    from_address: str = ""
    to_addresses: list[str] = field(default_factory=list)
    use_tls: bool = True


@dataclass(slots=True)
class StorageSettings:
    state_db_path: Path = Path("data/agent_state.sqlite3")
    output_dir: Path = Path("output")
    logs_dir: Path = Path("logs")


@dataclass(slots=True)
class ScrapeSettings:
    request_timeout_seconds: int = 30
    user_agent: str = "JobGraph/0.1"
    pause_seconds: float = 0.5
    verify_tls: bool = True


@dataclass(slots=True)
class AgentSettings:
    llm: LlmSettings = field(default_factory=LlmSettings)
    filters: FilterSettings = field(default_factory=FilterSettings)
    email: EmailSettings = field(default_factory=EmailSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    scrape: ScrapeSettings = field(default_factory=ScrapeSettings)


@dataclass(slots=True)
class JobPosting:
    company: str
    source_type: str
    job_id: str
    title: str
    location: str
    description_html: str
    description_text: str
    apply_url: str
    posted_at: str = ""
    department: str = ""
    commitment: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        safe_bits = [self.source_type, self.company, self.job_id or self.apply_url, self.title]
        return "|".join(bit.strip() for bit in safe_bits if bit)


@dataclass(slots=True)
class JobMatch:
    job: JobPosting
    matched_skills: list[str]
    matched_experience_indices: list[int]
    matched_project_indices: list[int]
    detected_experience_years: float | None
    explanation: str


@dataclass(slots=True)
class TailoredResume:
    company: str
    role: str
    summary: str
    skills: list[str]
    experience_indices: list[int]
    project_indices: list[int]
    cover_note: str
    resume_markdown: str
    created_at: datetime
    output_markdown_path: Path | None = None
    output_docx_path: Path | None = None
