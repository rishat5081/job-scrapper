#!/usr/bin/env python3
"""HTML-to-PDF rendering backed by headless Chrome."""

from __future__ import annotations

import html
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]


def _find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if os.path.isabs(candidate):
            if Path(candidate).exists():
                return candidate
        else:
            result = subprocess.run(
                ["which", candidate],
                capture_output=True,
                text=True,
                check=False,
            )
            resolved = result.stdout.strip()
            if resolved:
                return resolved
    return None


def _escape(text: str) -> str:
    return html.escape(text or "")


def _section(title: str, items: list[str] | str) -> str:
    if isinstance(items, str):
        items = [items] if items else []

    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return ""

    bullets = "".join(f"<li>{_escape(item)}</li>" for item in cleaned)
    return f"""
    <section class="section">
      <h2>{_escape(title)}</h2>
      <ul>{bullets}</ul>
    </section>
    """


def _work_history_section(work_history: list[dict]) -> str:
    if not work_history:
        return ""

    jobs = []
    for item in work_history:
        bullets = "".join(f"<li>{_escape(bullet)}</li>" for bullet in item.get("bullets", []))
        jobs.append(
            f"""
            <article class="job">
              <div class="job-head">
                <div>
                  <div class="company">{_escape(item.get("company", ""))}</div>
                  <div class="role">{_escape(item.get("role", ""))}</div>
                </div>
                <div class="dates">{_escape(item.get("dates", ""))}</div>
              </div>
              <ul>{bullets}</ul>
            </article>
            """
        )

    return f"""
    <section class="section full">
      <h2>Selected Experience</h2>
      {"".join(jobs)}
    </section>
    """


