from __future__ import annotations

from ..models import CompanySource, JobPosting
from ..utils import html_to_text
from .base import BaseScraper


class SmartRecruitersScraper(BaseScraper):
    def fetch_jobs(self, source: CompanySource) -> list[JobPosting]:
        company_id = source.company_id or source.board_token
        if not company_id:
            raise ValueError(f"{source.company} is missing company_id for SmartRecruiters.")
        response = self.session.get(
            f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings",
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        jobs: list[JobPosting] = []
        for item in payload.get("content", []):
            detail = self.session.get(
                f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings/{item['id']}",
                timeout=self.settings.request_timeout_seconds,
            )
            detail.raise_for_status()
            details = detail.json()
            sections = details.get("jobAd", {}).get("sections", {})
            html = "\n".join(
                section.get("text", "")
                for section in sections.values()
                if isinstance(section, dict)
            )
            location = details.get("location", {}) or item.get("location", {})
            location_text = ", ".join(
                part for part in [location.get("city"), location.get("region"), location.get("country")] if part
            )
            jobs.append(
                JobPosting(
                    company=source.company,
                    source_type="smartrecruiters",
                    job_id=str(item.get("id", "")),
                    title=item.get("name", ""),
                    location=location_text,
                    description_html=html,
                    description_text=html_to_text(html),
                    apply_url=details.get("applyUrl", item.get("ref", "")),
                    posted_at=item.get("releasedDate", ""),
                    department=details.get("department", ""),
                    commitment=details.get("typeOfEmployment", {}).get("label", ""),
                    metadata={"industry": details.get("industry", "")},
                )
            )
        return jobs
