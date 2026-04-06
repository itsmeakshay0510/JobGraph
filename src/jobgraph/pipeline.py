from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .config import load_companies, load_profile, load_settings
from .filters import match_job
from .llm import OllamaClient, ask_for_resume_customization
from .models import CandidateProfile, JobMatch, TailoredResume
from .notifications import send_digest_email
from .reporting import write_resume_tracker
from .renderer import build_resume_markdown, write_resume_files
from .scrapers import build_scraper
from .state import StateStore
from .utils import digest_text, ensure_dir


def configure_logging(logs_dir: Path) -> None:
    ensure_dir(logs_dir)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(logs_dir / "agent.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def _deterministic_summary(profile: CandidateProfile, match: JobMatch) -> str:
    matched_skills = ", ".join(match.matched_skills[:5])
    return (
        f"Early-career candidate with under {profile.years_experience:.1f} years of experience, "
        f"targeting {match.job.title} roles at {match.job.company}. "
        f"Highlights include {matched_skills or 'relevant technical skills'} aligned to the job description."
    )


def _deterministic_cover_note(match: JobMatch) -> str:
    return (
        f"Tailored for {match.job.company} - {match.job.title}. "
        f"Focus areas were selected from the job description without inventing any new experience."
    )


def tailor_resume(profile: CandidateProfile, match: JobMatch, llm_client: OllamaClient | None) -> TailoredResume:
    summary = _deterministic_summary(profile, match)
    cover_note = _deterministic_cover_note(match)
    skills = match.matched_skills[:12]
    experience_indices = match.matched_experience_indices[:3]
    project_indices = match.matched_project_indices[:2]

    if llm_client is not None:
        try:
            llm_result = ask_for_resume_customization(llm_client, profile, match) or {}
            summary = str(llm_result.get("summary", summary)).strip() or summary
            cover_note = str(llm_result.get("cover_note", cover_note)).strip() or cover_note
            llm_skills = [item for item in llm_result.get("skills", []) if item in profile.skills]
            if llm_skills:
                skills = llm_skills[:12]
            llm_experience_indices = [
                int(index)
                for index in llm_result.get("experience_indices", [])
                if isinstance(index, int) or str(index).isdigit()
            ]
            if llm_experience_indices:
                experience_indices = [index for index in llm_experience_indices if index < len(profile.experience)][:3]
            llm_project_indices = [
                int(index)
                for index in llm_result.get("project_indices", [])
                if isinstance(index, int) or str(index).isdigit()
            ]
            if llm_project_indices:
                project_indices = [index for index in llm_project_indices if index < len(profile.projects)][:2]
        except Exception as error:
            logging.warning("Falling back to deterministic resume tailoring for %s: %s", match.job.key, error)

    tailored = TailoredResume(
        company=match.job.company,
        role=match.job.title,
        summary=summary,
        skills=skills,
        experience_indices=experience_indices,
        project_indices=project_indices,
        cover_note=cover_note,
        resume_markdown="",
        created_at=datetime.now(),
    )
    tailored.resume_markdown = build_resume_markdown(profile, tailored)
    return tailored


def run_agent(
    project_root: Path,
    settings_path: Path,
    profile_path: Path,
    companies_path: Path,
    dry_run: bool = False,
) -> list[TailoredResume]:
    settings = load_settings(settings_path, project_root)
    configure_logging(settings.storage.logs_dir)
    profile = load_profile(profile_path)
    companies = [source for source in load_companies(companies_path) if source.enabled]
    ensure_dir(settings.storage.output_dir)
    state = StateStore(settings.storage.state_db_path)
    llm_client = OllamaClient(settings.llm)
    generated: list[TailoredResume] = []

    try:
        for source in companies:
            logging.info("Fetching jobs from %s (%s)", source.company, source.source_type)
            try:
                scraper = build_scraper(source, settings.scrape)
                jobs = scraper.fetch_jobs(source)
            except Exception as error:
                logging.exception("Unable to fetch jobs from %s: %s", source.company, error)
                continue

            matches: list[JobMatch] = []
            for job in jobs:
                description_hash = digest_text(job.description_text)
                if state.has_processed(job, description_hash):
                    continue
                match = match_job(job, profile, settings.filters)
                if match is not None:
                    matches.append(match)

            matches = matches[: settings.filters.max_roles_per_run]
            for match in matches:
                tailored = tailor_resume(profile, match, llm_client)
                if not dry_run:
                    tailored = write_resume_files(profile, tailored, settings.storage.output_dir)
                    state.mark_processed(
                        match.job,
                        digest_text(match.job.description_text),
                        str(tailored.output_markdown_path or ""),
                        str(tailored.output_docx_path or ""),
                    )
                generated.append(tailored)
                logging.info("Prepared resume for %s - %s", match.job.company, match.job.title)

        if not dry_run:
            send_digest_email(settings.email, generated)
            report_path = write_resume_tracker(state.fetch_processed_jobs(), settings.storage.output_dir)
            logging.info("Updated resume tracker workbook: %s", report_path)
        return generated
    finally:
        state.close()
        logging.shutdown()
