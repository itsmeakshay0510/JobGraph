from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..models import CompanySource, JobPosting
from ..utils import html_to_text
from .base import BaseScraper


class GenericHtmlScraper(BaseScraper):
    def fetch_jobs(self, source: CompanySource) -> list[JobPosting]:
        if not source.list_url:
            raise ValueError(f"{source.company} is missing list_url for generic_html scraping.")
        selectors = source.selectors
        list_response = self.session.get(
            source.list_url,
            headers=source.headers,
            timeout=self.settings.request_timeout_seconds,
        )
        list_response.raise_for_status()
        soup = BeautifulSoup(list_response.text, "html.parser")
        job_nodes = soup.select(selectors.get("job_selector", "a"))
        jobs: list[JobPosting] = []
        for index, node in enumerate(job_nodes, start=1):
            href = node.get("href", "")
            if not href:
                continue
            apply_url = urljoin(source.list_url, href)
            detail_response = self.session.get(
                apply_url,
                headers=source.headers,
                timeout=self.settings.request_timeout_seconds,
            )
            detail_response.raise_for_status()
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            title_selector = selectors.get("detail_title_selector", "title")
            description_selector = selectors.get("detail_description_selector", "body")
            location_selector = selectors.get("detail_location_selector", "")
            title_node = detail_soup.select_one(title_selector)
            location_node = detail_soup.select_one(location_selector) if location_selector else None
            description_node = detail_soup.select_one(description_selector)
            description_html = str(description_node) if description_node else detail_response.text
            jobs.append(
                JobPosting(
                    company=source.company,
                    source_type="generic_html",
                    job_id=f"generic-{index}",
                    title=title_node.get_text(" ", strip=True) if title_node else apply_url,
                    location=location_node.get_text(" ", strip=True) if location_node else "",
                    description_html=description_html,
                    description_text=html_to_text(description_html),
                    apply_url=apply_url,
                    posted_at="",
                    department="",
                    commitment="",
                    metadata={"selectors_used": selectors},
                )
            )
        return jobs
