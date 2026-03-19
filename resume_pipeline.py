#!/usr/bin/env python3
"""
Resume ingestion, matching, tailoring, validation, and artifact generation.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from bs4 import BeautifulSoup

from pdf_utils import write_resume_pdf

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
GENERATED_DIR = DATA_DIR / "generated_resumes"
PROFILE_FILE = DATA_DIR / "resume_profile.json"
TAILORED_FILE = DATA_DIR / "tailored_resumes.json"


SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "about"},
    "skills": {"skills", "core skills", "technical skills", "tech stack"},
    "experience": {"experience", "work experience", "employment history", "career history"},
    "projects": {"projects", "selected projects"},
    "education": {"education", "academic background"},
    "certifications": {"certifications", "licenses", "certificates"},
}

KNOWN_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "node",
    "node.js",
    "express",
    "express.js",
    "node.js",
    "react",
    "next.js",
    "django",
    "flask",
    "fastapi",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "terraform",
    "devops",
    "platform",
    "linux",
    "graphql",
    "rest",
    "microservices",
    "api",
    "ai",
    "llm",
    "machine learning",
    "data engineering",
    "etl",
    "spark",
    "airflow",
    "golang",
    "go",
    "c++",
    "c#",
    "leadership",
    "architecture",
    "system design",
    "testing",
    "ci/cd",
    "ec2",
    "s3",
    "vpc",
    "elb",
    "codedeploy",
    "codepipeline",
    "sentry",
    "jira",
    "agile",
]

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "that",
    "this",
    "from",
    "your",
    "have",
    "will",
    "their",
    "into",
    "using",
    "job",
    "jobs",
    "role",
    "team",
    "work",
    "remote",
    "onsite",
    "hybrid",
    "company",
    "candidate",
    "engineer",
    "engineering",
    "senior",
    "lead",
    "developer",
    "software",
    "years",
    "year",
    "experience",
    "required",
    "preferred",
    "strong",
    "plus",
    "build",
    "building",
    "responsible",
    "responsibilities",
    "position",
    "location",
    "full",
    "time",
}

ROLE_FAMILIES = {
    "devops_platform": {
        "triggers": ["devops", "platform", "sre", "site reliability", "cloud", "infrastructure"],
        "priority_terms": [
            "aws",
            "ec2",
            "s3",
            "vpc",
            "elb",
            "ci/cd",
            "codepipeline",
            "codedeploy",
            "docker",
            "kubernetes",
            "monitoring",
            "sentry",
            "linux",
        ],
        "headline": "Senior Software Engineer | Cloud, DevOps, and Delivery Automation",
    },
    "backend_api": {
        "triggers": ["backend", "back-end", "api", "services", "server", "platform engineer"],
        "priority_terms": [
            "node.js",
            "express",
            "rest",
            "api",
            "postgresql",
            "mongodb",
            "mysql",
            "redis",
            "performance",
            "architecture",
            "testing",
            "socket.io",
        ],
        "headline": "Senior Software Engineer | Backend APIs and Scalable Services",
    },
    "full_stack": {
        "triggers": ["full stack", "full-stack", "frontend", "front-end", "product engineer"],
        "priority_terms": [
            "node.js",
            "react",
            "next.js",
            "javascript",
            "rest",
            "api",
            "postgresql",
            "aws",
            "ai",
            "architecture",
            "agile",
        ],
        "headline": "Senior Software Engineer | Full-Stack Product Delivery",
    },
    "software_engineer": {
        "triggers": ["software engineer", "software developer", "engineer", "developer"],
        "priority_terms": [
            "node.js",
            "react",
            "aws",
            "rest",
            "api",
            "postgresql",
            "ai",
            "architecture",
            "testing",
            "agile",
        ],
        "headline": "Senior Software Engineer",
    },
}


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def save_uploaded_resume(filename: str, content: bytes) -> Path:
    ensure_data_dirs()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "resume.txt")
    path = UPLOADS_DIR / f"{_timestamp()}_{safe_name}"
    path.write_bytes(content)
    return path


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _text_quality_score(text: str) -> int:
    lowered = text.lower()
    if "%pdf-" in lowered or "/type /catalog" in lowered or "endobj" in lowered:
        return -1000

    words = re.findall(r"[A-Za-z][A-Za-z0-9+./-]{2,}", text)
    unique_words = len({word.lower() for word in words})
    email_bonus = 20 if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I) else 0
    section_bonus = sum(6 for alias_group in SECTION_ALIASES.values() if any(alias in lowered for alias in alias_group))
    return unique_words + email_bonus + section_bonus


def _extract_html_text(file_path: Path) -> str:
    html = file_path.read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)


def _normalize_display_case(text: str) -> str:
    stripped = (text or "").strip()
    letters = [char for char in stripped if char.isalpha()]
    if letters and all(char.isupper() for char in letters):
        return stripped.title()
    return stripped


def _extract_html_profile_data(file_path: Path) -> dict | None:
    html = file_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    page = soup.select_one(".page")
    if not page:
        return None

    name = (
        _normalize_display_case(page.select_one(".header-left h1").get_text(" ", strip=True))
        if page.select_one(".header-left h1")
        else ""
    )
    headline = (
        _normalize_display_case(page.select_one(".header-left .subtitle").get_text(" ", strip=True))
        if page.select_one(".header-left .subtitle")
        else ""
    )
    summary = page.select_one(".summary").get_text(" ", strip=True) if page.select_one(".summary") else ""

    header_lines = (
        [line.strip() for line in page.select_one(".header-right").stripped_strings]
        if page.select_one(".header-right")
        else []
    )
    contact_blob = " | ".join(header_lines)
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", contact_blob, re.I)
    phone_match = re.search(r"(\+?\d[\d\s().-]{7,}\d)", contact_blob)
    linkedin_match = re.search(r"(linkedin\.com/[^\s|]+)", contact_blob, re.I)
    location = header_lines[-1] if header_lines else ""

    work_history = []
    for job in page.select(".job"):
        company = job.select_one(".company").get_text(" ", strip=True) if job.select_one(".company") else ""
        dates = job.select_one(".dates").get_text(" ", strip=True) if job.select_one(".dates") else ""
        role = job.select_one(".job-role").get_text(" ", strip=True) if job.select_one(".job-role") else ""
        bullets = [item.get_text(" ", strip=True) for item in job.select("li")]
        if company or role:
            work_history.append(
                {
                    "company": company,
                    "dates": dates,
                    "role": role,
                    "bullets": bullets,
                }
            )

    skills = []
    for category in page.select(".skill-category"):
        values = category.select_one(".values").get_text(" ", strip=True) if category.select_one(".values") else ""
        for raw_skill in re.split(r"[|,/;()]", values):
            normalized = raw_skill.strip()
            if normalized:
                skills.append(normalized)

    education = []
    school = page.select_one(".edu-row .school")
    year = page.select_one(".edu-row .year")
    degree = page.select_one(".edu-degree")
    if school:
        education.append(school.get_text(" ", strip=True))
    if year:
        education.append(year.get_text(" ", strip=True))
    if degree:
        education.append(degree.get_text(" ", strip=True))

    languages = page.select_one(".languages")
    if languages:
        education.append("Languages")
        education.append(languages.get_text(" ", strip=True))

    raw_text = soup.get_text("\n", strip=True)
    return {
        "name": name,
        "headline": headline,
        "summary": summary,
        "contact": {
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(1).strip() if phone_match else "",
            "linkedin": linkedin_match.group(1) if linkedin_match else "",
            "github": "",
            "location": location,
        },
        "skills": skills,
        "experience": [bullet for job in work_history for bullet in job["bullets"]],
        "work_history": work_history,
        "projects": [],
        "education": education,
        "certifications": [],
        "raw_text": raw_text,
    }


def _find_html_companion(file_path: Path) -> Path | None:
    base = _normalize_name(file_path.stem)
    best_match = None
    best_score = 0

    for candidate in file_path.parent.glob("*.htm*"):
        candidate_base = _normalize_name(candidate.stem)
        overlap = len(set(base) & set(candidate_base))
        if base in candidate_base or candidate_base in base:
            overlap += 50
        if overlap > best_score:
            best_match = candidate
            best_score = overlap

    return best_match


def _ocr_pdf(file_path: Path) -> str:
    image_path = Path("/private/tmp") / f"{_timestamp()}_{re.sub(r'[^A-Za-z0-9._-]+', '_', file_path.stem)}.png"

    try:
        render = subprocess.run(
            ["sips", "-s", "format", "png", str(file_path), "--out", str(image_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if render.returncode != 0 or not image_path.exists():
            return ""

        ocr = subprocess.run(
            ["tesseract", str(image_path), "stdout", "--psm", "6"],
            capture_output=True,
            text=True,
            check=False,
        )
        return ocr.stdout.strip()
    finally:
        if image_path.exists():
            image_path.unlink()


def extract_resume_text(path: str | Path) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md", ".csv"}:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    elif suffix in {".html", ".htm"}:
        text = _extract_html_text(file_path)
    elif suffix in {".doc", ".docx", ".rtf", ".odt"}:
        result = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        text = result.stdout
    elif suffix == ".pdf":
        result = subprocess.run(
            ["strings", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        primary_text = result.stdout
        candidates = [primary_text]

        companion = _find_html_companion(file_path)
        if companion:
            candidates.append(_extract_html_text(companion))

        ocr_text = _ocr_pdf(file_path)
        if ocr_text:
            candidates.append(ocr_text)

        text = max(candidates, key=_text_quality_score)
    else:
        text = file_path.read_bytes().decode("utf-8", errors="ignore")

    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    cleaned = text.strip()

    if not cleaned:
        raise ValueError("Could not extract readable text from the uploaded resume.")

    return cleaned


def _split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"

    for raw_line in text.splitlines():
        line = raw_line.strip().strip("|")
        if not line:
            continue

        normalized = line.lower().rstrip(":")
        matched_section = next(
            (section for section, aliases in SECTION_ALIASES.items() if normalized in aliases),
            None,
        )

        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
            continue

        sections.setdefault(current, []).append(line)

    return sections


def _extract_contact(header_lines: list[str], full_text: str) -> dict:
    header_blob = " ".join(header_lines) + " " + full_text

    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", header_blob, re.I)
    phone_match = re.search(r"(\+?\d[\d\s().-]{7,}\d)", header_blob)
    linkedin_match = re.search(r"(https?://(?:www\.)?linkedin\.com/[^\s|]+)", header_blob, re.I)
    github_match = re.search(r"(https?://(?:www\.)?github\.com/[^\s|]+)", header_blob, re.I)

    location = ""
    for line in header_lines[:4]:
        if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
            continue
        if any(char.isdigit() for char in line):
            continue
        if any(term in line.lower() for term in ["engineer", "developer", "architect", "software"]):
            continue
        if "," in line and len(line.split()) <= 6:
            location = line
            break

    if not location:
        for line in full_text.splitlines()[:12]:
            stripped = line.strip()
            if not stripped:
                continue
            if "@" in stripped or "linkedin" in stripped.lower() or "github" in stripped.lower():
                continue
            if any(char.isdigit() for char in stripped):
                continue
            if any(term in stripped.lower() for term in ["engineer", "developer", "architect", "software"]):
                continue
            if "," in stripped and len(stripped.split()) <= 6:
                location = stripped
                break

    return {
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(1).strip() if phone_match else "",
        "linkedin": linkedin_match.group(1) if linkedin_match else "",
        "github": github_match.group(1) if github_match else "",
        "location": location,
    }


def _clean_items(lines: list[str], limit: int = 12) -> list[str]:
    items: list[str] = []

    for line in lines:
        normalized = line.lstrip("-*• ").strip()
        if len(normalized) < 3:
            continue
        items.append(normalized)

    deduped: list[str] = []
    seen = set()
    for item in items:
        key = item.lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)
        if len(deduped) >= limit:
            break

    return deduped


def _augment_items(primary: list[str], fallback_text: str, minimum: int, limit: int) -> list[str]:
    items = list(primary)
    if len(items) >= minimum:
        return items[:limit]

    for sentence in re.split(r"(?<=[.!?])\s+", fallback_text):
        normalized = sentence.strip().lstrip("-*• ").strip()
        if len(normalized) < 12:
            continue
        if normalized not in items:
            items.append(normalized)
        if len(items) >= minimum:
            break

    return items[:limit]


def _extract_skills(sections: dict[str, list[str]], full_text: str) -> list[str]:
    raw_skills = []
    for line in sections.get("skills", []):
        raw_skills.extend(re.split(r"[|,/;]", line))

    inferred = []
    lowered = full_text.lower()
    for keyword in KNOWN_KEYWORDS:
        if keyword in lowered:
            inferred.append(keyword)

    combined = [item.strip() for item in raw_skills if item.strip()] + inferred
    cleaned: list[str] = []
    seen = set()
    for skill in combined:
        normalized = skill.strip().rstrip(".")
        normalized = re.sub(r"^[A-Za-z& ]+:\s*", "", normalized).strip()
        normalized = normalized.replace("JavaScrip", "JavaScript")
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            cleaned.append(normalized)
            seen.add(key)
        if len(cleaned) >= 20:
            break

    return cleaned


def build_resume_profile(text: str, source_filename: str = "", source_path: str | Path | None = None) -> dict:
    ensure_data_dirs()
    source_path = Path(source_path) if source_path else None
    structured = None

    if source_path and source_path.suffix.lower() in {".html", ".htm"}:
        structured = _extract_html_profile_data(source_path)
    elif source_path and source_path.suffix.lower() == ".pdf":
        companion = _find_html_companion(source_path)
        if companion:
            structured = _extract_html_profile_data(companion)

    if structured:
        profile = {
            "name": structured.get("name") or "Candidate",
            "headline": structured.get("headline") or "",
            "summary": structured.get("summary") or "",
            "contact": structured.get("contact", {}),
            "skills": _clean_items(structured.get("skills", []), limit=24),
            "experience": _clean_items(structured.get("experience", []), limit=18),
            "work_history": structured.get("work_history", []),
            "projects": structured.get("projects", []),
            "education": _clean_items(structured.get("education", []), limit=8),
            "certifications": structured.get("certifications", []),
            "raw_text": structured.get("raw_text", text),
            "source_filename": source_filename,
            "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        return profile

    sections = _split_sections(text)
    header_lines = sections.get("header", [])[:8]
    name = "Candidate"

    for line in header_lines:
        if "@" in line or "linkedin" in line.lower() or "github" in line.lower():
            continue
        if any(char.isdigit() for char in line):
            continue
        if 1 < len(line.split()) <= 4:
            name = _normalize_display_case(line)
            break

    headline = ""
    for line in header_lines:
        if line == name:
            continue
        if "@" in line or "http" in line.lower():
            continue
        if any(char.isdigit() for char in line):
            continue
        if name.lower() in line.lower():
            continue
        if not any(
            term in line.lower()
            for term in ["engineer", "developer", "architect", "software", "full-stack", "backend", "frontend"]
        ):
            continue
        headline = _normalize_display_case(line)
        break

    summary_items = sections.get("summary", [])
    summary = " ".join(summary_items[:3]).strip()
    if not summary:
        summary_paragraph = ""
        capture = False
        collected = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if "work experience" in lower:
                break
            if capture:
                collected.append(stripped)
            if re.search(r"@\w|linkedin\.com|\+\d", stripped, re.I):
                capture = True
        if collected:
            summary_paragraph = " ".join(collected[:5]).strip()

        fallback = [line for line in header_lines[1:5] if "@" not in line and "http" not in line.lower()]
        summary = summary_paragraph or " ".join(fallback[:2]).strip()

    profile = {
        "name": name,
        "headline": headline,
        "summary": summary,
        "contact": _extract_contact(header_lines, text),
        "skills": _extract_skills(sections, text),
        "experience": _clean_items(sections.get("experience", []) or sections.get("header", []), limit=10),
        "work_history": [],
        "projects": _clean_items(sections.get("projects", []), limit=6),
        "education": _clean_items(sections.get("education", []), limit=5),
        "certifications": _clean_items(sections.get("certifications", []), limit=5),
        "raw_text": text,
        "source_filename": source_filename,
        "updated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    profile["experience"] = _augment_items(profile["experience"], text, minimum=3, limit=10)
    profile["projects"] = _augment_items(
        profile["projects"], profile["summary"], minimum=1 if profile["projects"] else 0, limit=6
    )

    if not profile["summary"]:
        profile["summary"] = "Experienced software professional with a background aligned to modern engineering teams."

    return profile


def save_resume_profile(profile: dict) -> dict:
    ensure_data_dirs()
    PROFILE_FILE.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return profile


def load_resume_profile() -> dict | None:
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return None


def public_profile(profile: dict | None) -> dict | None:
    if not profile:
        return None

    return {
        "name": profile.get("name", ""),
        "headline": profile.get("headline", ""),
        "summary": profile.get("summary", ""),
        "contact": profile.get("contact", {}),
        "skills": profile.get("skills", []),
        "experience_count": len(profile.get("experience", [])),
        "work_history_count": len(profile.get("work_history", [])),
        "projects_count": len(profile.get("projects", [])),
        "education_count": len(profile.get("education", [])),
        "source_filename": profile.get("source_filename", ""),
        "updated_at": profile.get("updated_at", ""),
    }


def extract_job_keywords(job: dict, limit: int = 18) -> list[str]:
    text_parts = [
        job.get("title", ""),
        job.get("description", ""),
        " ".join(job.get("tags", [])),
        job.get("location", ""),
    ]
    corpus = " ".join(part for part in text_parts if part).lower()
    matches = []

    for keyword in KNOWN_KEYWORDS:
        if keyword in corpus:
            matches.append(keyword)

    for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{2,}", corpus):
        token = token.lower()
        if token in STOPWORDS or token.isdigit():
            continue
        matches.append(token)

    ordered: list[str] = []
    seen = set()
    for token, _count in Counter(matches).most_common():
        if token not in seen:
            ordered.append(token)
            seen.add(token)
        if len(ordered) >= limit:
            break

    return ordered


def _score_text_overlap(items: list[str], keywords: list[str]) -> tuple[int, list[str]]:
    matched = []
    lowered_items = [item.lower() for item in items]

    for keyword in keywords:
        if any(keyword in item for item in lowered_items):
            matched.append(keyword)

    return len(matched), matched


def _detect_role_family(job: dict) -> str:
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()
    tags = " ".join(job.get("tags", [])).lower()
    corpus = " ".join([title, description, tags])

    scores = {}
    for family, config in ROLE_FAMILIES.items():
        score = 0
        for trigger in config["triggers"]:
            if trigger in title:
                score += 4
            elif trigger in tags:
                score += 2
            elif trigger in description:
                score += 1
        scores[family] = score

    best_family, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score <= 0 and any(term in corpus for term in ["engineer", "developer"]):
        return "software_engineer"
    return best_family if best_score > 0 else "software_engineer"


def _profile_evidence_terms(profile: dict) -> set[str]:
    blob = " ".join(
        profile.get("skills", [])
        + profile.get("experience", [])
        + profile.get("projects", [])
        + [profile.get("summary", ""), profile.get("headline", "")]
    ).lower()
    return {keyword for keyword in KNOWN_KEYWORDS if keyword in blob}


def _family_supported_terms(profile: dict, family: str, job_keywords: list[str]) -> list[str]:
    evidence = _profile_evidence_terms(profile)
    family_terms = ROLE_FAMILIES.get(family, ROLE_FAMILIES["software_engineer"])["priority_terms"]
    ranked: list[str] = []
    seen = set()

    for term in family_terms + job_keywords:
        if term in evidence and term not in seen:
            ranked.append(term)
            seen.add(term)

    return ranked


def score_job_against_profile(profile: dict, job: dict) -> dict:
    keywords = extract_job_keywords(job)
    family = _detect_role_family(job)
    profile_blob = " ".join(
        profile.get("skills", [])
        + profile.get("experience", [])
        + profile.get("projects", [])
        + [profile.get("summary", ""), profile.get("headline", "")]
    ).lower()

    evidenced_keywords = [keyword for keyword in keywords if keyword in profile_blob]
    if not evidenced_keywords:
        evidenced_keywords = keywords[:6]

    skills_overlap, matched_skills = _score_text_overlap(profile.get("skills", []), evidenced_keywords)
    exp_overlap, matched_exp = _score_text_overlap(
        profile.get("experience", []) + profile.get("projects", []),
        evidenced_keywords,
    )

    total_possible = max(1, len(evidenced_keywords))
    overlap_score = ((skills_overlap * 1.2) + (exp_overlap * 1.6)) / (total_possible * 2.8)
    structure_bonus = 0.1 if profile.get("contact", {}).get("email") else 0.0
    family_terms = _family_supported_terms(profile, family, keywords)
    family_bonus = min(0.14, len(family_terms) * 0.02)
    score = round(min(1.0, overlap_score + structure_bonus + family_bonus) * 100)

    matched = []
    seen = set()
    for keyword in matched_skills + matched_exp:
        if keyword not in seen:
            matched.append(keyword)
            seen.add(keyword)

    missing = [keyword for keyword in keywords if keyword not in matched][:10]

    return {
        "score": score,
        "role_family": family,
        "job_keywords": keywords,
        "matched_keywords": matched[:12],
        "missing_keywords": missing,
        "evidenced_keywords": evidenced_keywords[:12],
        "family_supported_terms": family_terms[:12],
    }


def match_jobs_to_profile(profile: dict, jobs: list[dict], limit: int | None = None) -> list[dict]:
    matches = []
    for job in jobs:
        score = score_job_against_profile(profile, job)
        enriched = dict(job)
        enriched["match"] = score
        matches.append(enriched)

    matches.sort(key=lambda item: item["match"]["score"], reverse=True)
    if limit:
        matches = matches[:limit]
    return matches


def _select_ranked_items(items: list[str], keywords: list[str], minimum: int, maximum: int) -> list[str]:
    if not items:
        return []

    ranked = []
    for item in items:
        lowered = item.lower()
        score = sum(2 for keyword in keywords if keyword in lowered)
        ranked.append((score, len(item), item))

    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    selected = [item for _score, _length, item in ranked[:maximum] if item]

    if len(selected) < minimum:
        for item in items:
            if item not in selected:
                selected.append(item)
            if len(selected) >= minimum:
                break

    return selected[:maximum]


def _compose_target_summary(
    profile: dict, job: dict, matched_keywords: list[str], family: str, family_supported_terms: list[str]
) -> str:
    matched_text = ", ".join(matched_keywords[:5])
    supported_text = ", ".join(family_supported_terms[:5])
    title = job.get("title", "engineering role")
    base_summary = profile.get("summary", "").strip()
    family_label = ROLE_FAMILIES.get(family, ROLE_FAMILIES["software_engineer"])["headline"]

    if matched_text and supported_text:
        return (
            f"{base_summary} Positioned for {title} work with strongest evidence in "
            f"{supported_text}. The resume is tailored around relevant delivery experience across "
            f"{matched_text} while staying within proven background."
        ).strip()
    if matched_text:
        return (
            f"{base_summary} Positioned for {family_label} responsibilities in {title}, "
            f"with emphasis on {matched_text} and production-grade software delivery."
        ).strip()

    return (
        f"{base_summary} Targeting {title} with a resume focused on the most relevant "
        f"experience already present in the source profile."
    ).strip()


def _build_transferable_highlights(profile: dict, family: str, family_supported_terms: list[str]) -> list[str]:
    evidence_blob = " ".join(profile.get("experience", []) + profile.get("projects", [])).lower()
    highlights = []

    family_statements = {
        "devops_platform": [
            "AWS operations across EC2, S3, VPC, ELB, and deployment automation.",
            "CI/CD ownership using CodePipeline, CodeDeploy, GitHub workflows, and release governance.",
            "Production reliability improvements through monitoring, performance tuning, and delivery discipline.",
        ],
        "backend_api": [
            "Backend API design and integration work across Node.js services, data access, and external platforms.",
            "Performance optimization and reliability improvements for production systems and database-heavy flows.",
            "Testable service delivery with code quality tooling, monitoring, and maintainable architecture.",
        ],
        "full_stack": [
            "Full-stack product delivery spanning backend APIs, React-based interfaces, and cloud deployment workflows.",
            "Cross-functional execution from requirements to production with emphasis on maintainable architecture.",
            "AI-assisted feature delivery and product-oriented iteration in fast-moving teams.",
        ],
        "software_engineer": [
            "Production software delivery across backend services, frontend integration, and cloud infrastructure.",
            "System design, code quality, and operational ownership across modern engineering workflows.",
            "Experience shipping customer-facing product features in collaborative teams.",
        ],
    }

    for statement in family_statements.get(family, family_statements["software_engineer"]):
        lowered = statement.lower()
        if any(term in lowered for term in family_supported_terms) or any(
            term in evidence_blob for term in family_supported_terms
        ):
            highlights.append(statement)

    if not highlights:
        highlights.extend(family_statements.get(family, family_statements["software_engineer"])[:2])

    return highlights[:3]


def _select_work_history(
    profile: dict, keywords: list[str], maximum_jobs: int = 3, bullets_per_job: int = 3
) -> list[dict]:
    work_history = profile.get("work_history", [])
    if not work_history:
        return []

    ranked = []
    for job in work_history:
        combined = " ".join([job.get("company", ""), job.get("role", ""), *job.get("bullets", [])]).lower()
        score = sum(2 for keyword in keywords if keyword in combined)
        ranked.append((score, job))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = []
    for _score, job in ranked[:maximum_jobs]:
        bullets = _select_ranked_items(job.get("bullets", []), keywords, minimum=1, maximum=bullets_per_job)
        selected.append(
            {
                "company": job.get("company", ""),
                "role": job.get("role", ""),
                "dates": job.get("dates", ""),
                "bullets": bullets,
            }
        )

    return selected


def validate_tailored_resume(resume: dict, profile: dict, job: dict) -> dict:
    issues = []
    warnings = []

    if not resume.get("contact", {}).get("email"):
        issues.append("Missing email in the tailored resume.")
    if not resume.get("summary"):
        issues.append("Missing summary section.")
    if len(resume.get("skills", [])) < 4:
        issues.append("Too few skills selected for a job-specific resume.")
    if len(resume.get("experience", [])) < 3:
        issues.append("Too few experience highlights selected.")

    job_keywords = extract_job_keywords(job)
    payload_blob = " ".join(
        [
            resume.get("summary", ""),
            *resume.get("skills", []),
            *resume.get("experience", []),
            *resume.get("projects", []),
        ]
    ).lower()
    profile_blob = profile.get("raw_text", "").lower()

    evidenced_keywords = [keyword for keyword in job_keywords if keyword in profile_blob]
    unsupported_keywords = [keyword for keyword in job_keywords if keyword not in profile_blob][:8]
    matched_keywords = [keyword for keyword in evidenced_keywords if keyword in payload_blob]

    if not evidenced_keywords:
        warnings.append("The source resume has limited direct overlap with the job description keywords.")

    coverage = len([keyword for keyword in evidenced_keywords if keyword in payload_blob]) / max(
        1, len(evidenced_keywords)
    )
    score = round((coverage * 80) + (20 if not issues else 0))
    unsupported_ratio = len(unsupported_keywords) / max(1, len(job_keywords))

    if unsupported_keywords:
        warnings.append(
            "Some job keywords were intentionally excluded because they were not evidenced in the source resume: "
            + ", ".join(unsupported_keywords[:5])
        )

    if coverage >= 0.75 and unsupported_ratio <= 0.25 and not issues:
        fit_label = "strong_alignment"
    elif coverage >= 0.5 and unsupported_ratio <= 0.5:
        fit_label = "partial_alignment"
    else:
        fit_label = "insufficient_evidence"

    return {
        "passed": not issues and coverage >= 0.6 and fit_label != "insufficient_evidence",
        "score": min(100, score),
        "coverage": round(coverage, 2),
        "fit_label": fit_label,
        "matched_keywords": matched_keywords[:12],
        "unsupported_keywords": unsupported_keywords,
        "issues": issues,
        "warnings": warnings,
    }


def _build_tailored_resume(profile: dict, job: dict, target_keywords: list[str], attempt: int) -> dict:
    family = _detect_role_family(job)
    family_supported_terms = _family_supported_terms(profile, family, target_keywords)
    prioritized_keywords = family_supported_terms + [
        keyword for keyword in target_keywords if keyword not in family_supported_terms
    ]
    experience_limit = 4 + attempt
    project_limit = 2 + min(attempt, 1)
    selected_experience = _select_ranked_items(
        profile.get("experience", []),
        prioritized_keywords,
        minimum=3,
        maximum=experience_limit,
    )
    selected_projects = _select_ranked_items(
        profile.get("projects", []),
        prioritized_keywords,
        minimum=0,
        maximum=project_limit,
    )
    selected_skills = _select_ranked_items(
        profile.get("skills", []),
        prioritized_keywords,
        minimum=6,
        maximum=12,
    )
    transferable_highlights = _build_transferable_highlights(profile, family, family_supported_terms)
    selected_work_history = _select_work_history(
        profile, prioritized_keywords, maximum_jobs=3, bullets_per_job=2 + min(attempt, 1)
    )
    normalized_headline = ROLE_FAMILIES.get(family, ROLE_FAMILIES["software_engineer"])["headline"]

    return {
        "name": profile.get("name", "Candidate"),
        "headline": normalized_headline,
        "contact": profile.get("contact", {}),
        "summary": _compose_target_summary(profile, job, prioritized_keywords, family, family_supported_terms),
        "target_role": f"{job.get('title', '')} | {job.get('location', '')}".strip(" |"),
        "skills": selected_skills,
        "experience": transferable_highlights
        + [item for item in selected_experience if item not in transferable_highlights],
        "work_history": selected_work_history,
        "projects": selected_projects,
        "education": profile.get("education", []),
        "certifications": profile.get("certifications", []),
    }


def load_tailored_resumes() -> list[dict]:
    if TAILORED_FILE.exists():
        return json.loads(TAILORED_FILE.read_text(encoding="utf-8"))
    return []


def save_tailored_resume_artifact(artifact: dict) -> dict:
    ensure_data_dirs()
    existing = load_tailored_resumes()
    filtered = [item for item in existing if item.get("job_id") != artifact.get("job_id")]
    filtered.append(artifact)
    filtered.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    TAILORED_FILE.write_text(json.dumps(filtered, indent=2), encoding="utf-8")
    return artifact


def tailor_resume_for_job(profile: dict, job: dict, output_dir: str | Path | None = None, persist: bool = True) -> dict:
    ensure_data_dirs()
    match = score_job_against_profile(profile, job)
    target_keywords = match.get("matched_keywords") or match.get("evidenced_keywords") or match.get("job_keywords", [])

    best_resume = None
    best_validation = None

    for attempt in range(3):
        candidate_resume = _build_tailored_resume(profile, job, target_keywords, attempt)
        validation = validate_tailored_resume(candidate_resume, profile, job)

        if best_validation is None or validation["score"] > best_validation["score"]:
            best_resume = candidate_resume
            best_validation = validation

        if validation["passed"]:
            break

    assert best_resume is not None
    assert best_validation is not None

    destination_dir = Path(output_dir) if output_dir else GENERATED_DIR
    destination_dir.mkdir(parents=True, exist_ok=True)
    pdf_name = f"{job.get('id', 'job')}.pdf"
    pdf_path = write_resume_pdf(destination_dir / pdf_name, best_resume)

    artifact = {
        "job_id": job.get("id"),
        "company": job.get("company"),
        "title": job.get("title"),
        "location": job.get("location"),
        "source": job.get("source"),
        "url": job.get("url"),
        "match": match,
        "validation": best_validation,
        "resume": best_resume,
        "pdf_filename": pdf_path.name,
        "pdf_path": str(pdf_path),
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    if persist:
        return save_tailored_resume_artifact(artifact)

    return artifact
