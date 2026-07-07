import base64
import datetime
import hashlib
import json
import os
import re
import secrets
import select
import shlex
import shutil
import smtplib
import ssl
import stat
import subprocess
import tempfile
import threading
import time
import email.message

from .jsonio import write_json

DEFAULT_SCRIPT_HEADER = "#!/bin/sh\nset -eux\n"
DEFAULT_MAX_BUILDS = 10
DEFAULT_MAX_CONCURRENT_JOBS = 2
DEFAULT_QUEUE_PAUSE_MESSAGE = "Job queue is paused."
DEFAULT_SMTP_PORT = 587
WEATHER_WINDOW = 5


def _cred_encrypt(key, plaintext):
    """Encrypt plaintext string using SHA-256 CTR mode, return base64 token."""
    nonce = secrets.token_bytes(16)
    data = plaintext.encode("utf-8")
    keystream = bytearray()
    block = 0
    while len(keystream) < len(data):
        h = hashlib.sha256(key + nonce + block.to_bytes(4, "big")).digest()
        keystream.extend(h)
        block += 1
    ct = bytes(a ^ b for a, b in zip(data, keystream))
    return base64.b64encode(nonce + ct).decode("ascii")


def _cred_decrypt(key, token):
    """Decrypt a base64 token produced by _cred_encrypt."""
    raw = base64.b64decode(token, validate=True)
    if len(raw) < 16:
        raise ValueError("token too short")
    nonce, ct = raw[:16], raw[16:]
    keystream = bytearray()
    block = 0
    while len(keystream) < len(ct):
        h = hashlib.sha256(key + nonce + block.to_bytes(4, "big")).digest()
        keystream.extend(h)
        block += 1
    return bytes(a ^ b for a, b in zip(ct, keystream)).decode("utf-8")


def _atomic_write_json(path, data):
    write_json(path, data)


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


def compute_weather(builds):
    recent = []
    for build in reversed(builds or []):
        status = build.get("status")
        if status == "running":
            continue
        if status not in ("success", "failure", "aborted"):
            continue
        recent.append(build)
        if len(recent) >= WEATHER_WINDOW:
            break
    if not recent:
        return None
    successes = sum(1 for build in recent if build.get("status") == "success")
    score = int(round((successes * 100.0) / len(recent)))
    if successes == len(recent):
        condition = "sunny"
    elif score >= 60:
        condition = "partly-cloudy"
    elif score >= 40:
        condition = "cloudy"
    elif score >= 20:
        condition = "rainy"
    else:
        condition = "stormy"
    return {
        "condition": condition,
        "score": score,
        "successes": successes,
        "total": len(recent),
    }


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


def _parse_cron_field(value, lo, hi):
    result = set()
    for part in value.split(","):
        part = part.strip()
        if "/" in part:
            range_part, step_str = part.rsplit("/", 1)
            try:
                step = int(step_str)
                if step < 1:
                    raise ValueError("step must be >= 1")
            except ValueError as exc:
                raise ValueError(f'Invalid step in "{part}": {exc}')
            if range_part == "*":
                start, end = lo, hi
            elif "-" in range_part:
                a, b = range_part.split("-", 1)
                start, end = int(a), int(b)
            else:
                start = end = int(range_part)
            result.update(range(start, end + 1, step))
        elif part == "*":
            result.update(range(lo, hi + 1))
        elif "-" in part:
            a, b = part.split("-", 1)
            result.update(range(int(a), int(b) + 1))
        else:
            result.add(int(part))
    for v in result:
        if v < lo or v > hi:
            raise ValueError(f"Value {v} out of range [{lo}, {hi}]")
    return result


def validate_cron(schedule):
    fields = schedule.strip().split()
    if len(fields) != 5:
        return "Schedule must have exactly 5 fields: minute hour day month weekday"
    ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    names = ["minute", "hour", "day", "month", "weekday"]
    for field, (lo, hi), name in zip(fields, ranges, names):
        try:
            _parse_cron_field(field, lo, hi)
        except ValueError as exc:
            return f'Invalid {name} field "{field}": {exc}'
    return None


def next_cron_run(schedule, now=None):
    if validate_cron(schedule):
        return None
    current = now or datetime.datetime.now()
    candidate = current.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    limit = candidate + datetime.timedelta(days=366)
    while candidate <= limit:
        if cron_matches(schedule, candidate):
            return candidate
        candidate += datetime.timedelta(minutes=1)
    return None


def cron_matches(schedule, dt):
    fields = schedule.strip().split()
    if len(fields) != 5:
        return False
    ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    # cron weekday: 0=Sunday … 6=Saturday; Python weekday(): 0=Monday … 6=Sunday
    weekday = (dt.weekday() + 1) % 7
    values = [dt.minute, dt.hour, dt.day, dt.month, weekday]
    for field, (lo, hi), value in zip(fields, ranges, values):
        try:
            if value not in _parse_cron_field(field, lo, hi):
                return False
        except ValueError:
            return False
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


