from __future__ import annotations

import re

from .models import CandidateProfile, FilterSettings, JobMatch, JobPosting
from .utils import normalize_whitespace, token_set

EXPERIENCE_PATTERNS = [
    re.compile(r"(\d+)\s*(?:\+|plus)?\s*(?:to\s*\d+\s*)?(?:years|year|yrs|yr)\s+of\s+experience", re.IGNORECASE),
    re.compile(r"minimum\s+of\s+(\d+)\s*(?:years|year|yrs|yr)", re.IGNORECASE),
    re.compile(r"(\d+)\s*-\s*(\d+)\s*(?:years|year|yrs|yr)\s+experience", re.IGNORECASE),
    re.compile(r"(\d+)\+?\s*(?:years|year|yrs|yr)\s+experience", re.IGNORECASE),
    re.compile(r"at\s+least\s+(\d+)\s*(?:years|year|yrs|yr)", re.IGNORECASE),
    re.compile(r"(\d+)\+?\s*yoe", re.IGNORECASE),
    re.compile(r"(\d+)\s*-\s*(\d+)\s*yoe", re.IGNORECASE),
]


def detect_required_years(text: str) -> float | None:
    cleaned = normalize_whitespace(text)
    years: list[float] = []
    for pattern in EXPERIENCE_PATTERNS:
        for match in pattern.finditer(cleaned):
            if len(match.groups()) == 1:
                years.append(float(match.group(1)))
            elif len(match.groups()) >= 2:
                years.append(float(match.group(1)))
    if not years:
        return None
    return min(years)


def _contains_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _rank_skills(job: JobPosting, profile: CandidateProfile) -> list[str]:
    description = job.description_text.lower()
    matches = [skill for skill in profile.skills if skill.lower() in description]
    remainder = [skill for skill in profile.skills if skill not in matches]
    return matches + remainder


def _rank_experience(job: JobPosting, profile: CandidateProfile) -> list[int]:
    job_tokens = token_set(job.title + " " + job.description_text)
    scored: list[tuple[int, int]] = []
    for index, item in enumerate(profile.experience):
        text = " ".join(item.bullets + [item.title, item.company])
        score = len(job_tokens.intersection(token_set(text)))
        scored.append((score, index))
    scored.sort(reverse=True)
    return [index for score, index in scored if score > 0] or [index for _, index in scored[:2]]


def _rank_projects(job: JobPosting, profile: CandidateProfile) -> list[int]:
    job_tokens = token_set(job.title + " " + job.description_text)
    scored: list[tuple[int, int]] = []
    for index, project in enumerate(profile.projects):
        text = " ".join(project.bullets + project.technologies + [project.name])
        score = len(job_tokens.intersection(token_set(text)))
        scored.append((score, index))
    scored.sort(reverse=True)
    return [index for score, index in scored if score > 0] or [index for _, index in scored[:2]]


def match_job(job: JobPosting, profile: CandidateProfile, settings: FilterSettings) -> JobMatch | None:
    title = job.title.lower()
    description = job.description_text.lower()
    default_blocked_keywords = [
        "account executive",
        "sales",
        "marketing",
        "customer success",
        "support",
        "recruiter",
        "talent",
        "finance",
        "legal",
        "attorney",
        "people",
        "hr",
        "designer",
        "product manager",
        "senior",
        "staff",
        "principal",
        "lead",
        "manager",
        "director",
        "head",
        "vp",
        "architect",
    ]
    blocked_keywords = list(dict.fromkeys(default_blocked_keywords + settings.blocked_title_keywords))
    default_entry_keywords = [
        "junior",
        "entry",
        "graduate",
        "new grad",
        "associate",
        "analyst",
        "trainee",
        "apprentice",
        "intern",
    ]
    entry_keywords = list(dict.fromkeys(default_entry_keywords + settings.entry_title_keywords))
    if _contains_keyword(title, blocked_keywords):
        return None

    detected_years = detect_required_years(job.title + " " + job.description_text)
    if detected_years is not None and detected_years > settings.max_experience_years:
        return None

    preferred_keywords = list(dict.fromkeys((settings.preferred_role_keywords or []) + profile.role_keywords))
    if preferred_keywords and not _contains_keyword(title, preferred_keywords):
        return None

    entry_signal = _contains_keyword(title + " " + description, entry_keywords)
    if detected_years is None and not entry_signal:
        if not settings.allow_unknown_experience:
            return None
        softer_entry_phrases = [
            "recent graduate",
            "early career",
            "campus recruiting",
            "university recruiting",
            "bachelor",
            "graduate program",
        ]
        if not _contains_keyword(description, softer_entry_phrases):
            return None

    ranked_skills = _rank_skills(job, profile)
    ranked_experience = _rank_experience(job, profile)
    ranked_projects = _rank_projects(job, profile)
    explanation = (
        f"Matched as an early-career role. Detected required experience: "
        f"{detected_years if detected_years is not None else 'unknown'} years."
    )
    return JobMatch(
        job=job,
        matched_skills=ranked_skills[:10],
        matched_experience_indices=ranked_experience[:3],
        matched_project_indices=ranked_projects[:2],
        detected_experience_years=detected_years,
        explanation=explanation,
    )
