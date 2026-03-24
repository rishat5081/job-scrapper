#!/usr/bin/env python3
"""
Flask API for governed job ingestion and resume tailoring.
"""

from __future__ import annotations

import math
import mimetypes

from flask import Flask, jsonify, request, send_file, send_from_directory

from jobintel import TEMPLATES_DIR
from jobintel.application_autofill import launch_autofill_session
from jobintel.application_materials import (
    STATUS_OPTIONS,
    get_application_status,
    load_application_tracker,
    upsert_application_status,
)
from jobintel.job_scraper import filter_jobs, load_last_scrape, load_scraped_jobs, scrape_all_jobs
from jobintel.resume_pipeline import (
    GENERATED_DIR,
    build_resume_profile,
    extract_resume_text,
    load_resume_profile,
    load_tailored_resumes,
    match_jobs_to_profile,
    public_profile,
    save_resume_profile,
    save_tailored_resume_artifact,
    save_uploaded_resume,
    tailor_resume_for_job,
)
from jobintel.source_registry import list_sources

app = Flask(__name__)


def _json_error(message: str, status_code: int = 400):
    return jsonify({"success": False, "error": message}), status_code


def _jobs_with_matches(jobs: list[dict]) -> list[dict]:
    profile = load_resume_profile()
    if not profile:
        return jobs
    return match_jobs_to_profile(profile, jobs)


def _get_job_by_id(job_id: str) -> dict | None:
    for job in load_scraped_jobs():
        if job.get("id") == job_id:
            return job
    return None


def _artifact_public_view(artifact: dict) -> dict:
    result = dict(artifact)
    result["download_url"] = f"/api/generated-resumes/{artifact['pdf_filename']}"
    cover_letter = dict(result.get("cover_letter", {}))
    if cover_letter.get("pdf_filename"):
        cover_letter["pdf_url"] = f"/api/generated-files/{cover_letter['pdf_filename']}"
    if cover_letter.get("markdown_filename"):
        cover_letter["markdown_url"] = f"/api/generated-files/{cover_letter['markdown_filename']}"
    result["cover_letter"] = cover_letter

    draft_answers = dict(result.get("draft_answers", {}))
    if draft_answers.get("markdown_filename"):
        draft_answers["markdown_url"] = f"/api/generated-files/{draft_answers['markdown_filename']}"
    if draft_answers.get("json_filename"):
        draft_answers["json_url"] = f"/api/generated-files/{draft_answers['json_filename']}"
    result["draft_answers"] = draft_answers
    result["application_status"] = get_application_status(artifact.get("job_id", ""))
    return result


def _generate_artifacts_for_jobs(profile: dict, jobs: list[dict]) -> list[dict]:
    artifacts = []
    for job in jobs:
        artifact = tailor_resume_for_job(profile, job)
        artifacts.append(_artifact_public_view(artifact))
    return artifacts


def _get_artifact_by_job_id(job_id: str) -> dict | None:
    for artifact in load_tailored_resumes():
        if artifact.get("job_id") == job_id:
            return artifact
    return None


@app.route("/")
def index():
    return send_from_directory(TEMPLATES_DIR, "live_dashboard.html")


@app.route("/automation-harness")
def automation_harness():
    return send_from_directory(TEMPLATES_DIR, "automation_harness.html")


@app.route("/api/health")
def health():
    return jsonify({"success": True, "status": "ok"})


@app.route("/api/sources")
def sources():
    return jsonify(
        {
            "success": True,
            "sources": list_sources(),
            "last_scrape": load_last_scrape(),
        }
    )


@app.route("/api/profile", methods=["GET"])
def get_profile():
    profile = load_resume_profile()
    return jsonify({"success": True, "profile": public_profile(profile)})


@app.route("/api/profile/upload", methods=["POST"])
def upload_profile():
    if "resume" not in request.files:
        return _json_error("Expected a file field named 'resume'.")

    uploaded = request.files["resume"]
    if not uploaded.filename:
        return _json_error("Resume filename is missing.")

    saved_path = save_uploaded_resume(uploaded.filename, uploaded.read())
    text = extract_resume_text(saved_path)
    profile = build_resume_profile(text, saved_path.name, saved_path)
    save_resume_profile(profile)

    jobs = _jobs_with_matches(load_scraped_jobs())
    return jsonify(
        {
            "success": True,
            "profile": public_profile(profile),
            "top_matches": jobs[:10],
        }
    )