class JobManager:
    def __init__(self, data_dir):
        self.data_dir = os.path.abspath(data_dir)
        self.jobs_dir = os.path.join(self.data_dir, "jobs")
        os.makedirs(self.jobs_dir, exist_ok=True)
        self._processes = {}  # (job_name, build_id) -> process
        self._lock = threading.Lock()
        self._queue_cond = threading.Condition(self._lock)
        self._queued_builds = []
        self._active_builds = set()
        self._git_pollers = {}  # job_name -> GitPollTrigger
        self._start_queue_runner()
        self._start_scheduler()
        self._start_git_pollers()

    def _start_queue_runner(self):
        t = threading.Thread(target=self._queue_runner_loop, daemon=True)
        t.start()

    def _queue_runner_loop(self):
        while True:
            with self._queue_cond:
                while True:
                    cfg = self.get_server_config()
                    paused = bool(cfg.get("queue_paused", False))
                    max_concurrent = _normalize_max_concurrent_jobs(
                        cfg.get("max_concurrent_jobs", DEFAULT_MAX_CONCURRENT_JOBS)
                    )
                    if (
                        not paused
                        and self._queued_builds
                        and len(self._active_builds) < max_concurrent
                    ):
                        queued = self._queued_builds.pop(0)
                        key = (queued["job_name"], queued["build_id"])
                        self._active_builds.add(key)
                        break
                    self._queue_cond.wait(timeout=1.0)

            thread = threading.Thread(
                target=self._run_queued_build,
                args=(queued,),
                daemon=True,
            )
            thread.start()

    def _run_queued_build(self, queued):
        info_path = queued["info_path"]
        with open(info_path) as f:
            info = json.load(f)
        info["status"] = "running"
        info["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _atomic_write_json(info_path, info)

        try:
            self._run_build(
                queued["job"],
                queued["build_id"],
                queued["build_dir"],
                queued["info_path"],
                queued["params"],
            )
        finally:
            with self._queue_cond:
                key = (queued["job_name"], queued["build_id"])
                self._active_builds.discard(key)
                self._queue_cond.notify_all()

    def _start_scheduler(self):
        t = threading.Thread(target=self._scheduler_loop, daemon=True)
        t.start()

    def _start_git_pollers(self):
        from .triggers.gitpoll import GitPollTrigger

        cfg = self.get_server_config()
        default_interval = cfg.get("git_poll_interval", 300)
        for job in self.list_jobs():
            trigger = job.get("trigger") or {}
            if trigger.get("type") != "gitpoll":
                continue
            interval = trigger.get("interval", default_interval)
            try:
                interval = int(interval)
            except Exception:
                interval = default_interval
            if interval < 300:
                interval = 300
            poller = GitPollTrigger(self, interval, job, self._on_git_poll_trigger)
            self._git_pollers[job["name"]] = poller
            poller.start()

    def _on_git_poll_trigger(self, job):
        params = {
            p["name"]: p.get("default", "")
            for p in (job.get("parameters") or [])
            if p.get("name")
        }
        self.trigger_build(job["name"], params, triggered_by="gitpoll")

    def _scheduler_loop(self):
        last_fired_minute = None
        while True:
            now = datetime.datetime.now()
            current_minute = (now.year, now.month, now.day, now.hour, now.minute)
            if current_minute != last_fired_minute:
                last_fired_minute = current_minute
                self._fire_scheduled_jobs(now)
            # Sleep until just after the next minute boundary
            time.sleep(60 - now.second + 1)

    def _fire_scheduled_jobs(self, now):
        try:
            jobs = self.list_jobs()
        except Exception:
            return
        for job in jobs:
            trigger = job.get("trigger") or {}
            if trigger.get("type") != "cron":
                continue
            schedule = trigger.get("schedule", "")
            if not schedule or not cron_matches(schedule, now):
                continue
            try:
                params = {
                    p["name"]: p.get("default", "")
                    for p in (job.get("parameters") or [])
                    if p.get("name")
                }
                self.trigger_build(job["name"], params, triggered_by="cron")
            except Exception:
                pass

    def _job_dir(self, name):
        return os.path.join(self.jobs_dir, name)

    def _build_dir(self, job_name, build_id):
        return os.path.join(self._job_dir(job_name), "builds", str(build_id))

    def _workspace_dir(self, job_name):
        return os.path.join(self._job_dir(job_name), "workspace")

    def list_workspace_files(self, job_name):
        workspace = self._workspace_dir(job_name)
        if not os.path.isdir(workspace):
            return []
        result = []
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in sorted(dirs) if not d.startswith(".")]
            for fname in sorted(f for f in files if not f.startswith(".")):
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, workspace)
                size = os.path.getsize(full)
                mtime = os.path.getmtime(full)
                result.append(
                    {
                        "path": rel,
                        "size": size,
                        "mtime": time.strftime(
                            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(mtime)
                        ),
                    }
                )
        return result

    def get_workspace_file(self, job_name, rel_path):
        workspace = self._workspace_dir(job_name)
        full = os.path.realpath(os.path.join(workspace, rel_path))
        if not full.startswith(
            os.path.realpath(workspace) + os.sep
        ) and full != os.path.realpath(workspace):
            return None
        if not os.path.isfile(full):
            return None
        return full

    def clear_workspace(self, job_name):
        workspace = self._workspace_dir(job_name)
        if os.path.isdir(workspace):
            shutil.rmtree(workspace)
        os.makedirs(workspace, exist_ok=True)

    def _credentials_path(self):
        return os.path.join(self.data_dir, "credentials.json")

    def _cred_key(self):
        """Return the 32-byte key used to encrypt credential values, creating it if needed."""
        key_path = os.path.join(self.data_dir, "credentials.key")
        if os.path.isfile(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        key = secrets.token_bytes(32)
        fd, tmp = tempfile.mkstemp(dir=self.data_dir)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(key)
            os.replace(tmp, key_path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return key

    def list_credentials(self):
        path = self._credentials_path()
        if not os.path.isfile(path):
            return []
        key = self._cred_key()
        with open(path) as f:
            raw = json.load(f)
        result = []
        for c in raw:
            entry = dict(c)
            token = entry.get("value", "")
            try:
                entry["value"] = _cred_decrypt(key, token)
            except Exception:
                pass  # leave as-is if decryption fails (e.g. legacy plain text)
            result.append(entry)
        return result

    def get_credential(self, name):
        for c in self.list_credentials():
            if c["name"] == name:
                return c
        return None

    def save_credential(self, name, value, description=""):
        key = self._cred_key()
        path = self._credentials_path()
        raw = []
        if os.path.isfile(path):
            with open(path) as f:
                raw = json.load(f)
        token = _cred_encrypt(key, value)
        for c in raw:
            if c["name"] == name:
                c["value"] = token
                c["description"] = description
                break
        else:
            raw.append({"name": name, "value": token, "description": description})
        write_json(path, raw)

    def delete_credential(self, name):
        path = self._credentials_path()
        if not os.path.isfile(path):
            return
        with open(path) as f:
            raw = json.load(f)
        raw = [c for c in raw if c["name"] != name]
        write_json(path, raw)

    def _server_config_path(self):
        return os.path.join(self.data_dir, "server.json")

    def get_server_config(self):
        path = self._server_config_path()
        if not os.path.isfile(path):
            return {
                "max_builds": DEFAULT_MAX_BUILDS,
                "max_concurrent_jobs": DEFAULT_MAX_CONCURRENT_JOBS,
                "queue_paused": False,
                "queue_pause_message": DEFAULT_QUEUE_PAUSE_MESSAGE,
                "default_script_header": _normalize_script_header(None),
                "mount_docker_socket": False,
                "email_notifications": _normalize_email_settings(None),
                "git_poll_interval": 300,
            }
        with open(path) as f:
            cfg = json.load(f)
        if "max_builds" not in cfg:
            cfg["max_builds"] = DEFAULT_MAX_BUILDS
        cfg["max_concurrent_jobs"] = _normalize_max_concurrent_jobs(
            cfg.get("max_concurrent_jobs", DEFAULT_MAX_CONCURRENT_JOBS)
        )
        cfg["queue_paused"] = _normalize_queue_paused(cfg.get("queue_paused"))
        cfg["queue_pause_message"] = _normalize_queue_pause_message(
            cfg.get("queue_pause_message")
        )
        if "git_poll_interval" not in cfg:
            cfg["git_poll_interval"] = 300
        cfg["default_script_header"] = _normalize_script_header(
            cfg.get("default_script_header")
        )
        cfg["mount_docker_socket"] = _normalize_mount_docker_socket(
            cfg.get("mount_docker_socket")
        )
        cfg["email_notifications"] = _normalize_email_settings(
            cfg.get("email_notifications")
        )
        return cfg

    def save_server_config(self, cfg):
        cfg = dict(cfg)
        cfg["max_concurrent_jobs"] = _normalize_max_concurrent_jobs(
            cfg.get("max_concurrent_jobs", DEFAULT_MAX_CONCURRENT_JOBS)
        )
        cfg["queue_paused"] = _normalize_queue_paused(cfg.get("queue_paused"))
        cfg["queue_pause_message"] = _normalize_queue_pause_message(
            cfg.get("queue_pause_message")
        )
        cfg["default_script_header"] = _normalize_script_header(
            cfg.get("default_script_header")
        )
        cfg["mount_docker_socket"] = _normalize_mount_docker_socket(
            cfg.get("mount_docker_socket")
        )
        cfg["email_notifications"] = _normalize_email_settings(
            cfg.get("email_notifications")
        )
        write_json(self._server_config_path(), cfg)
        with self._queue_cond:
            self._queue_cond.notify_all()

    def list_jobs(self):
        jobs = []
        if not os.path.isdir(self.jobs_dir):
            return jobs
        for name in sorted(os.listdir(self.jobs_dir)):
            config_path = os.path.join(self._job_dir(name), "config.json")
            if os.path.isfile(config_path):
                with open(config_path) as f:
                    config = normalize_job_config(json.load(f))
                builds = self.list_builds(name)
                config["last_build"] = builds[-1] if builds else None
                config["weather"] = compute_weather(builds)
                jobs.append(config)
        return jobs

    def get_job(self, name):
        config_path = os.path.join(self._job_dir(name), "config.json")
        if not os.path.isfile(config_path):
            return None
        with open(config_path) as f:
            return normalize_job_config(json.load(f))

    def save_job(self, config):
        config = normalize_job_config(config)
        name = config["name"]
        job_dir = self._job_dir(name)
        os.makedirs(job_dir, exist_ok=True)
        write_json(os.path.join(job_dir, "config.json"), config)
        # Restart git poller if needed
        trigger = config.get("trigger") or {}
        if trigger.get("type") == "gitpoll":
            from .triggers.gitpoll import GitPollTrigger

            cfg = self.get_server_config()
            default_interval = cfg.get("git_poll_interval", 300)
            interval = trigger.get("interval", default_interval)
            try:
                interval = int(interval)
            except Exception:
                interval = default_interval
            if interval < 300:
                interval = 300
            if name in self._git_pollers:
                self._git_pollers[name].stop()
            poller = GitPollTrigger(self, interval, config, self._on_git_poll_trigger)
            self._git_pollers[name] = poller
            poller.start()
        elif name in self._git_pollers:
            self._git_pollers[name].stop()
            del self._git_pollers[name]

    def delete_job(self, name):
        job_dir = self._job_dir(name)
        if os.path.isdir(job_dir):
            shutil.rmtree(job_dir)

    def list_builds(self, job_name):
        builds_dir = os.path.join(self._job_dir(job_name), "builds")
        if not os.path.isdir(builds_dir):
            return []
        build_ids = sorted(int(x) for x in os.listdir(builds_dir) if x.isdigit())
        builds = []
        for build_id in build_ids:
            info_path = os.path.join(builds_dir, str(build_id), "info.json")
            if os.path.isfile(info_path):
                with open(info_path) as f:
                    builds.append(json.load(f))
        return builds

    def get_build(self, job_name, build_id):
        info_path = os.path.join(self._build_dir(job_name, build_id), "info.json")
        if not os.path.isfile(info_path):
            return None
        with open(info_path) as f:
            return json.load(f)

    def _redact_log(self, text, job_name):
        job = self.get_job(job_name)
        if not job:
            return text
        for binding in job.get("credentials") or []:
            cred = self.get_credential(binding.get("credential", ""))
            if not cred:
                continue
            value = cred.get("value", "")
            if value:
                text = text.replace(value, "<HIDDEN>")
        return text

    def get_build_log(self, job_name, build_id):
        build = self.get_build(job_name, build_id)
        if not build:
            return ""
        names = [section["name"] for section in build.get("sections") or []]
        parts = []
        git_log = self.get_build_git_log(job_name, build_id)
        if git_log and "Git Checkout" not in names:
            parts.append(f"=== Git Checkout ===\n{git_log}")
        for i, section in enumerate(build.get("sections") or []):
            text = self.get_build_section_log(job_name, build_id, i + 1)
            parts.append(f'=== {section["name"]} ===\n{text}')
        return "\n".join(parts)

    def get_build_section_log(self, job_name, build_id, section_num):
        log_path = os.path.join(
            self._build_dir(job_name, build_id), "script-%d.log" % section_num
        )
        if not os.path.isfile(log_path):
            return ""
        with open(log_path, errors="replace", newline="") as f:
            return self._redact_log(f.read(), job_name)

    def get_build_section_script(self, job_name, build_id, section_num):
        script_path = os.path.join(
            self._build_dir(job_name, build_id), "script-%d.sh" % section_num
        )
        if not os.path.isfile(script_path):
            return ""
        with open(script_path, errors="replace") as f:
            return f.read()

    def get_build_git_log(self, job_name, build_id):
        log_path = os.path.join(self._build_dir(job_name, build_id), "git.log")
        if not os.path.isfile(log_path):
            return None
        with open(log_path, errors="replace", newline="") as f:
            return f.read()

    def get_build_section_logs(self, job_name, build_id):
        build = self.get_build(job_name, build_id)
        if not build:
            return []
        sections = [
            {
                "name": s["name"],
                "details": s.get("details", ""),
                "text": self.get_build_section_log(job_name, build_id, i + 1),
                "script": self.get_build_section_script(job_name, build_id, i + 1),
            }
            for i, s in enumerate(build.get("sections") or [])
        ]
        git_log = self.get_build_git_log(job_name, build_id)
        if git_log and not any(
            section["name"] == "Git Checkout" for section in sections
        ):
            sections.insert(
                0,
                {"name": "Git Checkout", "details": "", "text": git_log, "script": ""},
            )
        return sections

    def _next_build_id(self, job_name):
        builds_dir = os.path.join(self._job_dir(job_name), "builds")
        if not os.path.isdir(builds_dir):
            return 1
        ids = [int(x) for x in os.listdir(builds_dir) if x.isdigit()]
        return max(ids) + 1 if ids else 1

    def trigger_build(self, job_name, params, triggered_by=None):
        job = self.get_job(job_name)
        if not job:
            return None

        execution_sections = self._execution_sections(job)

        with self._lock:
            build_id = self._next_build_id(job_name)
            build_dir = self._build_dir(job_name, build_id)
            os.makedirs(build_dir, exist_ok=True)
            info = {
                "id": build_id,
                "job": job_name,
                "status": "queued",
                "queued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "started_at": None,
                "finished_at": None,
                "parameters": params,
                "triggered_by": triggered_by,
                "duration": None,
                "exit_code": None,
                "sections": [
                    {
                        "name": s["name"],
                        "status": "pending",
                        "details": self._section_details(s),
                    }
                    for s in execution_sections
                ],
            }
            info_path = os.path.join(build_dir, "info.json")
            _atomic_write_json(info_path, info)

            self._queued_builds.append(
                {
                    "job": job,
                    "job_name": job_name,
                    "build_id": build_id,
                    "build_dir": build_dir,
                    "info_path": info_path,
                    "params": params,
                }
            )
            self._queue_cond.notify_all()
        return build_id

    def _execution_sections(self, job):
        sections = []
        git_cfg = job.get("git")
        if git_cfg:
            sections.append(
                {
                    "kind": "git",
                    "name": "Git Checkout",
                    "script": self._git_checkout_script(git_cfg),
                }
            )
        for i, section in enumerate(job.get("steps") or []):
            sections.append(
                {
                    "kind": "script",
                    "name": section.get("name") or f"Script {i + 1}",
                    "script": section.get("script", ""),
                    "image": _normalize_step_image(section),
                    "reuse_container": bool(section.get("reuse_container", False)),
                }
            )
        return sections

    def _section_details(self, section):
        if section.get("kind") != "script":
            return ""
        image = section.get("image") or ""
        if image:
            return image
        return ""

    def _git_checkout_script(self, git_cfg):
        url = git_cfg["url"]
        branch = git_cfg.get("branch") or "main"
        shallow = git_cfg.get("shallow", True)
        depth_args = " --depth 1" if shallow else ""
        quoted_url = shlex.quote(url)
        quoted_branch = shlex.quote(branch)
        return "\n".join(
            [
                'project_dir="$WORKSPACE/project"',
                'rm -rf "$project_dir"',
                f'git clone{depth_args} -b {quoted_branch} -- {quoted_url} "$project_dir"',
            ]
        )

    def _git_checkout_env(self, git_cfg):
        cred_name = git_cfg.get("credential") or ""
        ssh_key_path = None

        git_env = {}
        git_env["GIT_TERMINAL_PROMPT"] = "0"

        if cred_name:
            cred = self.get_credential(cred_name)
            if cred:
                fd, ssh_key_path = tempfile.mkstemp(prefix="pipeline-git-key-")
                os.close(fd)
                with open(ssh_key_path, "w") as f:
                    f.write(cred["value"])
                os.chmod(ssh_key_path, stat.S_IRUSR | stat.S_IWUSR)
                git_env["GIT_SSH_COMMAND"] = (
                    f"ssh -i {ssh_key_path} "
                    f"-o StrictHostKeyChecking=no -o IdentitiesOnly=yes"
                )
        return git_env, ssh_key_path

    def _run_build(self, job, build_id, build_dir, info_path, params):
        start_time = time.time()
        execution_sections = self._execution_sections(job)
        git_cfg = job.get("git")

        workspace_dir = self._workspace_dir(job["name"])
        if git_cfg:
            os.makedirs(workspace_dir, exist_ok=True)
        else:
            if os.path.isdir(workspace_dir):
                shutil.rmtree(workspace_dir)
            os.makedirs(workspace_dir)

        env = {}
        env["JOB_NAME"] = job["name"]
        env["BUILD_ID"] = str(build_id)
        env["BUILD_DIR"] = build_dir
        env["WORKSPACE"] = workspace_dir
        for k, v in params.items():
            env[k] = str(v)

        cred_bindings = job.get("credentials") or []
        creds_ready = False

        exit_code = -1
        last_index = 0
        active_container = None
        try:
            for index, section in enumerate(execution_sections):
                last_index = index
                if section["kind"] != "git" and not creds_ready and cred_bindings:
                    cred_dir = os.path.join(workspace_dir, ".credentials")
                    os.makedirs(cred_dir, exist_ok=True)
                    os.chmod(cred_dir, stat.S_IRWXU)
                    for binding in cred_bindings:
                        cred_name = binding.get("credential", "")
                        env_var = binding.get("env_var", "")
                        bind_type = binding.get("type", "value")
                        if not cred_name or not env_var:
                            continue
                        cred = self.get_credential(cred_name)
                        if not cred:
                            continue
                        if bind_type == "file":
                            cred_file = os.path.join(
                                workspace_dir, ".credentials", env_var
                            )
                            with open(cred_file, "w") as cf:
                                cf.write(cred["value"])
                            os.chmod(cred_file, stat.S_IRUSR | stat.S_IWUSR)
                            env[env_var] = cred_file
                        else:
                            env[env_var] = cred["value"]
                    creds_ready = True

                script_content = self._prepare_script(
                    section.get("script", ""),
                    image=section.get("image"),
                )
                script_path = os.path.join(build_dir, "script-%d.sh" % (index + 1))
                with open(script_path, "w") as f:
                    f.write(script_content)
                os.chmod(script_path, stat.S_IRWXU)

                section_log_path = os.path.join(
                    build_dir, "script-%d.log" % (index + 1)
                )
                self._update_section_status(info_path, index, "running")

                section_env = env
                cleanup_path = None
                if section["kind"] == "git":
                    section_env, cleanup_path = self._git_checkout_env(git_cfg)
                    section_env.update(env)

                try:
                    with open(section_log_path, "w", newline="") as section_log:
                        if section["kind"] == "script":
                            reuse = section.get("reuse_container", False) and (
                                active_container is not None
                            )
                            if not reuse and active_container is not None:
                                self._stop_container(active_container["name"])
                                active_container = None
                            need_persistent = self._next_section_reuses_container(
                                execution_sections, index
                            )
                            if reuse:
                                exit_code = self._exec_script_in_container(
                                    active_container["name"],
                                    script_path,
                                    section_log,
                                    section_env,
                                    workspace_dir,
                                    build_dir,
                                    job["name"],
                                    build_id,
                                )
                            elif need_persistent:
                                container_name = self._make_container_name(
                                    job["name"], build_id, index
                                )
                                started = self._start_shared_container(
                                    container_name,
                                    section["image"] or "alpine:latest",
                                    section_env,
                                    workspace_dir,
                                    build_dir,
                                    section_log,
                                )
                                if not started:
                                    exit_code = 1
                                else:
                                    active_container = {"name": container_name}
                                    exit_code = self._exec_script_in_container(
                                        container_name,
                                        script_path,
                                        section_log,
                                        section_env,
                                        workspace_dir,
                                        build_dir,
                                        job["name"],
                                        build_id,
                                    )
                            else:
                                exit_code = self._run_docker_script_live(
                                    section,
                                    script_path,
                                    section_log,
                                    section_env,
                                    workspace_dir,
                                    build_dir,
                                    job["name"],
                                    build_id,
                                )
                        else:
                            exit_code = self._run_script_live(
                                script_path,
                                section_log,
                                section_env,
                                workspace_dir,
                                job["name"],
                                build_id,
                            )
                finally:
                    if cleanup_path and os.path.exists(cleanup_path):
                        os.unlink(cleanup_path)

                if exit_code == 0:
                    self._update_section_status(info_path, index, "success")
                    continue

                if active_container is not None:
                    self._stop_container(active_container["name"])
                    active_container = None
                self._update_section_status(info_path, index, "failure")
                for pending_index in range(index + 1, len(execution_sections)):
                    self._update_section_status(info_path, pending_index, "aborted")
                break
        except Exception as exc:  # noqa: BLE001
            self._update_section_status(info_path, last_index, "failure")
            for pending_index in range(last_index + 1, len(execution_sections)):
                self._update_section_status(info_path, pending_index, "aborted")
            if exit_code == -1:
                exit_code = 1
            section_log_path = os.path.join(
                build_dir, "script-%d.log" % (last_index + 1)
            )
            with open(section_log_path, "a", newline="") as section_log:
                section_log.write(f"\n[Error] {exc}\n")
        finally:
            if active_container is not None:
                self._stop_container(active_container["name"])
                active_container = None
            cred_dir = os.path.join(workspace_dir, ".credentials")
            if os.path.isdir(cred_dir):
                shutil.rmtree(cred_dir, ignore_errors=True)
            with self._lock:
                self._processes.pop((job["name"], build_id), None)

        duration = time.time() - start_time
        if exit_code == 0:
            status = "success"
        elif exit_code in (-15, 143):
            status = "aborted"
        else:
            status = "failure"

        with open(info_path) as f:
            info = json.load(f)
        info["status"] = status
        info["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        info["duration"] = round(duration, 1)
        info["exit_code"] = exit_code
        _atomic_write_json(info_path, info)

        if status == "failure" and job.get("notify_on_failure", True):
            try:
                self._send_failure_notification(job, info)
            except Exception as exc:
                self._write_notification_log(
                    build_dir, "Failed to send notification email: %s" % exc
                )

        self._prune_builds(job["name"], job)

    def _write_notification_log(self, build_dir, message):
        path = os.path.join(build_dir, "notification.log")
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(path, "a") as f:
            f.write("[%s] %s\n" % (stamp, message))

    def _failure_notification_body(self, job, build):
        lines = [
            "Job: %s" % job["name"],
            "Build: #%s" % build["id"],
            "Status: %s" % build.get("status", "failure"),
            "Started: %s" % build.get("started_at", ""),
            "Finished: %s" % build.get("finished_at", ""),
            "Duration: %s seconds" % build.get("duration", ""),
        ]
        triggered_by = build.get("triggered_by")
        if triggered_by:
            lines.append("Triggered by: %s" % triggered_by)
        failed_sections = [
            section.get("name", "")
            for section in (build.get("sections") or [])
            if section.get("status") == "failure"
        ]
        if failed_sections:
            lines.append("Failed sections: %s" % ", ".join(failed_sections))
        params = build.get("parameters") or {}
        if params:
            lines.append(
                "Parameters: %s"
                % ", ".join("%s=%s" % (k, v) for k, v in sorted(params.items()))
            )
        log_text = self.get_build_log(job["name"], build["id"]).strip()
        if log_text:
            tail_lines = log_text.splitlines()[-120:]
            tail_text = "\n".join(tail_lines)
            if len(tail_text) > 8000:
                tail_text = tail_text[-8000:]
            lines.extend(["", "Logs:", "", tail_text])
        return "\n".join(lines).strip() + "\n"

    def _send_failure_notification(self, job, build):
        settings = self.get_server_config().get("email_notifications") or {}
        recipients = settings.get("recipients") or []
        smtp_host = settings.get("smtp_host", "")
        if not recipients or not smtp_host:
            return
        from_address = (
            settings.get("from_address")
            or settings.get("smtp_username")
            or recipients[0]
        )
        smtp_port = settings.get("smtp_port", DEFAULT_SMTP_PORT)
        smtp_security = settings.get("smtp_security", "starttls")
        smtp_username = settings.get("smtp_username", "")
        credential_name = settings.get("smtp_credential", "")
        password = ""
        if credential_name:
            cred = self.get_credential(credential_name)
            if not cred:
                raise RuntimeError(
                    'SMTP credential "%s" was not found' % credential_name
                )
            password = cred.get("value", "")

        msg = email.message.EmailMessage()
        msg["Subject"] = "[Pipeline] Job failed: %s #%s" % (job["name"], build["id"])
        msg["From"] = from_address
        msg["To"] = ", ".join(recipients)
        msg.set_content(self._failure_notification_body(job, build))

        if smtp_security == "ssl":
            smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20)
        else:
            smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=20)
        with smtp:
            smtp.ehlo()
            if smtp_security == "starttls":
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if smtp_username and credential_name:
                smtp.login(smtp_username, password)
            smtp.send_message(msg)

    def _prune_builds(self, job_name, job):
        limit = job.get("max_builds")
        if limit is None:
            server_cfg = self.get_server_config()
            limit = server_cfg.get("max_builds", DEFAULT_MAX_BUILDS)
        builds_dir = os.path.join(self._job_dir(job_name), "builds")
        if not os.path.isdir(builds_dir):
            return
        ids = sorted(int(x) for x in os.listdir(builds_dir) if x.isdigit())
        to_delete = ids[: max(0, len(ids) - limit)]
        for bid in to_delete:
            shutil.rmtree(os.path.join(builds_dir, str(bid)), ignore_errors=True)

    def _update_section_status(self, info_path, section_idx, status):
        with open(info_path) as f:
            info = json.load(f)
        info["sections"][section_idx]["status"] = status
        _atomic_write_json(info_path, info)

    def cancel_build(self, job_name, build_id):
        key = (job_name, int(build_id))
        with self._lock:
            process = self._processes.get(key)
            if process:
                process.terminate()
                return True

            for index, queued in enumerate(self._queued_builds):
                if (queued["job_name"], queued["build_id"]) != key:
                    continue
                removed = self._queued_builds.pop(index)
                info_path = removed["info_path"]
                with open(info_path) as f:
                    info = json.load(f)
                info["status"] = "aborted"
                info["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                info["duration"] = 0.0
                info["exit_code"] = -15
                _atomic_write_json(info_path, info)
                self._queue_cond.notify_all()
                return True
        return False

    def is_running(self, job_name, build_id):
        with self._lock:
            key = (job_name, int(build_id))
            return key in self._active_builds

    def get_queue_state(self):
        cfg = self.get_server_config()
        with self._lock:
            queued = len(self._queued_builds)
            running = len(self._active_builds)
        return {
            "paused": bool(cfg.get("queue_paused", False)),
            "pause_message": cfg.get(
                "queue_pause_message", DEFAULT_QUEUE_PAUSE_MESSAGE
            ),
            "max_concurrent_jobs": _normalize_max_concurrent_jobs(
                cfg.get("max_concurrent_jobs", DEFAULT_MAX_CONCURRENT_JOBS)
            ),
            "queued_count": queued,
            "running_count": running,
        }

    def _run_script_live(
        self, script_path, log_file, env, build_dir, job_name, build_id
    ):
        return self._run_process_live(
            [script_path], log_file, env, build_dir, job_name, build_id
        )

    def _run_process_live(self, command, log_file, env, cwd, job_name, build_id):
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=cwd,
            close_fds=True,
        )
        stream = process.stdout
        if stream is None:
            return 1
        stream_fd = stream.fileno()

        with self._lock:
            self._processes[(job_name, build_id)] = process

        try:
            while True:
                ready, _, _ = select.select([stream_fd], [], [], 0.2)
                if ready:
                    chunk = os.read(stream_fd, 4096)
                    if chunk:
                        text = chunk.decode("utf-8", errors="replace")
                        text = text.replace("\r\n", "\n").replace("\r", "\n")
                        log_file.write(text)
                        log_file.flush()
                        continue
                if process.poll() is not None:
                    while True:
                        chunk = os.read(stream_fd, 4096)
                        if not chunk:
                            break
                        text = chunk.decode("utf-8", errors="replace")
                        text = text.replace("\r\n", "\n").replace("\r", "\n")
                        log_file.write(text)
                    log_file.flush()
                    return process.returncode
        finally:
            with self._lock:
                self._processes.pop((job_name, build_id), None)
            stream.close()

    def _run_docker_script_live(
        self,
        section,
        script_path,
        log_file,
        env,
        workspace_dir,
        build_dir,
        job_name,
        build_id,
    ):
        image = section.get("image", "")
        if not image:
            log_file.write("[Docker] Script sections must define a Docker image.\n")
            log_file.flush()
            return 1
        return self._run_local_docker_script_live(
            image,
            script_path,
            log_file,
            env,
            workspace_dir,
            build_dir,
            job_name,
            build_id,
        )

    def _run_local_docker_script_live(
        self,
        image,
        script_path,
        log_file,
        env,
        workspace_dir,
        build_dir,
        job_name,
        build_id,
    ):
        docker_env = self._docker_env(env, workspace_dir, build_dir)
        command = self._docker_run_command(
            image,
            docker_env,
            os.path.realpath(workspace_dir),
            os.path.realpath(build_dir),
            "/build/%s" % os.path.basename(script_path),
        )
        return self._run_process_live(
            command, log_file, os.environ.copy(), build_dir, job_name, build_id
        )

    def _docker_env(self, env, workspace_dir, build_dir):
        workspace_dir = os.path.realpath(workspace_dir)
        build_dir = os.path.realpath(build_dir)
        docker_env = {}
        for key, value in env.items():
            text = str(value)
            text = self._remap_env_path(text, workspace_dir, "/workspace")
            text = self._remap_env_path(text, build_dir, "/build")
            docker_env[key] = text
        docker_env["WORKSPACE"] = "/workspace"
        docker_env["BUILD_DIR"] = "/build"
        return docker_env

    def _remap_env_path(self, value, host_root, container_root):
        if value == host_root:
            return container_root
        prefix = host_root + os.sep
        if value.startswith(prefix):
            suffix = value[len(host_root) :].replace(os.sep, "/")
            return container_root + suffix
        return value

    def _docker_run_command(self, image, env, workspace_dir, build_dir, script_path):
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "-v",
            "%s:/workspace" % workspace_dir,
            "-v",
            "%s:/build" % build_dir,
            "-w",
            "/workspace",
        ]
        if self.get_server_config().get("mount_docker_socket", True) and os.path.exists(
            "/var/run/docker.sock"
        ):
            command.extend(["-v", "/var/run/docker.sock:/var/run/docker.sock"])
        for key in sorted(env):
            command.extend(["-e", "%s=%s" % (key, env[key])])
        command.extend([image, "/bin/sh", script_path])
        return command

    def _make_container_name(self, job_name, build_id, section_index):
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "-", job_name)[:50]
        return "pipeline-%s-%s-%s" % (safe, build_id, section_index)

    def _start_shared_container(
        self, container_name, image, env, workspace_dir, build_dir, log_file
    ):
        docker_env = self._docker_env(env, workspace_dir, build_dir)
        ws = os.path.realpath(workspace_dir)
        bd = os.path.realpath(build_dir)
        command = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-v",
            "%s:/workspace" % ws,
            "-v",
            "%s:/build" % bd,
            "-w",
            "/workspace",
        ]
        if self.get_server_config().get("mount_docker_socket", True) and os.path.exists(
            "/var/run/docker.sock"
        ):
            command.extend(["-v", "/var/run/docker.sock:/var/run/docker.sock"])
        for key in sorted(docker_env):
            command.extend(["-e", "%s=%s" % (key, docker_env[key])])
        command.extend([image, "sleep", "infinity"])
        try:
            result = subprocess.run(
                command, capture_output=True, timeout=60, env=os.environ.copy()
            )
            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace")
                log_file.write("[Docker] Failed to start container: %s\n" % stderr)
                log_file.flush()
                return False
            return True
        except Exception as exc:
            log_file.write("[Docker] Failed to start container: %s\n" % exc)
            log_file.flush()
            return False

    def _exec_script_in_container(
        self,
        container_name,
        script_path,
        log_file,
        env,
        workspace_dir,
        build_dir,
        job_name,
        build_id,
    ):
        docker_env = self._docker_env(env, workspace_dir, build_dir)
        command = ["docker", "exec", "-w", "/workspace"]
        for key in sorted(docker_env):
            command.extend(["-e", "%s=%s" % (key, docker_env[key])])
        command.extend(
            [container_name, "/bin/sh", "/build/%s" % os.path.basename(script_path)]
        )
        return self._run_process_live(
            command, log_file, os.environ.copy(), build_dir, job_name, build_id
        )

    def _stop_container(self, container_name):
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                timeout=30,
                env=os.environ.copy(),
            )
        except Exception:
            pass

    def _next_section_reuses_container(self, sections, index):
        if index + 1 < len(sections):
            nxt = sections[index + 1]
            return nxt.get("kind") == "script" and bool(
                nxt.get("reuse_container", False)
            )
        return False

    def _prepare_script(self, script_content, image=""):
        if script_content.startswith("#!"):
            return script_content
        header = self.get_server_config().get(
            "default_script_header", DEFAULT_SCRIPT_HEADER
        )
        return header + script_content
