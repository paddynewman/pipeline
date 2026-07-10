import re

DEFAULT_SCRIPT_HEADER = "#!/bin/sh\nset -eux\n"
DEFAULT_MAX_BUILDS = 10
DEFAULT_MAX_CONCURRENT_JOBS = 2
DEFAULT_QUEUE_PAUSE_MESSAGE = "Job queue is paused."
DEFAULT_SMTP_PORT = 587

__all__ = [
    "DEFAULT_SCRIPT_HEADER",
    "DEFAULT_MAX_BUILDS",
    "DEFAULT_MAX_CONCURRENT_JOBS",
    "DEFAULT_QUEUE_PAUSE_MESSAGE",
    "DEFAULT_SMTP_PORT",
    "_normalize_max_concurrent_jobs",
    "_normalize_queue_paused",
    "_normalize_queue_pause_message",
    "_normalize_script_header",
    "_normalize_email_recipients",
    "_normalize_email_settings",
    "_normalize_mount_docker_socket",
    "_normalize_allow_rerun",
    "normalize_job_config",
    "_normalize_steps",
    "_normalize_step_image",
]


def _normalize_max_concurrent_jobs(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_MAX_CONCURRENT_JOBS
    return max(1, parsed)


def _normalize_queue_paused(value):
    if value is None:
        return False
    return bool(value)


def _normalize_queue_pause_message(value):
    text = str(value or "").strip()
    return text or DEFAULT_QUEUE_PAUSE_MESSAGE


def _normalize_script_header(value):
    text = str(value or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        return DEFAULT_SCRIPT_HEADER
    if not text.endswith("\n"):
        text += "\n"
    return text


def _normalize_email_recipients(value):
    if isinstance(value, list):
        parts = value
    else:
        parts = re.split(r"[\n,]+", str(value or ""))
    return [str(part).strip() for part in parts if str(part).strip()]


def _normalize_email_settings(value):
    raw = value if isinstance(value, dict) else {}
    try:
        port = int(raw.get("smtp_port", DEFAULT_SMTP_PORT))
    except (TypeError, ValueError):
        port = DEFAULT_SMTP_PORT
    if port < 1 or port > 65535:
        port = DEFAULT_SMTP_PORT
    security = str(raw.get("smtp_security") or "starttls").strip().lower()
    if security not in ("none", "starttls", "ssl"):
        security = "starttls"
    return {
        "recipients": _normalize_email_recipients(raw.get("recipients")),
        "from_address": str(raw.get("from_address") or "").strip(),
        "smtp_host": str(raw.get("smtp_host") or "").strip(),
        "smtp_port": port,
        "smtp_security": security,
        "smtp_username": str(raw.get("smtp_username") or "").strip(),
        "smtp_credential": str(raw.get("smtp_credential") or "").strip(),
    }


def _normalize_mount_docker_socket(value):
    if value is None:
        return False
    return bool(value)


def _normalize_allow_rerun(value):
    return True


def normalize_job_config(config):
    if not config:
        return None
    normalized = dict(config)
    normalized["steps"] = _normalize_steps(config)
    normalized["credentials"] = config.get("credentials") or []
    raw_labels = config.get("labels")
    if isinstance(raw_labels, list):
        normalized["labels"] = [
            str(l).strip().lower() for l in raw_labels if str(l).strip()
        ]
    else:
        normalized["labels"] = []
    raw_enabled = config.get("enabled")
    if raw_enabled is None:
        normalized["enabled"] = True
    else:
        normalized["enabled"] = bool(raw_enabled)
    raw_notify = config.get("notify_on_failure")
    if raw_notify is None:
        normalized["notify_on_failure"] = True
    else:
        normalized["notify_on_failure"] = bool(raw_notify)
    normalized["allow_rerun"] = _normalize_allow_rerun(config.get("allow_rerun"))
    trigger = config.get("trigger")
    if isinstance(trigger, dict):
        if trigger.get("type") == "cron":
            normalized["trigger"] = {
                "type": "cron",
                "schedule": str(trigger.get("schedule", "")).strip(),
            }
        elif trigger.get("type") == "gitpoll":
            interval = trigger.get("interval")
            if interval:
                try:
                    interval = int(interval)
                except Exception:
                    interval = None
            if interval and interval < 300:
                interval = 300
            normalized["trigger"] = {"type": "gitpoll"}
            if interval:
                normalized["trigger"]["interval"] = interval
        else:
            normalized["trigger"] = {"type": "manual"}
    else:
        normalized["trigger"] = {"type": "manual"}
    git = config.get("git")
    if isinstance(git, dict) and str(git.get("url", "")).strip():
        normalized["git"] = {
            "url": str(git["url"]).strip(),
            "branch": str(git.get("branch") or "main").strip() or "main",
            "credential": str(git.get("credential") or "").strip(),
            "shallow": bool(git.get("shallow", True)),
        }
    else:
        normalized.pop("git", None)
    raw = config.get("max_builds")
    if raw is not None:
        try:
            normalized["max_builds"] = max(1, int(raw))
        except (TypeError, ValueError):
            normalized.pop("max_builds", None)
    else:
        normalized.pop("max_builds", None)
    return normalized


def _normalize_steps(config):
    sections = config.get("steps")
    result = []
    if isinstance(sections, list):
        for index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            name = str(section.get("name") or "").strip() or f"Script {index + 1}"
            script = str(section.get("script") or "")
            result.append(
                {
                    "name": name,
                    "script": script,
                    "image": _normalize_step_image(section),
                    "reuse_container": bool(section.get("reuse_container", False)),
                }
            )
    return result


def _normalize_step_image(section):
    image = str(section.get("image") or "").strip()
    if image:
        return image
    raw = section.get("execution")
    if isinstance(raw, dict):
        return str(raw.get("image") or "").strip()
    return ""
