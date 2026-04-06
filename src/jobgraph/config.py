from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml

from .models import (
    AgentSettings,
    CandidateProfile,
    CompanySource,
    EducationItem,
    EmailSettings,
    ExperienceItem,
    FilterSettings,
    LlmSettings,
    ProjectItem,
    ScrapeSettings,
    StorageSettings,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a top-level mapping.")
    return data


def _expand_path(path_text: str | None, project_root: Path) -> Path:
    if not path_text:
        return project_root
    path = Path(path_text)
    return path if path.is_absolute() else project_root / path


def load_profile(path: Path) -> CandidateProfile:
    raw = _load_yaml(path)
    experience = [
        ExperienceItem(
            company=item["company"],
            title=item["title"],
            start=item["start"],
            end=item["end"],
            location=item.get("location", ""),
            bullets=list(item.get("bullets", [])),
        )
        for item in raw.get("experience", [])
    ]
    projects = [
        ProjectItem(
            name=item["name"],
            technologies=list(item.get("technologies", [])),
            bullets=list(item.get("bullets", [])),
            link=item.get("link", ""),
        )
        for item in raw.get("projects", [])
    ]
    education = [
        EducationItem(
            school=item["school"],
            degree=item["degree"],
            graduation=item["graduation"],
            location=item.get("location", ""),
            bullets=list(item.get("bullets", [])),
        )
        for item in raw.get("education", [])
    ]
    return CandidateProfile(
        full_name=raw["full_name"],
        email=raw["email"],
        phone=raw["phone"],
        location=raw["location"],
        linkedin=raw.get("linkedin", ""),
        github=raw.get("github", ""),
        portfolio=raw.get("portfolio", ""),
        years_experience=float(raw.get("years_experience", 0.8)),
        summary_seed=raw.get("summary_seed", ""),
        role_keywords=list(raw.get("role_keywords", [])),
        skills=list(raw.get("skills", [])),
        experience=experience,
        projects=projects,
        education=education,
    )


def _dataclass_kwargs(cls: type[Any], raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {field.name for field in fields(cls)}
    return {name: value for name, value in raw.items() if name in allowed}


def load_settings(path: Path, project_root: Path) -> AgentSettings:
    raw = _load_yaml(path)
    llm = LlmSettings(**_dataclass_kwargs(LlmSettings, raw.get("llm", {})))
    filters = FilterSettings(**_dataclass_kwargs(FilterSettings, raw.get("filters", {})))
    email = EmailSettings(**_dataclass_kwargs(EmailSettings, raw.get("email", {})))
    storage_raw = raw.get("storage", {})
    storage = StorageSettings(
        state_db_path=_expand_path(storage_raw.get("state_db_path", "data/agent_state.sqlite3"), project_root),
        output_dir=_expand_path(storage_raw.get("output_dir", "output"), project_root),
        logs_dir=_expand_path(storage_raw.get("logs_dir", "logs"), project_root),
    )
    scrape = ScrapeSettings(**_dataclass_kwargs(ScrapeSettings, raw.get("scrape", {})))
    return AgentSettings(llm=llm, filters=filters, email=email, storage=storage, scrape=scrape)


def load_companies(path: Path) -> list[CompanySource]:
    raw = _load_yaml(path)
    companies: list[CompanySource] = []
    for item in raw.get("companies", []):
        known = {
            "company",
            "source_type",
            "enabled",
            "careers_url",
            "board_token",
            "company_id",
            "list_url",
            "detail_url_template",
            "method",
            "headers",
            "selectors",
            "notes",
        }
        extra = {key: value for key, value in item.items() if key not in known}
        companies.append(
            CompanySource(
                company=item["company"],
                source_type=item["source_type"],
                enabled=bool(item.get("enabled", True)),
                careers_url=item.get("careers_url", ""),
                board_token=item.get("board_token", ""),
                company_id=item.get("company_id", ""),
                list_url=item.get("list_url", ""),
                detail_url_template=item.get("detail_url_template", ""),
                method=item.get("method", "GET"),
                headers=dict(item.get("headers", {})),
                selectors=dict(item.get("selectors", {})),
                notes=item.get("notes", ""),
                extra=extra,
            )
        )
    return companies
