#!/usr/bin/env python3
"""Run the full daily scrape, match, tailor, and validation pipeline."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from jobintel import DATA_DIR
from jobintel.job_scraper import load_last_scrape, load_scraped_jobs, scrape_all_jobs
from jobintel.resume_pipeline import load_resume_profile, match_jobs_to_profile, tailor_resume_for_job

REPORTS_DIR = DATA_DIR / "reports"
TARGET_INCLUDE_TERMS = [
    "software engineer",
    "software developer",
    "backend",
    "back-end",
    "full stack",
    "full-stack",
    "platform engineer",
    "platform",
    "devops",
    "sre",
    "site reliability",
    "node",
    "node.js",
    "typescript",
    "javascript",
    "react",
    "next.js",
    "aws",
    "cloud",
    "api",
    "architect",
]
TARGET_EXCLUDE_TERMS = [
    "sales",
    "medical",
    "liaison",
    "recruiter",
    "talent",
    "account executive",
    "customer success",
    "support engineer",
    "manual qa",
    "quality assurance",
    "ios",
    "android",
    "machine learning",
    "verification",
    "data scientist",
]


def _same_day(value: str, target_day: str) -> bool:
    if not value:
        return False
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat() == target_day
    except ValueError:
        return value.startswith(target_day)


def _build_report_markdown(report: dict) -> str:
    lines = [
        "# Today Pipeline Report",
        "",
        f"- Run date: `{report['run_date']}`",
        f"- Resume profile: `{report['profile_name']}`",
        f"- Sources processed: `{report['source_summary']['processed']}`",
        f"- Source timeouts: `{report['source_summary']['timeouts']}`",
        f"- Total jobs in database: `{report['job_summary']['total_jobs']}`",
        f"- Jobs posted today: `{report['job_summary']['posted_today']}`",
        f"- Jobs scraped today: `{report['job_summary']['scraped_today']}`",
        f"- Jobs processed for tailoring: `{report['job_summary']['processed_for_tailoring']}`",
        f"- Min match score: `{report['job_summary']['minimum_match_score']}`",
        f"- Resumes generated: `{report['artifact_summary']['generated']}`",
        f"- Passed validation: `{report['artifact_summary']['passed']}`",
        f"- Needs review: `{report['artifact_summary']['needs_review']}`",
        "",
        "## Tasks",
        "",
    ]

    for task in report["tasks"]:
        lines.append(f"- {task['name']}: `{task['status']}`")
        if task.get("details"):
            lines.append(f"  - {task['details']}")

    lines.extend(
        [
            "",
            "## Source Results",
            "",
        ]
    )

    for source in report["source_results"]:
        line = (
            f"- `{source['source_key']}`: `{source['status']}`"
            f", jobs=`{source.get('jobs_found', 0)}`, elapsed=`{source.get('elapsed_seconds', 0)}s`"
        )
        if source.get("error"):
            line += f", error=`{source['error']}`"
        lines.append(line)

    lines.extend(["", "## Tailored Jobs", ""])
    for artifact in report["artifacts"]:
        lines.append(
            f"- `{artifact['title']}` at `{artifact['company']}`: "
            f"match=`{artifact['match_score']}`, validation=`{artifact['validation_score']}`, "
            f"fit=`{artifact['fit_label']}`, pdf=`{artifact['pdf_filename']}`"
        )

    if report["artifact_summary"]["needs_review"]:
        lines.extend(["", "## Needs Review", ""])
        for artifact in report["artifacts"]:
            if artifact["passed"]:
                continue
            warnings = "; ".join(artifact.get("warnings", [])[:2]) or "Validation score below threshold."
            lines.append(f"- `{artifact['title']}`: {warnings}")

    return "\n".join(lines) + "\n"


def run_today_tasks(
    max_jobs: int | None = None,
    min_validation_score: int = 70,
    allow_scraped_today_fallback: bool = False,
    min_match_score: int = 75,
    skip_scrape: bool = False,
) -> dict:
    profile = load_resume_profile()
    if not profile:
        raise SystemExit("No resume profile loaded. Upload a resume before running today tasks.")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(UTC).date().isoformat()

    tasks = [{"name": "load_resume_profile", "status": "completed", "details": profile.get("source_filename", "")}]

    if skip_scrape:
        jobs = load_scraped_jobs()
        scrape_report = load_last_scrape()
        tasks.append(
            {
                "name": "load_existing_scrape_snapshot",
                "status": "completed",
                "details": f"{len(jobs)} jobs loaded from the existing scrape snapshot.",
            }
        )
    else:
        jobs, scrape_report = scrape_all_jobs(notify=False)
        tasks.append(
            {
                "name": "scrape_enabled_sources",
                "status": "completed",
                "details": f"{len(jobs)} jobs available after merge; {scrape_report.get('new_jobs', 0)} new jobs.",
            }
        )

    posted_today = [job for job in jobs if _same_day(str(job.get("date_posted", "")), today)]
    scraped_today = [job for job in jobs if _same_day(str(job.get("date_scraped", "")), today)]
    selected_jobs = list(posted_today)
    selected_basis = "date_posted"
    if not selected_jobs and allow_scraped_today_fallback:
        selected_jobs = list(scraped_today)
        selected_basis = "date_scraped"
    tasks.append(
        {
            "name": "select_todays_jobs",
            "status": "completed",
            "details": f"Using {len(selected_jobs)} jobs from `{selected_basis}` for {today}.",
        }
    )

    def is_target_engineering_job(job: dict) -> bool:
        title_and_tags = " ".join(
            [
                job.get("title", ""),
                " ".join(str(tag) for tag in job.get("tags", [])),
            ]
        ).lower()
        if any(term in title_and_tags for term in TARGET_EXCLUDE_TERMS):
            return False
        return any(term in title_and_tags for term in TARGET_INCLUDE_TERMS)

    relevant_jobs = [job for job in selected_jobs if is_target_engineering_job(job)]
    tasks.append(
        {
            "name": "filter_relevant_engineering_roles",
            "status": "completed",
            "details": f"{len(relevant_jobs)} of {len(selected_jobs)} jobs kept for software/backend/full-stack/devops relevance.",
        }
    )

    matched_jobs = [job for job in match_jobs_to_profile(profile, relevant_jobs) if job["match"]["score"] >= min_match_score]
    if max_jobs is not None:
        matched_jobs = matched_jobs[:max_jobs]
    tasks.append(
        {
            "name": "match_jobs_to_resume",
            "status": "completed",
            "details": f"{len(matched_jobs)} jobs selected for tailoring at match score >= {min_match_score}.",
        }
    )

    artifacts = []
    for job in matched_jobs:
        artifact = tailor_resume_for_job(profile, job)
        artifacts.append(
            {
                "job_id": artifact["job_id"],
                "company": artifact["company"],
                "title": artifact["title"],
                "source": artifact["source"],
                "match_score": artifact["match"]["score"],
                "validation_score": artifact["validation"]["score"],
                "fit_label": artifact["validation"]["fit_label"],
                "passed": artifact["validation"]["passed"] and artifact["validation"]["score"] >= min_validation_score,
                "pdf_filename": artifact["pdf_filename"],
                "pdf_path": artifact["pdf_path"],
                "matched_keywords": artifact["validation"].get("matched_keywords", []),
                "warnings": artifact["validation"].get("warnings", []),
                "issues": artifact["validation"].get("issues", []),
            }
        )

    passed = sum(1 for artifact in artifacts if artifact["passed"])
    tasks.append(
        {
            "name": "generate_and_validate_resumes",
            "status": "completed",
            "details": f"{len(artifacts)} resumes generated; {passed} met the validation threshold of {min_validation_score}.",
        }
    )

    source_statuses = Counter(source.get("status", "unknown") for source in scrape_report.get("sources", []))
    report = {
        "run_date": today,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "profile_name": profile.get("name", "Candidate"),
        "tasks": tasks,
        "source_results": scrape_report.get("sources", []),
        "source_summary": {
            "processed": len(scrape_report.get("sources", [])),
            "ok": source_statuses.get("ok", 0),
            "errors": source_statuses.get("error", 0),
            "timeouts": source_statuses.get("timeout", 0),
        },
        "job_summary": {
            "total_jobs": len(jobs),
            "posted_today": len(posted_today),
            "scraped_today": len(scraped_today),
            "processed_for_tailoring": len(matched_jobs),
            "selection_basis": selected_basis,
            "minimum_match_score": min_match_score,
        },
        "artifact_summary": {
            "generated": len(artifacts),
            "passed": passed,
            "needs_review": len(artifacts) - passed,
            "minimum_validation_score": min_validation_score,
        },
        "artifacts": artifacts,
    }

    json_path = REPORTS_DIR / f"today_tasks_{today}.json"
    md_path = REPORTS_DIR / f"today_tasks_{today}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_build_report_markdown(report), encoding="utf-8")

    report["json_report"] = str(json_path)
    report["markdown_report"] = str(md_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-jobs", type=int, default=None, help="Optional cap on how many today-jobs to tailor.")
    parser.add_argument(
        "--min-validation-score",
        type=int,
        default=70,
        help="Minimum validation score for a resume to count as passed.",
    )
    parser.add_argument(
        "--allow-scraped-today-fallback",
        action="store_true",
        help="Use jobs scraped today if no jobs have an explicit today date_posted value.",
    )
    parser.add_argument(
        "--min-match-score",
        type=int,
        default=75,
        help="Minimum profile match score required before generating a resume.",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Reuse the current scraped_jobs.json snapshot instead of scraping again.",
    )
    args = parser.parse_args()

    report = run_today_tasks(
        max_jobs=args.max_jobs,
        min_validation_score=args.min_validation_score,
        allow_scraped_today_fallback=args.allow_scraped_today_fallback,
        min_match_score=args.min_match_score,
        skip_scrape=args.skip_scrape,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
