from __future__ import annotations

from urllib.parse import urljoin

from ..models import CompanySource, JobPosting
from ..utils import html_to_text
from .base import BaseScraper


class GreenhouseScraper(BaseScraper):
    def fetch_jobs(self, source: CompanySource) -> list[JobPosting]:
        token = source.board_token or source.company_id
        if not token:
            raise ValueError(f"{source.company} is missing board_token for Greenhouse.")
        response = self.session.get(
            f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        jobs: list[JobPosting] = []
        for item in payload.get("jobs", []):
            html = item.get("content", "") or ""
            jobs.append(
                JobPosting(
                    company=source.company,
                    source_type="greenhouse",
                    job_id=str(item.get("id", "")),
                    title=item.get("title", ""),
                    location=item.get("location", {}).get("name", ""),
                    description_html=html,
                    description_text=html_to_text(html),
                    apply_url=urljoin(source.careers_url or "", item.get("absolute_url", "")),
                    posted_at=item.get("updated_at", ""),
                    department=", ".join(dept.get("name", "") for dept in item.get("departments", [])),
                    commitment="",
                    metadata={"internal_job_id": item.get("internal_job_id", "")},
                )
            )
        return jobs
