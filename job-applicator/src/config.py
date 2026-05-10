"""
Configuration loader and validator for job-applicator.
Reads a YAML config file and returns a validated Config dataclass tree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FilterConfig:
    salary_min: Optional[int]
    salary_max: Optional[int]
    filter_undisclosed_salary: bool
    locations: List[str]
    remote_preference: str      # remote | hybrid | onsite | any
    job_types: List[str]        # full-time | part-time | contract | internship
    exclude_keywords: List[str]


@dataclass
class LinkedInConfig:
    email: str
    password: str
    cv_path: Path
    session_path: Path


@dataclass
class EmailConfig:
    enabled: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_address: str
    to_address: str
    subject_template: str


@dataclass
class AppSettings:
    max_custom_questions: int
    max_applications_per_run: int
    min_delay: float
    max_delay: float
    inter_application_delay: float
    dry_run: bool
    max_pages_per_role: int
    db_path: Path
    headless: bool


@dataclass
class Config:
    target_roles: List[str]
    filters: FilterConfig
    linkedin: LinkedInConfig
    email_notifications: EmailConfig
    application_settings: AppSettings
    config_dir: Path            # directory containing the config file


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> Config:
    """
    Load, parse, and validate a YAML config file.

    Raises:
        FileNotFoundError: if config_path or linkedin.cv_path doesn't exist.
        ValueError: on any validation failure (descriptive message).
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError("Config file must be a YAML mapping at the top level.")

    config_dir = config_path.parent

    # ── target_roles ────────────────────────────────────────────────────────
    roles = raw.get("target_roles", [])
    if not isinstance(roles, list) or not roles:
        raise ValueError("'target_roles' must be a non-empty list of strings.")
    roles = [str(r) for r in roles]

    # ── filters ─────────────────────────────────────────────────────────────
    f = raw.get("filters", {})
    salary_min = f.get("salary_min", None)
    salary_max = f.get("salary_max", None)
    if salary_min is not None:
        salary_min = int(salary_min)
    if salary_max is not None:
        salary_max = int(salary_max)

    remote_pref = str(f.get("remote_preference", "any")).lower()
    valid_remote = {"remote", "hybrid", "onsite", "any"}
    if remote_pref not in valid_remote:
        raise ValueError(
            f"'filters.remote_preference' must be one of {sorted(valid_remote)}, got '{remote_pref}'."
        )

    raw_job_types = f.get("job_types", [])
    valid_job_types = {"full-time", "part-time", "contract", "internship"}
    job_types = [str(jt).lower() for jt in raw_job_types]
    for jt in job_types:
        if jt not in valid_job_types:
            raise ValueError(
                f"'filters.job_types' contains invalid value '{jt}'. "
                f"Must be one of {sorted(valid_job_types)}."
            )

    filters = FilterConfig(
        salary_min=salary_min,
        salary_max=salary_max,
        filter_undisclosed_salary=bool(f.get("filter_undisclosed_salary", False)),
        locations=[str(loc) for loc in f.get("locations", [])],
        remote_preference=remote_pref,
        job_types=job_types,
        exclude_keywords=[str(kw) for kw in f.get("exclude_keywords", [])],
    )

    # ── linkedin ─────────────────────────────────────────────────────────────
    li = raw.get("linkedin", {})
    li_email = str(li.get("email", "")).strip()
    li_password = str(li.get("password", "")).strip()
    if not li_email:
        raise ValueError("'linkedin.email' must not be empty.")
    if not li_password:
        raise ValueError("'linkedin.password' must not be empty.")

    raw_cv = li.get("cv_path", "cv/my_cv.pdf")
    cv_path = Path(raw_cv)
    if not cv_path.is_absolute():
        cv_path = config_dir / cv_path
    cv_path = cv_path.resolve()
    if not cv_path.exists():
        raise FileNotFoundError(
            f"CV file not found: {cv_path}\n"
            "Place your PDF in the cv/ directory and update 'linkedin.cv_path' in config.yaml."
        )

    session_raw = li.get("session_path", ".linkedin_session")
    session_path = Path(session_raw)
    if not session_path.is_absolute():
        session_path = config_dir / session_path

    linkedin_cfg = LinkedInConfig(
        email=li_email,
        password=li_password,
        cv_path=cv_path,
        session_path=session_path,
    )

    # ── email_notifications ──────────────────────────────────────────────────
    en = raw.get("email_notifications", {})
    email_cfg = EmailConfig(
        enabled=bool(en.get("enabled", True)),
        smtp_host=str(en.get("smtp_host", "smtp.gmail.com")),
        smtp_port=int(en.get("smtp_port", 587)),
        smtp_user=str(en.get("smtp_user", "")),
        smtp_password=str(en.get("smtp_password", "")),
        from_address=str(en.get("from_address", "")),
        to_address=str(en.get("to_address", "")),
        subject_template=str(
            en.get("subject_template", "Job Applicator — Manual Apply Required ({date})")
        ),
    )

    # ── application_settings ─────────────────────────────────────────────────
    ap = raw.get("application_settings", {})
    raw_db = ap.get("db_path", "jobs.db")
    db_path = Path(raw_db)
    if not db_path.is_absolute():
        db_path = config_dir / db_path

    app_settings = AppSettings(
        max_custom_questions=int(ap.get("max_custom_questions", 3)),
        max_applications_per_run=int(ap.get("max_applications_per_run", 20)),
        min_delay=float(ap.get("min_delay", 2.0)),
        max_delay=float(ap.get("max_delay", 6.0)),
        inter_application_delay=float(ap.get("inter_application_delay", 15.0)),
        dry_run=bool(ap.get("dry_run", False)),
        max_pages_per_role=int(ap.get("max_pages_per_role", 5)),
        db_path=db_path,
        headless=bool(ap.get("headless", True)),
    )

    cfg = Config(
        target_roles=roles,
        filters=filters,
        linkedin=linkedin_cfg,
        email_notifications=email_cfg,
        application_settings=app_settings,
        config_dir=config_dir,
    )

    _validate(cfg)
    return cfg


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate(cfg: Config) -> None:
    f = cfg.filters
    if f.salary_min is not None and f.salary_max is not None:
        if f.salary_min > f.salary_max:
            raise ValueError(
                f"'filters.salary_min' ({f.salary_min}) must be <= "
                f"'filters.salary_max' ({f.salary_max})."
            )

    ap = cfg.application_settings
    if ap.min_delay > ap.max_delay:
        raise ValueError(
            f"'application_settings.min_delay' ({ap.min_delay}) must be <= "
            f"'application_settings.max_delay' ({ap.max_delay})."
        )
    if ap.max_custom_questions < 0:
        raise ValueError("'application_settings.max_custom_questions' must be >= 0.")
    if ap.max_applications_per_run < 0:
        raise ValueError("'application_settings.max_applications_per_run' must be >= 0.")

    en = cfg.email_notifications
    if en.enabled:
        if not (1 <= en.smtp_port <= 65535):
            raise ValueError(
                f"'email_notifications.smtp_port' must be 1–65535, got {en.smtp_port}."
            )
