#!/usr/bin/env python3
"""
Governed job ingestion with source registry support.
"""

from __future__ import annotations

import contextlib
import json
import os
import platform
import re
import subprocess
import time
from datetime import UTC, datetime, timedelta

import requests
from bs4 import BeautifulSoup

from jobintel import PROJECT_ROOT
from jobintel.source_registry import get_source, list_enabled_sources, list_sources

SCRAPED_JOBS_FILE = PROJECT_ROOT / "scraped_jobs.json"
LAST_SCRAPE_FILE = PROJECT_ROOT / "last_scrape.json"


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


def normalize_job(
    source_key: str,
    company: str,
    title: str,
    location: str,
    url: str,
    description: str,
    salary: str,
    job_type: str,
    date_posted: str,
    tags: list[str] | None = None,
) -> dict:
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


def scrape_jobspy_jobs(site_names, source_key_map):
    """Scrape LinkedIn, Indeed, and/or Glassdoor via python-jobspy."""
    jobs = []
    try:
        from jobspy import scrape_jobs as jobspy_scrape

        df = jobspy_scrape(
            site_name=site_names,
            search_term="software engineer",
            is_remote=True,
            results_wanted=30,
            hours_old=72,
        )

        for _, row in df.iterrows():
            site = str(row.get("site", "")).lower()
            source_key = source_key_map.get(site, site)

            company = str(row.get("company_name", "") or row.get("company", "") or "Unknown")
            title = str(row.get("title", ""))
            if not title:
                continue

            location = str(row.get("location", "") or "Remote")
            url = str(row.get("job_url", "") or row.get("link", "") or "")
            description = str(row.get("description", "") or "")[:1600]

            salary_min = row.get("min_amount") or row.get("salary_min")
            salary_max = row.get("max_amount") or row.get("salary_max")
            salary = "Not specified"
            if salary_min and salary_max:
                salary = f"${int(salary_min):,}-${int(salary_max):,}"
            elif salary_min:
                salary = f"${int(salary_min):,}+"

            date_posted = ""
            if row.get("date_posted"):
                with contextlib.suppress(Exception):
                    date_posted = str(row["date_posted"])

            jobs.append(
                normalize_job(
                    source_key,
                    company,
                    title,
                    location,
                    url,
                    description,
                    salary,
                    str(row.get("job_type", "") or "Full-time"),
                    date_posted,
                    [t for t in [site, "jobspy"] if t],
                )
            )
    except ImportError:
        pass
    except Exception:
        pass

    return jobs


def scrape_linkedin_jobs():
    return scrape_jobspy_jobs(["linkedin"], {"linkedin": "linkedin"})


def scrape_indeed_jobs():
    return scrape_jobspy_jobs(["indeed"], {"indeed": "indeed"})


def scrape_glassdoor_jobs():
    return scrape_jobspy_jobs(["glassdoor"], {"glassdoor": "glassdoor"})


