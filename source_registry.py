#!/usr/bin/env python3
"""
Source registry for job ingestion.

The registry distinguishes between sources that can be ingested with a
reasonably compliant public API/feed and sources that should only be handled
through manual review or approved partner integrations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    homepage: str
    regions: List[str]
    supports_remote: bool
    supports_onsite: bool
    ingestion_mode: str
    enabled_by_default: bool
    automation_allowed: bool
    notes: str
    api_url: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


SOURCE_DEFINITIONS = [
    SourceDefinition(
        key="remotive",
        name="Remotive",
        homepage="https://remotive.com/remote-jobs",
        regions=["remote", "europe", "worldwide"],
        supports_remote=True,
        supports_onsite=False,
        ingestion_mode="public_api",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Enabled by default through the public Remotive jobs API.",
        api_url="https://remotive.com/api/remote-jobs",
        tags=["remote", "engineering", "api"],
    ),
    SourceDefinition(
        key="weworkremotely",
        name="We Work Remotely",
        homepage="https://weworkremotely.com/remote-jobs",
        regions=["remote", "worldwide"],
        supports_remote=True,
        supports_onsite=False,
        ingestion_mode="public_html",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Enabled with conservative HTML parsing of public job listings.",
        tags=["remote", "engineering", "html"],
    ),
    SourceDefinition(
        key="remoteok",
        name="Remote OK",
        homepage="https://remoteok.com/",
        regions=["remote", "worldwide"],
        supports_remote=True,
        supports_onsite=False,
        ingestion_mode="public_api",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Enabled by default through the public Remote OK API endpoint.",
        api_url="https://remoteok.com/api",
        tags=["remote", "engineering", "api"],
    ),
    SourceDefinition(
        key="linkedin",
        name="LinkedIn Jobs",
        homepage="https://www.linkedin.com/jobs/",
        regions=["global", "dubai", "poland", "netherlands"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="library",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Scraped via python-jobspy library. No API key needed.",
        tags=["enterprise", "jobspy"],
    ),
    SourceDefinition(
        key="indeed",
        name="Indeed",
        homepage="https://www.indeed.com/",
        regions=["global", "dubai", "poland", "netherlands"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="library",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Scraped via python-jobspy library. No API key needed.",
        tags=["enterprise", "jobspy"],
    ),
    SourceDefinition(
        key="glassdoor",
        name="Glassdoor",
        homepage="https://www.glassdoor.com/Job/",
        regions=["global", "dubai", "poland", "netherlands"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="library",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Scraped via python-jobspy library. No API key needed.",
        tags=["enterprise", "jobspy"],
    ),
    SourceDefinition(
        key="wellfound",
        name="Wellfound",
        homepage="https://wellfound.com/jobs",
        regions=["global", "remote"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="auth_required",
        enabled_by_default=False,
        automation_allowed=False,
        notes="Authentication is typically required, so this repo treats it as a future connector.",
        tags=["startup", "auth"],
    ),
    SourceDefinition(
        key="bayt",
        name="Bayt",
        homepage="https://www.bayt.com/en/",
        regions=["dubai", "uae", "middle-east"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="manual_review",
        enabled_by_default=False,
        automation_allowed=False,
        notes="Included as a regional source to review manually or via an approved feed.",
        tags=["dubai", "uae"],
    ),
    SourceDefinition(
        key="naukrigulf",
        name="NaukriGulf",
        homepage="https://www.naukrigulf.com/",
        regions=["dubai", "uae", "middle-east"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="manual_review",
        enabled_by_default=False,
        automation_allowed=False,
        notes="Included for source coverage, but not automated without an approved connector.",
        tags=["dubai", "uae"],
    ),
    SourceDefinition(
        key="nofluffjobs",
        name="No Fluff Jobs",
        homepage="https://nofluffjobs.com/",
        regions=["poland", "europe"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="manual_review",
        enabled_by_default=False,
        automation_allowed=False,
        notes="Regional board for Poland and Europe. Kept in the source catalog for manual sourcing.",
        tags=["poland", "europe"],
    ),
    SourceDefinition(
        key="justjoinit",
        name="Just Join IT",
        homepage="https://justjoin.it/",
        regions=["poland", "europe"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="manual_review",
        enabled_by_default=False,
        automation_allowed=False,
        notes="Regional engineering board retained for manual review or future approved ingestion.",
        tags=["poland", "europe"],
    ),
    SourceDefinition(
        key="himalayas",
        name="Himalayas",
        homepage="https://himalayas.app/jobs",
        regions=["remote", "worldwide"],
        supports_remote=True,
        supports_onsite=False,
        ingestion_mode="public_api",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Free JSON API with salary data, seniority levels, and timezone filters.",
        api_url="https://himalayas.app/jobs/api",
        tags=["remote", "api", "salary-data"],
    ),
    SourceDefinition(
        key="jobicy",
        name="Jobicy",
        homepage="https://jobicy.com/",
        regions=["remote", "worldwide"],
        supports_remote=True,
        supports_onsite=False,
        ingestion_mode="public_api",
        enabled_by_default=True,
        automation_allowed=True,
        notes="Free remote jobs API with salary ranges, job levels, and industry data.",
        api_url="https://jobicy.com/api/v2/remote-jobs",
        tags=["remote", "api", "salary-data"],
    ),
    SourceDefinition(
        key="adzuna",
        name="Adzuna",
        homepage="https://www.adzuna.com/",
        regions=["global", "europe", "us", "uk"],
        supports_remote=True,
        supports_onsite=True,
        ingestion_mode="api_key_required",
        enabled_by_default=False,
        automation_allowed=True,
        notes="Free-tier API covering 10+ countries. Requires ADZUNA_APP_ID and ADZUNA_APP_KEY env vars.",
        api_url="https://api.adzuna.com/v1/api/jobs",
        tags=["global", "api", "salary-estimates"],
    ),
]


def list_sources() -> list[dict]:
    return [source.to_dict() for source in SOURCE_DEFINITIONS]


def get_source(key: str) -> SourceDefinition | None:
    for source in SOURCE_DEFINITIONS:
        if source.key == key:
            return source
    return None


def list_enabled_sources() -> list[SourceDefinition]:
    return [
        source
        for source in SOURCE_DEFINITIONS
        if source.enabled_by_default and source.automation_allowed
    ]
