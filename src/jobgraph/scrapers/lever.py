from __future__ import annotations

from ..models import CompanySource, JobPosting
from ..utils import html_to_text
from .base import BaseScraper


class LeverScraper(BaseScraper):
    def fetch_jobs(self, source: CompanySource) -> list[JobPosting]:
        token = source.company_id or source.board_token
        if not token:
            raise ValueError(f"{source.company} is missing company_id for Lever.")
        response = self.session.get(
            f"https://api.lever.co/v0/postings/{token}?mode=json",
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        jobs: list[JobPosting] = []
        for item in payload:
            html_parts = [
                item.get("description", ""),
                item.get("descriptionPlain", ""),
                item.get("additional", ""),
                item.get("additionalPlain", ""),
            ]
            html = "\n".join(part for part in html_parts if part)
            categories = item.get("categories", {})
            jobs.append(
                JobPosting(
                    company=source.company,
                    source_type="lever",
                    job_id=str(item.get("id", "")),
                    title=item.get("text", ""),
                    location=categories.get("location", ""),
                    description_html=html,
                    description_text=html_to_text(html),
                    apply_url=item.get("hostedUrl", "") or item.get("applyUrl", ""),
                    posted_at=str(item.get("createdAt", "")),
                    department=categories.get("team", ""),
                    commitment=categories.get("commitment", ""),
                    metadata={"workplace_type": categories.get("workplaceType", "")},
                )
            )
        return jobs
