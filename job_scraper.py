#!/usr/bin/env python3
"""
Governed job ingestion with source registry support.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from source_registry import get_source, list_enabled_sources, list_sources


BASE_DIR = Path(__file__).parent
SCRAPED_JOBS_FILE = BASE_DIR / "scraped_jobs.json"
LAST_SCRAPE_FILE = BASE_DIR / "last_scrape.json"


def send_notification(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return

    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "{title}" sound name "Glass"'],
        capture_output=True,
        check=False,
    )


def load_scraped_jobs() -> list[dict]:
    if SCRAPED_JOBS_FILE.exists():
        return json.loads(SCRAPED_JOBS_FILE.read_text(encoding="utf-8"))
    return []


def save_scraped_jobs(jobs: list[dict]) -> None:
    SCRAPED_JOBS_FILE.write_text(json.dumps(jobs, indent=2), encoding="utf-8")


def load_last_scrape() -> dict:
    if LAST_SCRAPE_FILE.exists():
        return json.loads(LAST_SCRAPE_FILE.read_text(encoding="utf-8"))
    return {"last_scrape": None, "total_jobs": 0, "sources": []}


def save_last_scrape(report: dict) -> None:
    LAST_SCRAPE_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")


def generate_job_id(company: str, title: str, location: str, source_key: str) -> str:
    text = f"{source_key}_{company}_{title}_{location}".lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def normalize_location(raw_location: str, default_location: str = "Remote") -> tuple[str, str]:
    raw = (raw_location or "").strip()
    lowered = raw.lower()

    if not raw:
        return default_location, "remote"
    if any(term in lowered for term in ["remote", "worldwide", "anywhere"]):
        return raw or "Remote", "remote"
    if any(term in lowered for term in ["hybrid"]):
        return raw, "hybrid"
    return raw, "onsite"


def normalize_job(source_key: str, company: str, title: str, location: str, url: str, description: str, salary: str, job_type: str, date_posted: str, tags: list[str] | None = None) -> dict:
    source = get_source(source_key)
    normalized_location, remote_policy = normalize_location(location)
    tags = tags or []

    return {
        "id": generate_job_id(company, title, normalized_location, source_key),
        "company": company,
        "title": title,
        "location": normalized_location,
        "remote_policy": remote_policy,
        "url": url,
        "source": source.name if source else source_key,
        "source_key": source_key,
        "description": (description or "").strip(),
        "salary": salary or "Not specified",
        "job_type": job_type or "Not specified",
        "date_posted": date_posted or datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "date_scraped": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "tags": tags,
        "compliance": {
            "automation_allowed": bool(source and source.automation_allowed),
            "ingestion_mode": source.ingestion_mode if source else "unknown",
            "notes": source.notes if source else "",
        },
    }


def scrape_remotive_jobs() -> list[dict]:
    jobs: list[dict] = []
    response = requests.get(
        "https://remotive.com/api/remote-jobs?category=software-dev",
        headers={"User-Agent": "JobSystem/1.0"},
        timeout=20,
    )
    response.raise_for_status()

    for item in response.json().get("jobs", [])[:80]:
        title = item.get("title", "")
        if not any(term in title.lower() for term in ["engineer", "developer", "architect"]):
            continue

        location = item.get("candidate_required_location", "Remote")
        jobs.append(
            normalize_job(
                "remotive",
                item.get("company_name", "Unknown"),
                title,
                location,
                item.get("url", ""),
                re.sub(r"<[^>]+>", " ", item.get("description", ""))[:1600],
                item.get("salary", "Not specified"),
                item.get("job_type", "Full-time"),
                item.get("publication_date", ""),
                item.get("tags", []),
            )
        )

    return jobs


def scrape_weworkremotely_jobs() -> list[dict]:
    jobs: list[dict] = []
    response = requests.get(
        "https://weworkremotely.com/categories/remote-programming-jobs",
        headers={"User-Agent": "JobSystem/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    for listing in soup.select("section.jobs li:not(.view-all)")[:60]:
        link = listing.find("a")
        title_element = listing.select_one(".title")
        company_element = listing.select_one(".company")
        region_element = listing.select_one(".region")

        if not link or not title_element or not company_element:
            continue

        title = title_element.get_text(" ", strip=True)
        if not any(term in title.lower() for term in ["engineer", "developer", "architect"]):
            continue

        location = region_element.get_text(" ", strip=True) if region_element else "Remote"
        url = link.get("href", "")
        if url and not url.startswith("http"):
            url = f"https://weworkremotely.com{url}"

        jobs.append(
            normalize_job(
                "weworkremotely",
                company_element.get_text(" ", strip=True),
                title,
                location or "Remote (Worldwide)",
                url,
                "Public We Work Remotely listing.",
                "Not specified",
                "Not specified",
                datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                ["remote", "programming"],
            )
        )

    return jobs


def scrape_remoteok_jobs() -> list[dict]:
    jobs: list[dict] = []
    response = requests.get(
        "https://remoteok.com/api",
        headers={"User-Agent": "JobSystem/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    for item in payload[1:80]:
        title = item.get("position", "")
        if not any(term in title.lower() for term in ["engineer", "developer", "architect"]):
            continue

        location = "Remote"
        if item.get("location"):
            location = item.get("location")

        salary = "Not specified"
        if item.get("salary_min") and item.get("salary_max"):
            salary = f"${item['salary_min']}-${item['salary_max']}"

        jobs.append(
            normalize_job(
                "remoteok",
                item.get("company", "Unknown"),
                title,
                location,
                item.get("url", ""),
                re.sub(r"<[^>]+>", " ", item.get("description", ""))[:1600],
                salary,
                "Full-time",
                item.get("date", ""),
                item.get("tags", []),
            )
        )

    return jobs


SCRAPERS = {
    "remotive": scrape_remotive_jobs,
    "weworkremotely": scrape_weworkremotely_jobs,
    "remoteok": scrape_remoteok_jobs,
}


def merge_jobs(existing_jobs: list[dict], new_jobs: list[dict]) -> tuple[list[dict], int]:
    deduped = {job["id"]: job for job in existing_jobs}
    added_count = 0

    for job in new_jobs:
        if job["id"] not in deduped:
            added_count += 1
        deduped[job["id"]] = job

    merged = list(deduped.values())
    merged.sort(key=lambda item: item.get("date_scraped", ""), reverse=True)
    return merged, added_count


def scrape_all_jobs(notify: bool = True) -> tuple[list[dict], dict]:
    existing_jobs = load_scraped_jobs()
    all_new_jobs: list[dict] = []
    source_reports = []
    started = time.time()

    for source in list_enabled_sources():
        scraper = SCRAPERS.get(source.key)
        if not scraper:
            source_reports.append(
                {"source_key": source.key, "status": "skipped", "reason": "No scraper registered"}
            )
            continue

        try:
            jobs = scraper()
            all_new_jobs.extend(jobs)
            source_reports.append(
                {"source_key": source.key, "status": "ok", "jobs_found": len(jobs)}
            )
        except Exception as exc:
            source_reports.append(
                {"source_key": source.key, "status": "error", "error": str(exc)}
            )

        time.sleep(1)

    merged_jobs, new_count = merge_jobs(existing_jobs, all_new_jobs)
    save_scraped_jobs(merged_jobs)

    report = {
        "last_scrape": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "total_jobs": len(merged_jobs),
        "new_jobs": new_count,
        "elapsed_seconds": round(time.time() - started, 2),
        "sources": source_reports,
        "catalog": list_sources(),
    }
    save_last_scrape(report)

    if notify and new_count > 0:
        send_notification(
            f"{new_count} new jobs ingested",
            f"The system added {new_count} new jobs from enabled sources.",
        )

    return merged_jobs, report


def filter_jobs(jobs: list[dict], location: str | None = None, search_term: str | None = None, remote_policy: str | None = None, source_key: str | None = None) -> list[dict]:
    filtered = list(jobs)

    if location:
        filtered = [
            job for job in filtered
            if location.lower() in job.get("location", "").lower()
        ]

    if search_term:
        needle = search_term.lower()
        filtered = [
            job
            for job in filtered
            if needle in job.get("title", "").lower()
            or needle in job.get("company", "").lower()
            or needle in job.get("description", "").lower()
            or needle in " ".join(job.get("tags", [])).lower()
        ]

    if remote_policy:
        filtered = [
            job for job in filtered
            if remote_policy.lower() == job.get("remote_policy", "").lower()
        ]

    if source_key:
        filtered = [
            job for job in filtered
            if source_key.lower() == job.get("source_key", "").lower()
        ]

    return filtered


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scrape":
        jobs, report = scrape_all_jobs(notify=False)
        print(f"Scraped total jobs: {len(jobs)}")
        print(json.dumps(report, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "list":
        for job in load_scraped_jobs()[:30]:
            print(f"{job['company']} | {job['title']} | {job['location']} | {job['source']}")
    else:
        print("Usage:")
        print("  python3 job_scraper.py scrape")
        print("  python3 job_scraper.py list")
