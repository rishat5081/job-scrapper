#!/usr/bin/env python3
"""Application package generation, validation, and status tracking."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from jobintel import DATA_DIR
from jobintel.pdf_utils import write_cover_letter_pdf

APPLICATION_TRACKER_FILE = DATA_DIR / "application_tracker.json"

STATUS_OPTIONS = [
    "prepared",
    "ready_to_review",
    "applied",
    "interview",
    "offer",
    "rejected",
    "archived",
]

CONTENT_STOPWORDS = {
    "and",
    "the",
    "with",
    "from",
    "this",
    "that",
    "your",
    "their",
    "will",
    "have",
    "into",
    "role",
    "team",
    "work",
    "remote",
    "software",
    "engineer",
    "developer",
    "engineering",
    "experience",
    "years",
}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", text or "").strip("_").lower() or "document"


def load_application_tracker() -> dict[str, dict]:
    if APPLICATION_TRACKER_FILE.exists():
        return json.loads(APPLICATION_TRACKER_FILE.read_text(encoding="utf-8"))
    return {}


def save_application_tracker(payload: dict[str, dict]) -> dict[str, dict]:
    APPLICATION_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    APPLICATION_TRACKER_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def upsert_application_status(job_id: str, **updates) -> dict:
    tracker = load_application_tracker()
    current = tracker.get(job_id, {"status": "prepared", "notes": "", "created_at": _timestamp()})
    current.update({key: value for key, value in updates.items() if value is not None})
    current["updated_at"] = _timestamp()
    tracker[job_id] = current
    save_application_tracker(tracker)
    return current


def get_application_status(job_id: str) -> dict:
    tracker = load_application_tracker()
    return tracker.get(job_id, {"status": "prepared", "notes": "", "created_at": "", "updated_at": ""})


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _alignment_terms(job: dict, artifact: dict, limit: int = 8) -> list[str]:
    match = artifact.get("match", {})
    candidates = (
        list(match.get("family_supported_terms") or [])
        + list(match.get("matched_keywords") or [])
        + list(match.get("evidenced_keywords") or [])
    )
    title_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{2,}", job.get("title", "").lower())
    for token in title_tokens:
        if token not in CONTENT_STOPWORDS:
            candidates.append(token)

    ordered = []
    seen = set()
    for item in candidates:
        normalized = _normalize_text(str(item)).lower()
        if not normalized or normalized in CONTENT_STOPWORDS or normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
        if len(ordered) >= limit:
            break
    return ordered


def _evidence_lines(profile: dict, artifact: dict, limit: int = 3) -> list[str]:
    resume = artifact.get("resume", {})
    lines = []
    for item in resume.get("work_history", []):
        for bullet in item.get("bullets", []):
            normalized = _normalize_text(bullet)
            if normalized:
                lines.append(normalized)
    for item in resume.get("experience", []):
        normalized = _normalize_text(item)
        if normalized:
            lines.append(normalized)
    for item in profile.get("projects", []):
        normalized = _normalize_text(item)
        if normalized:
            lines.append(normalized)

    deduped = []
    seen = set()
    for item in lines:
        key = item.lower()
        if key in seen:
            continue
        deduped.append(item)
        seen.add(key)
        if len(deduped) >= limit:
            break
    return deduped


def _job_focus_statement(job: dict, artifact: dict) -> str:
    terms = _alignment_terms(job, artifact, limit=5)
    if not terms:
        return "production software delivery and modern engineering workflows"
    if len(terms) == 1:
        return terms[0]
    if len(terms) == 2:
        return f"{terms[0]} and {terms[1]}"
    return f"{', '.join(terms[:-1])}, and {terms[-1]}"


def _coverage_score(text: str, terms: list[str]) -> tuple[int, list[str]]:
    lowered = (text or "").lower()
    matched = [term for term in terms if term in lowered]
    score = round((len(matched) / max(1, len(terms))) * 100)
    return score, matched


def build_cover_letter(profile: dict, job: dict, artifact: dict) -> str:
    contact = profile.get("contact", {})
    supported_terms = _job_focus_statement(job, artifact)
    company = job.get("company", "your team")
    title = job.get("title", "the role")
    summary = profile.get("summary", "").strip()
    evidence_lines = _evidence_lines(profile, artifact, limit=2)
    evidence_sentence = " ".join(
        [
            f"My recent work includes {evidence_lines[0].rstrip('.')}." if len(evidence_lines) >= 1 else "",
            f"I have also delivered {evidence_lines[1].rstrip('.')}." if len(evidence_lines) >= 2 else "",
        ]
    ).strip()
    if not evidence_sentence:
        evidence_sentence = (
            "My recent work includes production backend delivery, product execution, and cloud-backed engineering work."
        )

    opening = f"Dear Hiring Team at {company},"
    intro = (
        f"I am applying for the {title} role. My background centers on {summary.lower() if summary else 'shipping production software'} "
        f"with directly demonstrated work across {supported_terms}."
    )
    body = (
        f"{evidence_sentence} That makes me especially relevant for roles focused on {supported_terms}, "
        "system ownership, and dependable delivery."
    )
    close = (
        f"I would welcome the opportunity to discuss how that experience can support {company}'s priorities for this role. "
        "Thank you for your consideration."
    )

    signature_lines = [
        "Sincerely,",
        profile.get("name", "Candidate"),
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("linkedin", ""),
    ]
    signature = "\n".join(line for line in signature_lines if line)
    return "\n\n".join([opening, intro, body, close, signature]).strip()


def build_draft_answers(profile: dict, job: dict, artifact: dict, cover_letter_text: str) -> list[dict]:
    supported_terms = _job_focus_statement(job, artifact)
    company = job.get("company", "the company")
    title = job.get("title", "the role")
    summary = profile.get("summary", "").strip()
    contact = profile.get("contact", {})
    evidence_lines = _evidence_lines(profile, artifact, limit=3)
    evidence_text = (
        " ".join(evidence_lines[:2]) if evidence_lines else "production software delivery in modern product teams"
    )
    resume = artifact.get("resume", {})
    key_skills = ", ".join((resume.get("skills") or [])[:6]) or supported_terms

    return [
        {
            "question": "Why are you interested in this role?",
            "answer": (
                f"This role aligns with my background in {supported_terms}. I am most effective in positions where I can "
                f"ship production software, improve delivery quality, and contribute across the core engineering workflow for {title}. "
                f"My recent work includes {evidence_text}."
            ),
        },
        {
            "question": "Why are you interested in this company?",
            "answer": (
                f"{company} is hiring for work that overlaps with the areas where I already have proven experience. "
                f"I am especially interested in roles where {supported_terms} and strong product delivery expectations meet."
            ),
        },
        {
            "question": "Summarize your most relevant experience.",
            "answer": (
                f"{summary} My recent work includes directly evidenced contributions around {supported_terms}. "
                f"Relevant examples include {evidence_text}. Core skills I would bring into this application include {key_skills}."
            ),
        },
        {
            "question": "What should we know before reviewing your application?",
            "answer": (
                "All materials in this application packet are tailored to the job description while staying within my demonstrated background. "
                "Unsupported technologies are intentionally not claimed."
            ),
        },
        {
            "question": "Application basics",
            "answer": (
                f"Name: {profile.get('name', '')}; Email: {contact.get('email', '')}; Phone: {contact.get('phone', '')}; "
                f"Location: {contact.get('location', '')}."
            ),
        },
    ]


def build_autofill_payload(profile: dict, artifact: dict, cover_letter_text: str, draft_answers: list[dict]) -> dict:
    contact = profile.get("contact", {})
    name = profile.get("name", "").strip()
    parts = name.split()
    first_name = parts[0] if parts else ""
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    return {
        "full_name": name,
        "first_name": first_name,
        "last_name": last_name,
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": contact.get("location", ""),
        "linkedin": contact.get("linkedin", ""),
        "github": contact.get("github", ""),
        "resume_pdf_path": artifact.get("pdf_path", ""),
        "cover_letter_text": cover_letter_text,
        "summary": artifact.get("resume", {}).get("summary", ""),
        "draft_answers": draft_answers,
        "target_role": artifact.get("title", ""),
    }


def validate_application_packet(job: dict, artifact: dict, packet: dict) -> dict:
    cover_letter_text = packet.get("cover_letter", {}).get("text", "")
    draft_answers = packet.get("draft_answers", {}).get("items", [])
    combined_answers = " ".join(item.get("answer", "") for item in draft_answers)
    terms = _alignment_terms(job, artifact, limit=6)

    issues = []
    warnings = []

    if not cover_letter_text or len(cover_letter_text.split()) < 80:
        issues.append("Cover letter is too short or missing.")
    if len(draft_answers) < 4:
        issues.append("Draft answers are incomplete.")
    if any(
        len(item.get("answer", "").split()) < (6 if item.get("question") == "Application basics" else 12)
        for item in draft_answers
    ):
        issues.append("One or more draft answers are too short.")

    title = job.get("title", "")
    company = job.get("company", "")
    if title and title.lower() not in cover_letter_text.lower():
        issues.append("Cover letter does not name the target role.")
    if company and company.lower() not in cover_letter_text.lower():
        warnings.append("Cover letter does not mention the company name.")

    cover_score, cover_terms = _coverage_score(cover_letter_text, terms)
    answers_score, answer_terms = _coverage_score(combined_answers, terms)
    overall = round((cover_score * 0.45) + (answers_score * 0.55))

    if cover_score < 50:
        issues.append("Cover letter is not specific enough to the job requirements.")
    if answers_score < 50:
        issues.append("Draft answers are not specific enough to the job requirements.")

    fit_label = (
        "strong_alignment" if overall >= 80 else "partial_alignment" if overall >= 60 else "insufficient_evidence"
    )

    return {
        "passed": not issues and overall >= 70,
        "score": overall,
        "fit_label": fit_label,
        "alignment_terms": terms,
        "cover_letter_score": cover_score,
        "cover_letter_terms": cover_terms,
        "draft_answers_score": answers_score,
        "draft_answers_terms": answer_terms,
        "issues": issues,
        "warnings": warnings,
    }


def prepare_application_packet(
    profile: dict, job: dict, artifact: dict, output_dir: str | Path | None = None, persist: bool = True
) -> dict:
    cover_letter_text = build_cover_letter(profile, job, artifact)
    draft_answers = build_draft_answers(profile, job, artifact, cover_letter_text)
    packet = {
        "cover_letter": {
            "text": cover_letter_text,
        },
        "draft_answers": {
            "items": draft_answers,
        },
    }
    autofill_payload = build_autofill_payload(profile, artifact, cover_letter_text, draft_answers)
    packet["autofill"] = {
        "payload": autofill_payload,
        "last_result": None,
    }
    packet["packet_validation"] = validate_application_packet(job, artifact, packet)
    packet["application_status"] = (
        get_application_status(job.get("id", ""))
        if not persist
        else upsert_application_status(
            job.get("id", ""),
            company=job.get("company", ""),
            title=job.get("title", ""),
            source=job.get("source", ""),
            url=job.get("url", ""),
        )
    )

    if not persist:
        return packet

    files = write_application_support_files(
        output_dir or DATA_DIR / "generated_resumes", job, cover_letter_text, draft_answers
    )
    return {
        **packet,
        **files,
        "autofill": {
            "payload": autofill_payload,
            "last_result": None,
        },
    }


def write_application_support_files(
    output_dir: str | Path,
    job: dict,
    cover_letter_text: str,
    draft_answers: list[dict],
) -> dict:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_slug(job.get("id", "job"))

    cover_letter_md = out_dir / f"{stem}_cover_letter.md"
    cover_letter_pdf = out_dir / f"{stem}_cover_letter.pdf"
    answers_md = out_dir / f"{stem}_draft_answers.md"
    answers_json = out_dir / f"{stem}_draft_answers.json"

    cover_letter_md.write_text(cover_letter_text + "\n", encoding="utf-8")
    write_cover_letter_pdf(cover_letter_pdf, {"title": job.get("title", ""), "body": cover_letter_text})

    answers_md.write_text(
        "\n\n".join(f"## {item['question']}\n\n{item['answer']}" for item in draft_answers) + "\n",
        encoding="utf-8",
    )
    answers_json.write_text(json.dumps(draft_answers, indent=2), encoding="utf-8")

    return {
        "cover_letter": {
            "text": cover_letter_text,
            "markdown_filename": cover_letter_md.name,
            "markdown_path": str(cover_letter_md),
            "pdf_filename": cover_letter_pdf.name,
            "pdf_path": str(cover_letter_pdf),
        },
        "draft_answers": {
            "items": draft_answers,
            "markdown_filename": answers_md.name,
            "markdown_path": str(answers_md),
            "json_filename": answers_json.name,
            "json_path": str(answers_json),
        },
    }
