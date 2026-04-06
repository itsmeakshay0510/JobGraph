from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from ..models import CompanySource, JobPosting, ScrapeSettings


class BaseScraper(ABC):
    def __init__(self, settings: ScrapeSettings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    @abstractmethod
    def fetch_jobs(self, source: CompanySource) -> list[JobPosting]:
        raise NotImplementedError


def build_scraper(source: CompanySource, settings: ScrapeSettings) -> BaseScraper:
    if source.source_type == "greenhouse":
        from .greenhouse import GreenhouseScraper

        return GreenhouseScraper(settings)
    if source.source_type == "lever":
        from .lever import LeverScraper

        return LeverScraper(settings)
    if source.source_type == "smartrecruiters":
        from .smartrecruiters import SmartRecruitersScraper

        return SmartRecruitersScraper(settings)
    if source.source_type == "generic_html":
        from .generic_html import GenericHtmlScraper

        return GenericHtmlScraper(settings)
    raise ValueError(f"Unsupported source type: {source.source_type}")