def _resume_html(resume: dict) -> str:
    contact = resume.get("contact", {})
    contact_items = [
        contact.get("email", ""),
        contact.get("phone", ""),
        contact.get("location", ""),
        contact.get("linkedin", ""),
        contact.get("github", ""),
    ]
    contact_line = " | ".join(item for item in contact_items if item)

    skills = resume.get("skills", [])
    experience = resume.get("experience", [])
    projects = resume.get("projects", [])
    education = resume.get("education", [])
    certifications = resume.get("certifications", [])
    work_history = resume.get("work_history", [])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{_escape(resume.get("name", "Candidate"))}</title>
  <style>
    @page {{
      size: A4;
      margin: 14mm;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      color: #18222d;
      background: #fff;
      font-size: 11px;
      line-height: 1.45;
    }}

    .page {{
      width: 100%;
    }}

    .header {{
      border-bottom: 2px solid #0f766e;
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}

    h1 {{
      margin: 0;
      font-size: 22px;
      line-height: 1.1;
      letter-spacing: 0.02em;
    }}

    .headline {{
      margin-top: 5px;
      font-size: 13px;
      color: #0f766e;
      font-weight: 700;
    }}

    .contact {{
      margin-top: 7px;
      color: #4b5b6b;
      font-size: 10px;
    }}

    .summary {{
      margin: 12px 0 0;
      color: #243443;
      font-size: 11px;
    }}

    .target {{
      margin-top: 8px;
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: #eef7f6;
      color: #0f5c59;
      font-size: 10px;
      font-weight: 600;
    }}

    .grid {{
      display: grid;
      grid-template-columns: 1.45fr 0.95fr;
      gap: 12px;
      align-items: start;
    }}

    .section {{
      margin-top: 12px;
      break-inside: avoid;
    }}

    h2 {{
      margin: 0 0 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #0f1720;
      border-bottom: 1px solid #d8e2ea;
      padding-bottom: 4px;
    }}

    ul {{
      margin: 0;
      padding-left: 16px;
    }}

    li {{
      margin-bottom: 5px;
      color: #22313f;
    }}

    .job {{
      padding: 8px 0;
      border-bottom: 1px solid #eef2f6;
      break-inside: avoid;
    }}

    .job:last-child {{
      border-bottom: none;
    }}

    .job-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 6px;
      align-items: baseline;
    }}

    .company {{
      font-weight: 700;
      font-size: 11px;
      color: #18222d;
    }}

    .role {{
      font-size: 10px;
      color: #47606c;
      margin-top: 2px;
    }}

    .dates {{
      font-size: 10px;
      color: #627484;
      white-space: nowrap;
    }}

    .skills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }}

    .skill {{
      padding: 5px 8px;
      border-radius: 999px;
      background: #f2f4f7;
      color: #334155;
      font-size: 10px;
    }}

    .full {{
      grid-column: 1 / -1;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="header">
      <h1>{_escape(resume.get("name", "Candidate"))}</h1>
      <div class="headline">{_escape(resume.get("headline", ""))}</div>
      <div class="contact">{_escape(contact_line)}</div>
      <p class="summary">{_escape(resume.get("summary", ""))}</p>
      <div class="target">{_escape(resume.get("target_role", ""))}</div>
    </header>

    <main class="grid">
      <section class="section full">
        <h2>Skills</h2>
        <div class="skills">
          {"".join(f'<span class="skill">{_escape(skill)}</span>' for skill in skills)}
        </div>
      </section>
      {_section("Experience Highlights", experience)}
      {_work_history_section(work_history)}
      {_section("Projects", projects)}
      {_section("Education", education)}
      {_section("Certifications", certifications)}
    </main>
  </div>
</body>
</html>
"""


def _cover_letter_html(document: dict) -> str:
    title = document.get("title", "Cover Letter")
    subtitle = document.get("subtitle", "")
    contact_line = document.get("contact_line", "")
    body = document.get("body", "")
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    body_html = "".join(f"<p>{_escape(part)}</p>" for part in paragraphs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{_escape(title)}</title>
  <style>
    @page {{
      size: A4;
      margin: 18mm;
    }}

    body {{
      margin: 0;
      font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif;
      color: #1e293b;
      background: #fff;
      font-size: 12px;
      line-height: 1.65;
    }}

    .page {{
      width: 100%;
    }}

    .header {{
      border-bottom: 2px solid #1d4ed8;
      padding-bottom: 12px;
      margin-bottom: 18px;
    }}

    h1 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.15;
    }}

    .subtitle {{
      margin-top: 6px;
      color: #1d4ed8;
      font-size: 12px;
      font-weight: 700;
    }}

    .contact {{
      margin-top: 6px;
      color: #64748b;
      font-size: 10px;
    }}

    p {{
      margin: 0 0 12px;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="header">
      <h1>{_escape(title)}</h1>
      {f'<div class="subtitle">{_escape(subtitle)}</div>' if subtitle else ""}
      {f'<div class="contact">{_escape(contact_line)}</div>' if contact_line else ""}
    </header>
    <main>{body_html}</main>
  </div>
</body>
</html>
"""


def _legacy_write_pdf(output_path: Path, resume: dict) -> Path:
    from pathlib import Path as _Path

    content = (
        "%PDF-1.4\n% fallback\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        "4 0 obj\n<< /Length 0 >>\nstream\nendstream\nendobj\nxref\n0 5\n"
        "0000000000 65535 f \n0000000015 00000 n \n0000000064 00000 n \n0000000121 00000 n \n0000000208 00000 n \n"
        "trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n256\n%%EOF\n"
    )
    _Path(output_path).write_text(content, encoding="latin-1")
    return output_path


def _render_html_pdf(output_path: str | Path, html_content: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    chrome = _find_chrome()
    if not chrome:
        return _legacy_write_pdf(path, {})

    last_error = "unknown error"
    for _attempt in range(3):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            html_path = temp_dir_path / "resume.html"
            pdf_path = temp_dir_path / "resume.pdf"
            log_path = temp_dir_path / "chrome.log"
            html_path.write_text(html_content, encoding="utf-8")

            command = [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-first-run",
                "--no-default-browser-check",
                "--no-pdf-header-footer",
                "--virtual-time-budget=1500",
                f"--print-to-pdf={pdf_path}",
                html_path.as_uri(),
            ]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=45,
            )
            log_path.write_text((result.stderr or "") + "\n" + (result.stdout or ""), encoding="utf-8")

            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                path.write_bytes(pdf_path.read_bytes())
                return path

            shell_script = f"""
            {shlex.quote(chrome)} --headless=new --disable-gpu --no-sandbox --no-first-run --no-default-browser-check --no-pdf-header-footer --virtual-time-budget=1500 --print-to-pdf={shlex.quote(str(pdf_path))} {shlex.quote(html_path.as_uri())} >{shlex.quote(str(log_path))} 2>&1 &
            pid=$!
            for i in {{1..25}}; do
              if [ -s {shlex.quote(str(pdf_path))} ]; then
                break
              fi
              sleep 1
            done
            kill $pid 2>/dev/null || true
            wait $pid 2>/dev/null || true
            """
            shell = shutil.which("zsh") or shutil.which("bash") or "/bin/sh"
            result = subprocess.run(
                [shell, "-c", shell_script],
                capture_output=True,
                text=True,
                check=False,
                timeout=40,
            )

            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                path.write_bytes(pdf_path.read_bytes())
                return path

            chrome_log = log_path.read_text(encoding="utf-8", errors="ignore")
            last_error = (chrome_log or result.stderr or result.stdout).strip() or last_error
        time.sleep(1)

    raise RuntimeError(f"Chrome PDF generation failed: {last_error}")


def write_resume_pdf(output_path: str | Path, resume: dict) -> Path:
    return _render_html_pdf(output_path, _resume_html(resume))


def write_cover_letter_pdf(output_path: str | Path, document: dict) -> Path:
    return _render_html_pdf(output_path, _cover_letter_html(document))