@app.route("/api/filter-options", methods=["GET"])
def filter_options():
    jobs = load_scraped_jobs()
    tags_set = set()
    job_types_set = set()
    sources_set = set()
    for job in jobs:
        for tag in job.get("tags", []):
            if tag:
                tags_set.add(tag)
        jt = job.get("job_type", "")
        if jt and jt != "Not specified":
            job_types_set.add(jt)
        sk = job.get("source_key", "")
        if sk:
            sources_set.add(sk)
    return jsonify(
        {
            "success": True,
            "tags": sorted(tags_set),
            "job_types": sorted(job_types_set),
            "sources": sorted(sources_set),
            "experience_levels": ["junior", "mid", "senior", "lead"],
            "date_ranges": ["today", "3days", "week", "month"],
        }
    )


@app.route("/api/scraped-jobs", methods=["GET"])
def get_scraped_jobs():
    jobs = load_scraped_jobs()

    skills_param = request.args.get("skills")
    skills_list = [s.strip() for s in skills_param.split(",") if s.strip()] if skills_param else None

    salary_min_raw = request.args.get("salary_min", type=int)
    salary_max_raw = request.args.get("salary_max", type=int)

    jobs = filter_jobs(
        jobs,
        location=request.args.get("location"),
        search_term=request.args.get("search"),
        remote_policy=request.args.get("remote_policy"),
        source_key=request.args.get("source_key"),
        salary_min=salary_min_raw,
        salary_max=salary_max_raw,
        experience_level=request.args.get("experience_level"),
        skills=skills_list,
        date_posted=request.args.get("date_posted"),
        job_type=request.args.get("job_type"),
    )
    jobs = _jobs_with_matches(jobs)

    total = len(jobs)
    page = max(request.args.get("page", type=int) or 1, 1)
    per_page = request.args.get("per_page", type=int)
    limit = request.args.get("limit", type=int)

    if per_page:
        per_page = max(1, min(per_page, 100))
        total_pages = max(1, math.ceil(total / per_page)) if total else 1
        page = min(page, total_pages)
        start = (page - 1) * per_page
        end = start + per_page
        jobs = jobs[start:end]
        return jsonify(
            {
                "success": True,
                "total": total,
                "count": len(jobs),
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "jobs": jobs,
            }
        )

    if limit:
        jobs = jobs[:limit]

    return jsonify({"success": True, "total": total, "count": len(jobs), "jobs": jobs})


@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    jobs, report = scrape_all_jobs(notify=False)
    jobs = _jobs_with_matches(jobs)
    return jsonify(
        {
            "success": True,
            "total_jobs": len(jobs),
            "new_jobs": report.get("new_jobs", 0),
            "report": report,
        }
    )


@app.route("/api/matches", methods=["GET"])
def matches():
    profile = load_resume_profile()
    if not profile:
        return _json_error("Upload a resume before requesting matches.", 412)

    jobs = match_jobs_to_profile(profile, load_scraped_jobs(), limit=request.args.get("limit", type=int) or 50)
    return jsonify({"success": True, "total": len(jobs), "jobs": jobs})


@app.route("/api/jobs/<job_id>/tailor", methods=["POST"])
def tailor_job(job_id: str):
    profile = load_resume_profile()
    if not profile:
        return _json_error("Upload a resume before generating tailored resumes.", 412)

    job = _get_job_by_id(job_id)
    if not job:
        return _json_error("Job not found.", 404)

    artifact = tailor_resume_for_job(profile, job)
    return jsonify({"success": True, "artifact": _artifact_public_view(artifact)})


@app.route("/api/jobs/<job_id>/prepare-application", methods=["POST"])
def prepare_application(job_id: str):
    return tailor_job(job_id)


@app.route("/api/jobs/<job_id>/status", methods=["GET"])
def job_status(job_id: str):
    return jsonify(
        {"success": True, "job_id": job_id, "status": get_application_status(job_id), "status_options": STATUS_OPTIONS}
    )


@app.route("/api/jobs/<job_id>/status", methods=["POST"])
def update_job_status(job_id: str):
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    notes = payload.get("notes")

    if status and status not in STATUS_OPTIONS:
        return _json_error("Invalid application status.")

    updated = upsert_application_status(job_id, status=status, notes=notes)
    return jsonify({"success": True, "job_id": job_id, "status": updated, "status_options": STATUS_OPTIONS})


