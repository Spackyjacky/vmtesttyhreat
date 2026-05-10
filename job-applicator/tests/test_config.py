"""Unit tests for src/config.py — uses fixture YAML files in tests/fixtures/."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import pytest

from src.config import load_config

FIXTURES = Path(__file__).parent / "fixtures"


def _write_yaml(tmp_path: Path, content: str, cv: bool = True) -> Path:
    """Write a config YAML to tmp_path, optionally creating a dummy CV."""
    if cv:
        cv_file = tmp_path / "cv" / "test_cv.pdf"
        cv_file.parent.mkdir(parents=True, exist_ok=True)
        cv_file.write_bytes(b"%PDF-1.4 test")  # minimal PDF header

    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(content, encoding="utf-8")
    return cfg_file


def _base_yaml(tmp_path: Path, **overrides) -> str:
    """Return a valid YAML config string, with optional field overrides."""
    cv_rel = "cv/test_cv.pdf"
    return f"""
target_roles:
  - "SOC Analyst"

filters:
  salary_min: 60000
  salary_max: 130000
  filter_undisclosed_salary: false
  locations:
    - "New York"
  remote_preference: any
  job_types:
    - full-time
  exclude_keywords:
    - "unpaid"

linkedin:
  email: "user@example.com"
  password: "secret"
  cv_path: "{cv_rel}"
  session_path: ".session"

email_notifications:
  enabled: true
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "user@example.com"
  smtp_password: "apppass"
  from_address: "user@example.com"
  to_address: "user@example.com"
  subject_template: "Test ({{date}})"

application_settings:
  max_custom_questions: 3
  max_applications_per_run: 20
  min_delay: 2.0
  max_delay: 6.0
  inter_application_delay: 15.0
  dry_run: false
  max_pages_per_role: 5
  db_path: "jobs.db"
  headless: true
"""


# ---------------------------------------------------------------------------
# Valid config
# ---------------------------------------------------------------------------

class TestValidConfig:
    def test_loads_successfully(self, tmp_path):
        cfg_file = _write_yaml(tmp_path, _base_yaml(tmp_path))
        cfg = load_config(cfg_file)
        assert cfg.target_roles == ["SOC Analyst"]

    def test_cv_path_resolved(self, tmp_path):
        cfg_file = _write_yaml(tmp_path, _base_yaml(tmp_path))
        cfg = load_config(cfg_file)
        assert cfg.linkedin.cv_path.is_absolute()
        assert cfg.linkedin.cv_path.exists()

    def test_db_path_resolved_to_config_dir(self, tmp_path):
        cfg_file = _write_yaml(tmp_path, _base_yaml(tmp_path))
        cfg = load_config(cfg_file)
        assert cfg.application_settings.db_path.parent == tmp_path

    def test_filter_values(self, tmp_path):
        cfg_file = _write_yaml(tmp_path, _base_yaml(tmp_path))
        cfg = load_config(cfg_file)
        assert cfg.filters.salary_min == 60000
        assert cfg.filters.salary_max == 130000
        assert cfg.filters.remote_preference == "any"
        assert "full-time" in cfg.filters.job_types

    def test_email_config(self, tmp_path):
        cfg_file = _write_yaml(tmp_path, _base_yaml(tmp_path))
        cfg = load_config(cfg_file)
        assert cfg.email_notifications.smtp_port == 587
        assert cfg.email_notifications.enabled is True


# ---------------------------------------------------------------------------
# Missing / empty required fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    def test_missing_target_roles(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("target_roles:\n  - \"SOC Analyst\"", "target_roles: []")
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="target_roles"):
            load_config(cfg_file)

    def test_missing_linkedin_email(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace('email: "user@example.com"', 'email: ""')
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="email"):
            load_config(cfg_file)

    def test_missing_linkedin_password(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace('password: "secret"', 'password: ""')
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="password"):
            load_config(cfg_file)

    def test_cv_not_found(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("cv/test_cv.pdf", "cv/missing.pdf")
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(FileNotFoundError, match="CV file not found"):
            load_config(cfg_file)

    def test_config_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")


# ---------------------------------------------------------------------------
# Invalid enum values
# ---------------------------------------------------------------------------

class TestInvalidEnums:
    def test_invalid_remote_preference(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("remote_preference: any", "remote_preference: flying")
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="remote_preference"):
            load_config(cfg_file)

    def test_invalid_job_type(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("    - full-time", "    - moonlighting")
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="job_types"):
            load_config(cfg_file)


# ---------------------------------------------------------------------------
# Salary range validation
# ---------------------------------------------------------------------------

class TestSalaryValidation:
    def test_min_greater_than_max_raises(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace(
            "salary_min: 60000\n  salary_max: 130000",
            "salary_min: 130000\n  salary_max: 60000",
        )
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="salary_min"):
            load_config(cfg_file)

    def test_null_salary_is_valid(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace(
            "salary_min: 60000\n  salary_max: 130000",
            "salary_min: null\n  salary_max: null",
        )
        cfg_file = _write_yaml(tmp_path, yaml)
        cfg = load_config(cfg_file)
        assert cfg.filters.salary_min is None
        assert cfg.filters.salary_max is None


# ---------------------------------------------------------------------------
# SMTP port validation
# ---------------------------------------------------------------------------

class TestSmtpPort:
    def test_invalid_port_raises(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("smtp_port: 587", "smtp_port: 99999")
        cfg_file = _write_yaml(tmp_path, yaml)
        with pytest.raises(ValueError, match="smtp_port"):
            load_config(cfg_file)

    def test_port_465_valid(self, tmp_path):
        yaml = _base_yaml(tmp_path).replace("smtp_port: 587", "smtp_port: 465")
        cfg_file = _write_yaml(tmp_path, yaml)
        cfg = load_config(cfg_file)
        assert cfg.email_notifications.smtp_port == 465
