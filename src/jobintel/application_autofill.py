#!/usr/bin/env python3
"""Best-effort browser launch and autofill for common job application fields."""

from __future__ import annotations

import contextlib
import os
from datetime import UTC, datetime

try:
    from selenium import webdriver
    from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except ModuleNotFoundError as exc:
    webdriver = None
    InvalidSessionIdException = WebDriverException = Exception
    Options = By = None
    _SELENIUM_IMPORT_ERROR = exc
else:
    _SELENIUM_IMPORT_ERROR = None

PROVIDER_PATTERNS = {
    "greenhouse": ["greenhouse.io", "boards.greenhouse.io"],
    "lever": ["lever.co"],
    "workday": ["myworkdayjobs.com", "workday.com"],
    "ashby": ["ashbyhq.com"],
    "workable": ["workable.com"],
    "bamboohr": ["bamboohr.com"],
}

FIELD_HINTS = {
    "first_name": ["first", "given", "firstname"],
    "last_name": ["last", "family", "lastname", "surname"],
    "full_name": ["full name", "fullname", "name"],
    "email": ["email", "e-mail"],
    "phone": ["phone", "mobile", "telephone"],
    "location": ["location", "city", "address"],
    "linkedin": ["linkedin"],
    "github": ["github", "portfolio", "website", "site", "url"],
    "cover_letter_text": ["cover letter", "coverletter", "message", "additional information"],
}

FILE_HINTS = {
    "resume_pdf_path": ["resume", "cv", "curriculum"],
}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def detect_application_provider(url: str) -> str:
    lowered = (url or "").lower()
    for provider, patterns in PROVIDER_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            return provider
    return "generic"


def _is_headless_fallback() -> bool:
    if os.name == "nt":
        return False
    if os.uname().sysname == "Darwin":
        return False
    return not bool(os.environ.get("DISPLAY"))


def _candidate_fields(driver) -> list:
    return driver.find_elements(By.CSS_SELECTOR, "input, textarea")


def _field_signature(element) -> str:
    parts = [
        element.get_attribute("name") or "",
        element.get_attribute("id") or "",
        element.get_attribute("placeholder") or "",
        element.get_attribute("aria-label") or "",
        element.get_attribute("data-qa") or "",
        element.get_attribute("autocomplete") or "",
    ]
    return " ".join(parts).lower()


def _fill_element(element, value: str) -> bool:
    if not value:
        return False
    input_type = (element.get_attribute("type") or "").lower()
    if input_type in {"hidden", "submit", "button", "checkbox", "radio"}:
        return False
    if not element.is_displayed() or not element.is_enabled():
        return False

    existing = (element.get_attribute("value") or "").strip()
    if existing:
        return False

    element.click()
    element.clear()
    element.send_keys(value)
    return True


def _fill_text_fields(driver, payload: dict) -> list[str]:
    filled: list[str] = []
    used_elements = set()

    for field_name, hints in FIELD_HINTS.items():
        value = payload.get(field_name, "")
        if not value:
            continue

        for element in _candidate_fields(driver):
            element_id = element.id
            if element_id in used_elements:
                continue
            signature = _field_signature(element)
            if not any(hint in signature for hint in hints):
                continue
            try:
                if _fill_element(element, value):
                    filled.append(field_name)
                    used_elements.add(element_id)
                    break
            except WebDriverException:
                continue

    if "full_name" in payload and "first_name" not in filled and "last_name" not in filled:
        for element in _candidate_fields(driver):
            signature = _field_signature(element)
            if element.id in used_elements:
                continue
            if any(hint in signature for hint in FIELD_HINTS["full_name"]):
                try:
                    if _fill_element(element, payload["full_name"]):
                        filled.append("full_name")
                        used_elements.add(element.id)
                        break
                except WebDriverException:
                    continue

    return filled


def _upload_files(driver, payload: dict) -> list[str]:
    uploaded: list[str] = []
    for file_key, hints in FILE_HINTS.items():
        value = payload.get(file_key, "")
        if not value:
            continue

        for element in _candidate_fields(driver):
            input_type = (element.get_attribute("type") or "").lower()
            if input_type != "file":
                continue
            signature = _field_signature(element)
            if not any(hint in signature for hint in hints):
                continue
            try:
                element.send_keys(value)
                uploaded.append(file_key)
                break
            except WebDriverException:
                continue
    return uploaded


def launch_autofill_session(job: dict, payload: dict) -> dict:
    url = job.get("url", "")
    provider = detect_application_provider(url)
    headless = _is_headless_fallback()

    if webdriver is None or Options is None or By is None:
        return {
            "success": False,
            "provider": provider,
            "url": url,
            "headless": headless,
            "filled_fields": [],
            "uploaded_files": [],
            "warnings": [],
            "opened_at": _timestamp(),
            "message": (
                f"Selenium is not installed in this environment: {_SELENIUM_IMPORT_ERROR}. "
                "Install the browser automation dependencies before launching autofill."
            ),
        }

    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("detach", not headless)
    if headless:
        options.add_argument("--headless=new")

    warnings: list[str] = []
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(45)
        driver.get(url)
        filled_fields = _fill_text_fields(driver, payload)
        uploaded_files = _upload_files(driver, payload)

        if not filled_fields:
            warnings.append("No matching text fields were autofilled on the detected page.")
        if payload.get("resume_pdf_path") and not uploaded_files:
            warnings.append("Resume upload field was not detected automatically.")

        return {
            "success": True,
            "provider": provider,
            "url": url,
            "headless": headless,
            "filled_fields": filled_fields,
            "uploaded_files": uploaded_files,
            "warnings": warnings,
            "opened_at": _timestamp(),
            "message": "Application page opened and autofill attempted. Review before submitting.",
        }
    except WebDriverException as exc:
        return {
            "success": False,
            "provider": provider,
            "url": url,
            "headless": headless,
            "filled_fields": [],
            "uploaded_files": [],
            "warnings": warnings,
            "opened_at": _timestamp(),
            "message": str(exc).strip() or "Browser autofill failed.",
        }
    finally:
        if driver and headless:
            with contextlib.suppress(WebDriverException, InvalidSessionIdException):
                driver.quit()