@app.route("/api/jobs/<job_id>/autofill", methods=["POST"])
def autofill_job(job_id: str):
    profile = load_resume_profile()
    if not profile:
        return _json_error("Upload a resume before launching autofill.", 412)

    job = _get_job_by_id(job_id)
    if not job:
        return _json_error("Job not found.", 404)

    artifact = _get_artifact_by_job_id(job_id)
    if not artifact:
        artifact = tailor_resume_for_job(profile, job)

    autofill = artifact.get("autofill", {})
    payload = autofill.get("payload", {})
    if not payload:
        return _json_error("Application packet is missing autofill data.", 409)

    result = launch_autofill_session(job, payload)
    status_update = {"last_autofill_at": result.get("opened_at"), "last_autofill_success": result.get("success", False)}
    if result.get("success") and artifact.get("application_status", {}).get("status") == "prepared":
        status_update["status"] = "ready_to_review"
    updated_status = upsert_application_status(job_id, **status_update)

    refreshed_artifact = _get_artifact_by_job_id(job_id)
    if refreshed_artifact:
        refreshed_artifact.setdefault("autofill", {})
        refreshed_artifact["autofill"]["last_result"] = result
        refreshed_artifact["application_status"] = updated_status
        save_tailored_resume_artifact(refreshed_artifact)

    return jsonify(
        {
            "success": True,
            "job_id": job_id,
            "result": result,
            "status": updated_status,
            "artifact": _artifact_public_view(refreshed_artifact or artifact),
        }
    )


@app.route("/api/pipeline/run", methods=["POST"])
def run_pipeline():
    profile = load_resume_profile()
    if not profile:
        return _json_error("Upload a resume before running the pipeline.", 412)

    payload = request.get_json(silent=True) or {}
    requested_ids = payload.get("job_ids") or []
    limit = min(max(int(payload.get("limit", 5)), 1), 25)

    jobs = match_jobs_to_profile(profile, load_scraped_jobs())
    if requested_ids:
        requested = set(requested_ids)
        jobs = [job for job in jobs if job.get("id") in requested]
    else:
        jobs = jobs[:limit]

    artifacts = _generate_artifacts_for_jobs(profile, jobs)

    return jsonify({"success": True, "total": len(artifacts), "artifacts": artifacts})


@app.route("/api/pipeline/refresh", methods=["POST"])
def refresh_pipeline():
    profile = load_resume_profile()
    if not profile:
        return _json_error("Upload a resume before refreshing and generating resumes.", 412)

    payload = request.get_json(silent=True) or {}
    limit = min(max(int(payload.get("limit", 6)), 1), 25)

    jobs, report = scrape_all_jobs(notify=False)
    matched_jobs = match_jobs_to_profile(profile, jobs)

    selected_jobs = matched_jobs[:limit]
    artifacts = _generate_artifacts_for_jobs(profile, selected_jobs)

    return jsonify(
        {
            "success": True,
            "report": report,
            "jobs": selected_jobs,
            "artifacts": artifacts,
            "total": len(artifacts),
        }
    )


@app.route("/api/generated-resumes", methods=["GET"])
def generated_resumes():
    artifacts = [_artifact_public_view(item) for item in load_tailored_resumes()]
    return jsonify({"success": True, "total": len(artifacts), "artifacts": artifacts, "status_options": STATUS_OPTIONS})


@app.route("/api/generated-resumes/<path:filename>", methods=["GET"])
def download_generated_resume(filename: str):
    path = GENERATED_DIR / filename
    if not path.exists():
        return _json_error("Generated PDF not found.", 404)
    return send_file(path, mimetype="application/pdf", as_attachment=True, download_name=path.name)


@app.route("/api/generated-files/<path:filename>", methods=["GET"])
def download_generated_file(filename: str):
    path = GENERATED_DIR / filename
    if not path.exists():
        return _json_error("Generated file not found.", 404)
    mimetype, _encoding = mimetypes.guess_type(path.name)
    return send_file(path, mimetype=mimetype or "application/octet-stream", as_attachment=True, download_name=path.name)


@app.route("/api/application-tracker", methods=["GET"])
def application_tracker():
    tracker = load_application_tracker()
    return jsonify({"success": True, "tracker": tracker, "status_options": STATUS_OPTIONS})


@app.route("/api/stats", methods=["GET"])
def stats():
    jobs = load_scraped_jobs()
    profile = load_resume_profile()
    generated = load_tailored_resumes()

    jobs_with_matches = match_jobs_to_profile(profile, jobs) if profile else jobs
    strong_matches = (
        len([job for job in jobs_with_matches if job.get("match", {}).get("score", 0) >= 70]) if profile else 0
    )

    by_source = {}
    for job in jobs:
        source = job.get("source", "Unknown")
        by_source[source] = by_source.get(source, 0) + 1

    return jsonify(
        {
            "success": True,
            "stats": {
                "jobs_scraped": len(jobs),
                "sources_in_catalog": len(list_sources()),
                "strong_matches": strong_matches,
                "generated_resumes": len(generated),
                "prepared_applications": len(
                    [item for item in generated if item.get("cover_letter") and item.get("draft_answers")]
                ),
                "has_profile": bool(profile),
                "jobs_by_source": by_source,
            },
        }
    )


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE")
    return response


if __name__ == "__main__":
    import os

    print("Job system API running at http://localhost:8080")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("FLASK_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_PORT", "8080")),
    )
