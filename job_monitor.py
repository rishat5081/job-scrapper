#!/usr/bin/env python3
"""
Job Monitor - Tracks senior software engineering jobs and sends macOS notifications
Monitors jobs from Dubai, Netherlands, and Germany
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Job tracking file
TRACKER_FILE = Path(__file__).parent / "job_tracker.json"

# Job sources to monitor (you can add more)
JOB_SOURCES = {
    "Dubai": [
        {"name": "Glassdoor Dubai", "url": "https://www.glassdoor.com/Job/dubai-remote-software-developer-jobs-SRCH_IL.0,5_IC2204498_KO6,31.htm"},
        {"name": "Indeed UAE", "url": "https://ae.indeed.com/q-software-developer-remote-l-dubai-jobs.html"},
        {"name": "NaukriGulf", "url": "https://www.naukrigulf.com/remote-developer-jobs-in-dubai"},
        {"name": "Remote DXB", "url": "https://www.remotedxb.com/"}
    ],
    "Netherlands": [
        {"name": "WeAreDevelopers NL", "url": "https://www.wearedevelopers.com/en/jobs/l/remote/netherlands"},
        {"name": "Indeed Netherlands", "url": "https://www.indeed.com/q-netherlands-developer-l-remote-jobs.html"},
        {"name": "NextLevelJobs NL", "url": "https://nextleveljobs.eu/country/nl"},
        {"name": "Remote Rocketship NL", "url": "https://www.remoterocketship.com/country/netherlands/jobs/senior-software-engineer/"}
    ],
    "Germany": [
        {"name": "LinkedIn Berlin", "url": "https://www.linkedin.com/jobs/senior-java-software-engineer-remote-jobs-berlin-be"},
        {"name": "Glassdoor Berlin", "url": "https://www.glassdoor.com/Job/berlin-remote-developer-jobs-SRCH_IL.0,6_IC2622109_KO7,23.htm"},
        {"name": "NextLevelJobs DE", "url": "https://nextleveljobs.eu/country/de"},
        {"name": "Remote Rocketship DE", "url": "https://www.remoterocketship.com/country/germany/jobs/software-engineer/"}
    ]
}


def send_notification(title, message, sound=True):
    """Send a native macOS notification"""
    script = f'display notification "{message}" with title "{title}"'
    if sound:
        script += ' sound name "Glass"'

    subprocess.run(['osascript', '-e', script])


def load_tracked_jobs():
    """Load previously tracked jobs"""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return []


def save_tracked_jobs(jobs):
    """Save tracked jobs to file"""
    with open(TRACKER_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)


def add_job(company, title, location, url, source):
    """Add a new job to tracking system"""
    jobs = load_tracked_jobs()

    job = {
        "id": len(jobs) + 1,
        "company": company,
        "title": title,
        "location": location,
        "url": url,
        "source": source,
        "date_added": datetime.now().isoformat(),
        "status": "new",
        "notes": ""
    }

    jobs.append(job)
    save_tracked_jobs(jobs)

    # Send notification
    send_notification(
        f"New Job: {company}",
        f"{title} in {location} - Click to view tracker"
    )

    return job


def update_job_status(job_id, status, notes=""):
    """Update job application status"""
    jobs = load_tracked_jobs()

    for job in jobs:
        if job["id"] == job_id:
            job["status"] = status
            job["notes"] = notes
            job["last_updated"] = datetime.now().isoformat()
            break

    save_tracked_jobs(jobs)


def get_jobs_by_status(status=None):
    """Get jobs filtered by status"""
    jobs = load_tracked_jobs()

    if status:
        return [job for job in jobs if job["status"] == status]
    return jobs


def get_jobs_by_location(location):
    """Get jobs filtered by location"""
    jobs = load_tracked_jobs()
    return [job for job in jobs if job["location"].lower() == location.lower()]


def list_all_jobs():
    """Print all tracked jobs"""
    jobs = load_tracked_jobs()

    if not jobs:
        print("No jobs tracked yet.")
        return

    print(f"\n{'='*80}")
    print(f"TRACKED JOBS ({len(jobs)} total)")
    print(f"{'='*80}\n")

    # Group by location
    locations = {}
    for job in jobs:
        loc = job["location"]
        if loc not in locations:
            locations[loc] = []
        locations[loc].append(job)

    for location, loc_jobs in locations.items():
        print(f"\n📍 {location.upper()} ({len(loc_jobs)} jobs)")
        print("-" * 80)

        for job in loc_jobs:
            status_emoji = {
                "new": "🆕",
                "applied": "📤",
                "interview": "💼",
                "rejected": "❌",
                "offer": "🎉"
            }.get(job["status"], "📋")

            print(f"\n{status_emoji} ID: {job['id']} | {job['company']}")
            print(f"   Title: {job['title']}")
            print(f"   Source: {job['source']}")
            print(f"   Status: {job['status'].upper()}")
            print(f"   Added: {job['date_added'][:10]}")
            print(f"   URL: {job['url']}")
            if job['notes']:
                print(f"   Notes: {job['notes']}")

    print(f"\n{'='*80}\n")


def show_job_sources():
    """Display all job sources to check"""
    print(f"\n{'='*80}")
    print("JOB SOURCES TO MONITOR")
    print(f"{'='*80}\n")

    for location, sources in JOB_SOURCES.items():
        print(f"\n📍 {location}")
        print("-" * 80)
        for source in sources:
            print(f"  • {source['name']}")
            print(f"    {source['url']}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("\nJob Tracker - Usage:")
        print("  python job_monitor.py add <company> <title> <location> <url> <source>")
        print("  python job_monitor.py list")
        print("  python job_monitor.py sources")
        print("  python job_monitor.py update <id> <status> [notes]")
        print("  python job_monitor.py status <status>")
        print("\nStatuses: new, applied, interview, rejected, offer")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add" and len(sys.argv) >= 7:
        company = sys.argv[2]
        title = sys.argv[3]
        location = sys.argv[4]
        url = sys.argv[5]
        source = sys.argv[6]
        job = add_job(company, title, location, url, source)
        print(f"✅ Added job #{job['id']}: {company} - {title}")

    elif command == "list":
        list_all_jobs()

    elif command == "sources":
        show_job_sources()

    elif command == "update" and len(sys.argv) >= 4:
        job_id = int(sys.argv[2])
        status = sys.argv[3]
        notes = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        update_job_status(job_id, status, notes)
        print(f"✅ Updated job #{job_id} to status: {status}")

    elif command == "status" and len(sys.argv) >= 3:
        status = sys.argv[2]
        jobs = get_jobs_by_status(status)
        print(f"\nJobs with status '{status}': {len(jobs)}")
        for job in jobs:
            print(f"  #{job['id']}: {job['company']} - {job['title']}")

    else:
        print("❌ Invalid command or arguments")