def scrape_himalayas_jobs():
    jobs = []
    try:
        response = requests.get(
            "https://himalayas.app/jobs/api",
            params={"limit": 50, "offset": 0},
            headers={"User-Agent": "JobSystem/1.0"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("jobs", []):
            title = item.get("title", "")
            if not any(
                term in title.lower()
                for term in [
                    "engineer",
                    "developer",
                    "architect",
                    "devops",
                    "sre",
                    "backend",
                    "frontend",
                    "fullstack",
                    "full-stack",
                    "full stack",
                ]
            ):
                continue

            salary = "Not specified"
            if item.get("salary"):
                sal = item["salary"]
                s_min = sal.get("min")
                s_max = sal.get("max")
                currency = sal.get("currency", "USD")
                if s_min and s_max:
                    salary = f"{currency} {s_min:,}-{s_max:,}"
                elif s_min:
                    salary = f"{currency} {s_min:,}+"

            locations = item.get("locationRestrictions", [])
            location = ", ".join(locations) if locations else "Remote (Worldwide)"

            categories = item.get("categories", [])
            tags = (
                [c.get("name", "") for c in categories if isinstance(c, dict)] if isinstance(categories, list) else []
            )
            seniority = item.get("seniority", "")
            if seniority:
                tags.append(seniority)

            jobs.append(
                normalize_job(
                    "himalayas",
                    item.get("companyName", "Unknown"),
                    title,
                    location,
                    item.get("applicationLink", "") or item.get("url", ""),
                    (item.get("description", "") or "")[:1600],
                    salary,
                    "Full-time",
                    item.get("pubDate", "") or item.get("postedDate", ""),
                    tags,
                )
            )
    except Exception:
        pass

    return jobs


def scrape_jobicy_jobs():
    jobs = []
    try:
        response = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": 50, "tag": "engineer"},
            headers={"User-Agent": "JobSystem/1.0"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("jobs", []):
            title = item.get("jobTitle", "")
            if not any(
                term in title.lower()
                for term in [
                    "engineer",
                    "developer",
                    "architect",
                    "devops",
                    "sre",
                    "backend",
                    "frontend",
                    "fullstack",
                    "full-stack",
                    "full stack",
                ]
            ):
                continue

            salary = "Not specified"
            s_min = item.get("annualSalaryMin")
            s_max = item.get("annualSalaryMax")
            currency = item.get("salaryCurrency", "USD")
            if s_min and s_max:
                salary = f"{currency} {s_min}-{s_max}"
            elif s_min:
                salary = f"{currency} {s_min}+"

            job_level = item.get("jobLevel", "")
            tags = ["remote"]
            if job_level:
                tags.append(job_level)

            jobs.append(
                normalize_job(
                    "jobicy",
                    item.get("companyName", "Unknown"),
                    title,
                    item.get("jobGeo", "Remote"),
                    item.get("url", ""),
                    (item.get("jobDescription", "") or "")[:1600],
                    salary,
                    "Full-time",
                    item.get("pubDate", ""),
                    tags,
                )
            )
    except Exception:
        pass

    return jobs


def scrape_adzuna_jobs():
    """Only runs if ADZUNA_APP_ID and ADZUNA_APP_KEY env vars are set."""
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []

    jobs = []
    try:
        response = requests.get(
            "https://api.adzuna.com/v1/api/jobs/us/search/1",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": "software engineer",
                "where": "remote",
                "results_per_page": 30,
            },
            headers={"User-Agent": "JobSystem/1.0"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("results", []):
            title = item.get("title", "")
            salary = "Not specified"
            if item.get("salary_min") and item.get("salary_max"):
                salary = f"${int(item['salary_min']):,}-${int(item['salary_max']):,}"

            jobs.append(
                normalize_job(
                    "adzuna",
                    item.get("company", {}).get("display_name", "Unknown"),
                    title,
                    item.get("location", {}).get("display_name", "Remote"),
                    item.get("redirect_url", ""),
                    (item.get("description", "") or "")[:1600],
                    salary,
                    item.get("contract_type", "Full-time") or "Full-time",
                    item.get("created", ""),
                    ["adzuna"],
                )
            )
    except Exception:
        pass

    return jobs


def parse_salary_range(salary_str):
    """Parse salary string into (min_int, max_int) or (None, None)."""
    if not salary_str or salary_str == "Not specified":
        return None, None

    text = salary_str.replace(",", "").replace(" ", "").upper()

    hourly = re.search(r"\$?(\d+)\s*/\s*HR", text, re.IGNORECASE)
    if hourly:
        rate = int(hourly.group(1))
        return rate * 2080, rate * 2080

    numbers = re.findall(r"(\d+\.?\d*)\s*[Kk]", text)
    if numbers:
        nums = [int(float(n) * 1000) for n in numbers]
        if len(nums) >= 2:
            return min(nums), max(nums)
        return nums[0], nums[0]

    numbers = re.findall(r"(\d{4,})", text)
    if numbers:
        nums = [int(n) for n in numbers]
        if len(nums) >= 2:
            return min(nums), max(nums)
        return nums[0], nums[0]

    return None, None


def infer_experience_level(title, description=""):
    """Infer experience level from job title and description."""
    text = f"{title} {description}".lower()

    if any(k in text for k in ["principal", "staff", "distinguished", "vp ", "vice president", "director"]):
        return "lead"
    if any(k in text for k in ["senior", "sr.", "sr ", "lead", "manager", "head of"]):
        return "senior"
    if any(k in text for k in ["junior", "jr.", "jr ", "entry", "intern", "graduate", "new grad"]):
        return "junior"
    return "mid"


SCRAPERS = {
    "remotive": scrape_remotive_jobs,
    "weworkremotely": scrape_weworkremotely_jobs,
    "remoteok": scrape_remoteok_jobs,
    "linkedin": scrape_linkedin_jobs,
    "indeed": scrape_indeed_jobs,
    "glassdoor": scrape_glassdoor_jobs,
    "himalayas": scrape_himalayas_jobs,
    "jobicy": scrape_jobicy_jobs,
    "adzuna": scrape_adzuna_jobs,
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
            source_reports.append({"source_key": source.key, "status": "skipped", "reason": "No scraper registered"})
            continue

        try:
            jobs = scraper()
            all_new_jobs.extend(jobs)
            source_reports.append({"source_key": source.key, "status": "ok", "jobs_found": len(jobs)})
        except Exception as exc:
            source_reports.append({"source_key": source.key, "status": "error", "error": str(exc)})

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


def filter_jobs(
    jobs: list[dict],
    location: str | None = None,
    search_term: str | None = None,
    remote_policy: str | None = None,
    source_key: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    experience_level: str | None = None,
    skills: list[str] | None = None,
    date_posted: str | None = None,
    job_type: str | None = None,
) -> list[dict]:
    filtered = list(jobs)

    if location:
        filtered = [job for job in filtered if location.lower() in job.get("location", "").lower()]

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
        filtered = [job for job in filtered if remote_policy.lower() == job.get("remote_policy", "").lower()]

    if source_key:
        filtered = [job for job in filtered if source_key.lower() == job.get("source_key", "").lower()]

    if salary_min is not None or salary_max is not None:

        def salary_matches(job):
            s_min, s_max = parse_salary_range(job.get("salary", ""))
            if s_min is None and s_max is None:
                return False
            if salary_min is not None and (s_max or s_min or 0) < salary_min:
                return False
            return not (salary_max is not None and (s_min or s_max or 0) > salary_max)

        filtered = [job for job in filtered if salary_matches(job)]

    if experience_level:
        filtered = [
            job
            for job in filtered
            if infer_experience_level(job.get("title", ""), job.get("description", "")) == experience_level.lower()
        ]

    if skills:
        skills_lower = [s.lower() for s in skills]

        def has_skills(job):
            haystack = (
                job.get("title", "").lower()
                + " "
                + job.get("description", "").lower()
                + " "
                + " ".join(job.get("tags", [])).lower()
            )
            return any(skill in haystack for skill in skills_lower)

        filtered = [job for job in filtered if has_skills(job)]

    if date_posted:
        now = datetime.now(UTC)
        cutoffs = {
            "today": timedelta(days=1),
            "3days": timedelta(days=3),
            "week": timedelta(days=7),
            "month": timedelta(days=30),
        }
        cutoff = cutoffs.get(date_posted)
        if cutoff:
            threshold = now - cutoff

            def posted_after(job):
                dp = job.get("date_posted", "")
                if not dp:
                    return False
                try:
                    posted_dt = datetime.fromisoformat(dp.replace("Z", "+00:00"))
                    return posted_dt >= threshold
                except (ValueError, TypeError):
                    return False

            filtered = [job for job in filtered if posted_after(job)]

    if job_type:
        filtered = [job for job in filtered if job_type.lower() in job.get("job_type", "").lower()]

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
