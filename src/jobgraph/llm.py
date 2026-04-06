from __future__ import annotations

import json
import subprocess
from typing import Any

import requests

from .models import CandidateProfile, JobMatch, LlmSettings
from .utils import extract_json_block


class OllamaClient:
    def __init__(self, settings: LlmSettings) -> None:
        self.settings = settings

    def _chat_via_http(self, messages: list[dict[str, str]]) -> str:
        response = requests.post(
            f"{self.settings.endpoint.rstrip('/')}/api/chat",
            json={
                "model": self.settings.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": self.settings.temperature},
            },
            timeout=self.settings.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("message", {}).get("content", "")

    def _chat_via_cli(self, messages: list[dict[str, str]]) -> str:
        prompt = "\n\n".join(f"{item['role'].upper()}:\n{item['content']}" for item in messages)
        result = subprocess.run(
            ["ollama", "run", self.settings.model, prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=self.settings.timeout_seconds,
        )
        return result.stdout

    def chat(self, messages: list[dict[str, str]]) -> str:
        try:
            return self._chat_via_http(messages)
        except Exception:
            return self._chat_via_cli(messages)


def build_tailoring_payload(profile: CandidateProfile, match: JobMatch) -> dict[str, Any]:
    return {
        "candidate": {
            "full_name": profile.full_name,
            "years_experience": profile.years_experience,
            "summary_seed": profile.summary_seed,
            "skills": profile.skills,
            "experience": [
                {
                    "company": item.company,
                    "title": item.title,
                    "start": item.start,
                    "end": item.end,
                    "bullets": item.bullets,
                }
                for item in profile.experience
            ],
            "projects": [
                {
                    "name": item.name,
                    "technologies": item.technologies,
                    "bullets": item.bullets,
                }
                for item in profile.projects
            ],
        },
        "job": {
            "company": match.job.company,
            "title": match.job.title,
            "location": match.job.location,
            "description": match.job.description_text[:9000],
            "apply_url": match.job.apply_url,
        },
        "match": {
            "skills": match.matched_skills,
            "experience_indices": match.matched_experience_indices,
            "project_indices": match.matched_project_indices,
        },
    }


def ask_for_resume_customization(client: OllamaClient, profile: CandidateProfile, match: JobMatch) -> dict[str, Any] | None:
    payload = build_tailoring_payload(profile, match)
    messages = [
        {
            "role": "system",
            "content": (
                "You tailor resumes for early-career candidates. "
                "Never invent employers, metrics, technologies, education, or achievements. "
                "The candidate has less than 1 year of experience. "
                "Return JSON only with keys: summary, cover_note, skills, experience_indices, project_indices."
            ),
        },
        {
            "role": "user",
            "content": (
                "Use only skills and indices that already exist in the input. "
                "Keep summary to 2 sentences, ATS-friendly, and aligned to the job description.\n\n"
                f"{json.dumps(payload, ensure_ascii=True)}"
            ),
        },
    ]
    raw = client.chat(messages)
    return extract_json_block(raw)
