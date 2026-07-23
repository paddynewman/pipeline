import http.server
import json
import logging
import re
import sys
import urllib.parse
from collections import namedtuple

from . import ui
from .auth import AuthManager
from .jobs import JobManager, compute_weather
from .cron import next_cron_run, validate_cron

_access_log = logging.getLogger("pipeline.access")

_JOB_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")


def _valid_job_name(name):
    return bool(name and _JOB_NAME_RE.match(name))


def _valid_build_id(bid):
    try:
        return int(bid) > 0
    except (TypeError, ValueError):
        return False


def _valid_cred_name(name):
    return _valid_job_name(name)


def _valid_template_name(name):
    return _valid_job_name(name)


def _compile_param_regex(pattern):
    if not pattern:
        return None
    return re.compile(pattern)


def _validate_build_params(job, params):
    for p in job.get("parameters") or []:
        name = p.get("name", "")
        pattern = p.get("regex", "")
        if not name or not pattern:
            continue
        if not _compile_param_regex(pattern).fullmatch(params.get(name, "")):
            return f'Parameter "{name}" must match regex: {pattern}'
    return None


# ── Route table ──────────────────────────────────────────────────────────────
#
# Each Route maps an HTTP method + URL pattern to a handler method (referenced by
# name). Pattern segments wrapped in ``{}`` capture a single path segment and are
# passed to the handler as positional arguments in the order they appear; a
# trailing ``{name*}`` segment captures the remaining path (joined with "/").
#
#   roles       tuple of roles allowed to access the route (None = any logged-in)
#   wants_query if True, the parsed query dict is passed as the final argument
#   check       name of a custom permission method called with the captured args
#   public      if True, no authentication is required (login/setup pages)
Route = namedtuple(
    "Route",
    "method pattern handler roles wants_query check public",
    defaults=(None, False, None, False),
)

ROUTES = [
    # Public (no authentication required)
    Route("GET", "/login", "_get_login", public=True),
    Route("POST", "/login", "_post_login", public=True),
    Route("GET", "/setup", "_get_setup", public=True),
    Route("POST", "/setup", "_post_setup", public=True),
    # GET
    Route("GET", "/", "_get_dashboard"),
    Route("GET", "/logout", "_get_logout"),
    Route("GET", "/api/queue", "_get_queue_status"),
    Route("GET", "/api/dashboard", "_get_dashboard_status"),
    Route(
        "GET", "/cron/preview", "_get_cron_preview", roles=("admin",), wants_query=True
    ),
    Route("GET", "/jobs/new", "_get_job_new", roles=("admin",)),
    Route("GET", "/jobs/{name}", "_get_job_detail"),
    Route("GET", "/jobs/{name}/builds.json", "_get_job_builds_status"),
    Route("GET", "/jobs/{name}/gitpoll-log", "_get_gitpoll_log"),
    Route("GET", "/jobs/{name}/gitpoll-log.txt", "_get_gitpoll_log_text"),
    Route("GET", "/jobs/{name}/edit", "_get_job_edit", roles=("admin",)),
    Route(
        "GET",
        "/jobs/{name}/build",
        "_get_build_form",
        roles=("admin", "user"),
        wants_query=True,
    ),
    Route("GET", "/jobs/{name}/builds/{bid}", "_get_build_detail"),
    Route("GET", "/jobs/{name}/builds/{bid}/log", "_get_build_log"),
    Route(
        "GET",
        "/jobs/{name}/builds/{bid}/log/{section}",
        "_get_build_section_log_text",
    ),
    Route("GET", "/jobs/{name}/builds/{bid}/status", "_get_build_status"),
    Route(
        "GET",
        "/jobs/{name}/workspace",
        "_get_workspace",
        roles=("admin", "user", "viewer"),
    ),
    Route(
        "GET",
        "/jobs/{name}/workspace/{path*}",
        "_get_workspace_file",
        roles=("admin", "user", "viewer"),
    ),
    Route("GET", "/credentials", "_get_credentials_list", roles=("admin",)),
    Route("GET", "/credentials/new", "_get_credential_new", roles=("admin",)),
    Route("GET", "/credentials/{name}/edit", "_get_credential_edit", roles=("admin",)),
    Route("GET", "/templates", "_get_templates_list", roles=("admin",)),
    Route("GET", "/templates/new", "_get_template_new", roles=("admin",)),
    Route("GET", "/templates/{name}/edit", "_get_template_edit", roles=("admin",)),
    Route("GET", "/settings", "_get_settings", roles=("admin",)),
    Route("GET", "/settings/users", "_get_users_list", roles=("admin",)),
    Route("GET", "/settings/users/new", "_get_user_new", roles=("admin",)),
    Route("GET", "/settings/users/{name}/edit", "_get_user_edit", roles=("admin",)),
    Route(
        "GET",
        "/settings/users/{name}/password",
        "_get_user_password",
        check="_can_manage_password",
    ),
    # POST
    Route("POST", "/jobs/new", "_post_job_create", roles=("admin",)),
    Route("POST", "/jobs/{name}/edit", "_post_job_update", roles=("admin",)),
    Route("POST", "/jobs/{name}/delete", "_post_job_delete", roles=("admin",)),
    Route("POST", "/jobs/{name}/build", "_post_job_trigger", roles=("admin", "user")),
    Route(
        "POST",
        "/jobs/{name}/workspace/clear",
        "_post_workspace_clear",
        roles=("admin",),
    ),
    Route(
        "POST",
        "/jobs/{name}/builds/{bid}/cancel",
        "_post_build_cancel",
        roles=("admin", "user"),
    ),
    Route(
        "POST",
        "/jobs/{name}/builds/{bid}/rerun",
        "_post_build_rerun",
        roles=("admin", "user"),
    ),
    Route("POST", "/credentials/new", "_post_credential_create", roles=("admin",)),
    Route(
        "POST",
        "/credentials/{name}/edit",
        "_post_credential_update",
        roles=("admin",),
    ),
    Route(
        "POST",
        "/credentials/{name}/delete",
        "_post_credential_delete",
        roles=("admin",),
    ),
    Route("POST", "/templates/new", "_post_template_create", roles=("admin",)),
    Route(
        "POST",
        "/templates/{name}/edit",
        "_post_template_update",
        roles=("admin",),
    ),
    Route(
        "POST",
        "/templates/{name}/delete",
        "_post_template_delete",
        roles=("admin",),
    ),
    Route("POST", "/settings", "_post_settings", roles=("admin",)),
    Route("POST", "/settings/users/new", "_post_user_create", roles=("admin",)),
    Route("POST", "/settings/users/{name}/edit", "_post_user_edit", roles=("admin",)),
    Route(
        "POST",
        "/settings/users/{name}/password",
        "_post_user_password",
        check="_can_manage_password",
    ),
    Route(
        "POST",
        "/settings/users/{name}/delete",
        "_post_user_delete",
        roles=("admin",),
    ),
    Route("POST", "/settings/users/{name}/role", "_post_user_role", roles=("admin",)),
]


def _split_pattern(pattern):
    return [seg for seg in pattern.split("/") if seg]


def _match_pattern(segments, parts):
    """Match precompiled pattern segments against request path parts.

    Returns a list of captured values, or None if the pattern does not match.
    """
    params = []
    for i, seg in enumerate(segments):
        if seg.startswith("{") and seg.endswith("*}"):
            rest = parts[i:]
            if not rest:
                return None
            params.append("/".join(rest))
            return params
        if i >= len(parts):
            return None
        if seg.startswith("{"):
            params.append(parts[i])
        elif parts[i] != seg:
            return None
    if len(parts) != len(segments):
        return None
    return params


_COMPILED_ROUTES = [(route, _split_pattern(route.pattern)) for route in ROUTES]


def _resolve_route(method, parts):
    for route, segments in _COMPILED_ROUTES:
        if route.method != method:
            continue
        params = _match_pattern(segments, parts)
        if params is not None:
            return route, params
    return None


def make_handler(manager, auth):
    class PipelineHandler(http.server.BaseHTTPRequestHandler):
        _manager = manager
        _auth = auth

        def _log_username(self):
            return getattr(self, "_authed_user", None) or self._current_user() or "-"

        def _is_poll_request(self):
            """True for the UI's periodic polling endpoints (live updates)."""
            path = self.path.split("?", 1)[0]
            if path in ("/api/queue", "/api/dashboard"):
                return True
            if path.endswith("/builds.json") or path.endswith("/status"):
                return True
            if path.endswith("/gitpoll-log.txt"):
                return True
            return bool(re.search(r"/log/\d+$", path))

        def log_message(self, fmt, *args):
            # Suppress successful polling requests so live-update traffic does
            # not flood the access log; failures are still logged.
            if self._is_poll_request():
                code = args[1] if len(args) > 1 else None
                try:
                    if 200 <= int(code) < 400:
                        return
                except (TypeError, ValueError):
                    pass
            _access_log.info(
                "%s %s %s", self.address_string(), self._log_username(), fmt % args
            )

        def log_error(self, fmt, *args):
            _access_log.warning(
                "%s %s %s", self.address_string(), self._log_username(), fmt % args
            )

        # ── Helpers ──────────────────────────────────────────────────────────

        def _send_html(self, content, status=200):
            if status == 200:
                try:
                    queue_state = self._manager.get_queue_state()
                except Exception:
                    queue_state = None
                if queue_state and queue_state.get("paused"):
                    banner = ui.queue_paused_banner(
                        {
                            "pause_message": queue_state.get("pause_message", ""),
                            "queued_count": queue_state.get("queued_count", 0),
                            "running_count": queue_state.get("running_count", 0),
                            "max_concurrent_jobs": queue_state.get(
                                "max_concurrent_jobs", 1
                            ),
                        }
                    )
                    marker = '<main class="container">'
                    if marker in content:
                        content = content.replace(marker, marker + banner, 1)
            data = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_text(self, text, status=200):
            data = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_json(self, obj, status=200):
            data = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _redirect(self, location):
            self.send_response(303)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _read_form(self):
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            body = self.rfile.read(length).decode("utf-8")
            raw = urllib.parse.parse_qs(body, keep_blank_values=True)
            return {k: v[0] for k, v in raw.items()}

        def _parse_path(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/") or "/"
            parts = [p for p in path.split("/") if p]
            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            return path, parts, query

        def _get_cookie(self, name):
            raw = self.headers.get("Cookie", "")
            for part in raw.split(";"):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    if k.strip() == name:
                        return v.strip()
            return None

        def _set_session_cookie(self, token):
            self.send_header(
                "Set-Cookie",
                f"pipeline_session={token}; HttpOnly; SameSite=Lax; Path=/",
            )

        def _clear_session_cookie(self):
            self.send_header(
                "Set-Cookie",
                "pipeline_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0",
            )

        def _current_user(self):
            token = self._get_cookie("pipeline_session")
            if not token:
                return None
            return self._auth.get_session_user(token)

        def _require_auth(self):
            """Return the current username, or send a redirect and return None."""
            user = self._current_user()
            if user:
                role = self._auth.get_user_role(user)
                if not role:
                    token = self._get_cookie("pipeline_session")
                    if token:
                        self._auth.destroy_session(token)
                    self._clear_session_cookie()
                    self._redirect("/login")
                    return None
                self._authed_user = user
                self._authed_role = role
                return user
            self._redirect("/login")
            return None

        def _has_role(self, *roles):
            return getattr(self, "_authed_role", None) in roles

        def _forbidden(self):
            self._render(ui.error_403, status=403)

        def _require_roles(self, *roles):
            if self._has_role(*roles):
                return True
            self._forbidden()
            return False

        def _can_manage_password(self, target):
            if self._has_role("admin"):
                return True
            if self._has_role("user", "viewer") and target == getattr(
                self, "_authed_user", None
            ):
                return True
            return False

        def _render(self, page_fn, *args, status=200, **kwargs):
            """Render a UI page, passing a context with the current user/role."""
            ctx = ui.PageContext(
                username=getattr(self, "_authed_user", None),
                role=getattr(self, "_authed_role", None),
            )
            self._send_html(page_fn(ctx, *args, **kwargs), status)

        def _send_404(self):
            self._render(ui.error_404, status=404)

        def _load_job_or_404(self, name):
            """Return the named job, or send a 404 page and return None."""
            if not _valid_job_name(name):
                self._send_404()
                return None
            job = self._manager.get_job(name)
            if not job:
                self._send_404()
                return None
            return job

        # ── Routing ──────────────────────────────────────────────────────────

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def _dispatch(self, method):
            _, parts, query = self._parse_path()
            try:
                match = _resolve_route(method, parts)
                # Public routes (login/setup) bypass authentication.
                if match is not None and match[0].public:
                    route, params = match
                    getattr(self, route.handler)(*params)
                    return
                # Everything else requires a logged-in user first, so unknown
                # paths still redirect anonymous visitors to the login page.
                if not self._require_auth():
                    return
                if match is None:
                    self._send_404()
                    return
                route, params = match
                if route.check is not None:
                    if not getattr(self, route.check)(*params):
                        self._forbidden()
                        return
                elif route.roles is not None:
                    if not self._require_roles(*route.roles):
                        return
                args = list(params)
                if route.wants_query:
                    args.append(query)
                getattr(self, route.handler)(*args)
            except Exception as exc:
                self._render(ui.error_500, exc, status=500)

        # ── GET handlers ─────────────────────────────────────────────────────

        def _get_dashboard(self):
            jobs = self._manager.list_jobs()
            self._render(ui.dashboard, jobs)

        def _get_queue_status(self):
            self._send_json(self._manager.get_queue_state())

        def _get_dashboard_status(self):
            jobs = self._manager.list_jobs()
            result = []
            for job in jobs:
                lb = job.get("last_build") or None
                weather = job.get("weather")
                entry = {
                    "name": job["name"],
                    "last_build": None,
                    "weather": weather,
                }
                if lb:
                    entry["last_build"] = {
                        "id": lb.get("id"),
                        "status": lb.get("status"),
                        "duration": lb.get("duration"),
                        "started_at": lb.get("started_at") or lb.get("queued_at", ""),
                    }
                result.append(entry)
            self._send_json({"jobs": result})

        def _get_job_new(self):
            creds = self._manager.list_credentials()
            self._render(
                ui.job_form,
                available_creds=[c["name"] for c in creds],
                templates=self._manager.list_templates(),
            )

        def _get_job_detail(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            builds = self._manager.list_builds(name)
            job["weather"] = compute_weather(builds)
            self._render(ui.job_detail, job, builds)

        def _get_gitpoll_log(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            if (job.get("trigger") or {}).get("type") != "gitpoll":
                self._send_404()
                return
            log_text = self._manager.get_git_poll_log(name)
            self._render(ui.gitpoll_log, job, log_text)

        def _get_gitpoll_log_text(self, name):
            if not _valid_job_name(name):
                self._send_text("", 404)
                return
            job = self._manager.get_job(name)
            if not job or (job.get("trigger") or {}).get("type") != "gitpoll":
                self._send_text("", 404)
                return
            self._send_text(self._manager.get_git_poll_log(name))

        def _get_job_builds_status(self, name):
            if not _valid_job_name(name):
                self._send_json({"error": "not found"}, 404)
                return
            job = self._manager.get_job(name)
            if not job:
                self._send_json({"error": "not found"}, 404)
                return
            builds = self._manager.list_builds(name)
            result = []
            for b in builds:
                result.append(
                    {
                        "id": b.get("id"),
                        "status": b.get("status"),
                        "duration": b.get("duration"),
                        "started_at": b.get("started_at") or b.get("queued_at", ""),
                        "triggered_by": b.get("triggered_by") or "",
                        "parameters": b.get("parameters") or {},
                    }
                )
            self._send_json(
                {
                    "builds": result,
                    "weather": compute_weather(builds),
                }
            )

        def _get_job_edit(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            creds = self._manager.list_credentials()
            self._render(
                ui.job_form,
                job,
                available_creds=[c["name"] for c in creds],
                templates=self._manager.list_templates(),
            )

        def _get_build_form(self, name, query=None):
            job = self._load_job_or_404(name)
            if job is None:
                return
            if not job.get("enabled", True):
                self._redirect(f"/jobs/{name}")
                return
            if not job.get("parameters"):
                # No parameters — trigger immediately
                build_id = self._manager.trigger_build(
                    name, {}, triggered_by=self._authed_user
                )
                self._redirect(f"/jobs/{name}/builds/{build_id}")
                return

            values = None
            rerun_from = ""
            if query:
                rerun_from = (query.get("rerun_from") or [""])[0].strip()
            if rerun_from and _valid_build_id(rerun_from):
                source_build = self._manager.get_build(name, int(rerun_from))
                if source_build:
                    values = source_build.get("parameters") or {}

            self._render(ui.build_form, job, values=values)

        def _get_build_detail(self, name, bid):
            if not _valid_build_id(bid):
                self._send_404()
                return
            job = self._load_job_or_404(name)
            if job is None:
                return
            build = self._manager.get_build(name, int(bid))
            if not build:
                self._send_404()
                return
            section_logs = self._manager.get_build_section_logs(name, int(bid))
            self._render(ui.build_detail, job, build, section_logs)

        def _get_build_log(self, name, bid):
            if not _valid_job_name(name) or not _valid_build_id(bid):
                self._send_text("", 404)
                return
            log_text = self._manager.get_build_log(name, int(bid))
            self._send_text(log_text)

        def _get_build_section_log_text(self, name, bid, section_num):
            if not _valid_job_name(name) or not _valid_build_id(bid):
                self._send_text("", 404)
                return
            try:
                snum = int(section_num)
                if snum < 1:
                    raise ValueError
            except (TypeError, ValueError):
                self._send_text("", 404)
                return
            text = self._manager.get_build_section_log(name, int(bid), snum)
            self._send_text(text)

        def _get_build_status(self, name, bid):
            if not _valid_job_name(name) or not _valid_build_id(bid):
                self._send_json({"error": "not found"}, 404)
                return
            build = self._manager.get_build(name, int(bid))
            if not build:
                self._send_json({"error": "not found"}, 404)
                return
            self._send_json(
                {
                    "status": build.get("status"),
                    "duration": build.get("duration"),
                    "finished_at": build.get("finished_at"),
                }
            )

        def _get_cron_preview(self, query):
            schedule = (query.get("schedule") or [""])[0].strip()
            if not schedule:
                self._send_json(
                    {
                        "next_run": None,
                        "message": "Enter a cron schedule to preview the next run.",
                    }
                )
                return
            error = validate_cron(schedule)
            if error:
                self._send_json({"next_run": None, "error": error})
                return
            next_run = next_cron_run(schedule)
            if not next_run:
                self._send_json(
                    {
                        "next_run": None,
                        "error": "Could not determine the next run for this schedule.",
                    },
                    422,
                )
                return
            self._send_json(
                {
                    "next_run": next_run.isoformat(timespec="minutes"),
                    "message": next_run.strftime("Next run: %a %Y-%m-%d %H:%M"),
                }
            )

        def _get_workspace(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            files = self._manager.list_workspace_files(name)
            self._render(ui.workspace, job, files)

        def _get_workspace_file(self, name, rel_path):
            if not _valid_job_name(name):
                self._send_404()
                return
            full_path = self._manager.get_workspace_file(name, rel_path)
            if not full_path:
                self._send_404()
                return
            try:
                with open(full_path, "rb") as f:
                    data = f.read()
            except OSError:
                self._send_404()
                return
            mime = _guess_mime(rel_path)
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        # ── POST handlers ────────────────────────────────────────────────────

        def _post_job_create(self):
            form = self._read_form()
            name = form.get("name", "").strip()
            notify_on_failure = form.get("notify_on_failure") == "1"
            available_creds = [c["name"] for c in self._manager.list_credentials()]
            if not _valid_job_name(name):
                self._render(
                    ui.job_form,
                    error="Invalid job name. Use letters, numbers, hyphens and underscores only.",
                    available_creds=available_creds,
                )
                return
            if self._manager.get_job(name):
                self._render(
                    ui.job_form,
                    error=f'A job named "{name}" already exists.',
                    available_creds=available_creds,
                )
                return
            try:
                params = _parse_params_json(form.get("params_json", "[]"))
                steps = _parse_steps_json(form.get("steps_json", "[]"))
            except ValueError as exc:
                self._render(
                    ui.job_form,
                    {
                        "name": name,
                        "description": form.get("description", "").strip(),
                        "steps": _load_raw_steps_json(form.get("steps_json", "[]")),
                        "env_script": form.get("env_script", ""),
                        "parameters": _load_raw_params_json(
                            form.get("params_json", "[]")
                        ),
                        "credentials": _parse_credentials_json(
                            form.get("credentials_json", "[]")
                        ),
                        "notify_on_failure": notify_on_failure,
                    },
                    error=str(exc),
                    available_creds=available_creds,
                )
                return
            trigger = _parse_trigger(form)
            if trigger["type"] == "cron":
                cron_error = validate_cron(trigger["schedule"])
                if cron_error:
                    self._render(
                        ui.job_form,
                        {
                            "name": name,
                            "description": form.get("description", "").strip(),
                            "steps": _load_raw_steps_json(form.get("steps_json", "[]")),
                            "env_script": form.get("env_script", ""),
                            "parameters": _load_raw_params_json(
                                form.get("params_json", "[]")
                            ),
                            "credentials": _parse_credentials_json(
                                form.get("credentials_json", "[]")
                            ),
                            "notify_on_failure": notify_on_failure,
                            "trigger": trigger,
                        },
                        error=f"Invalid cron schedule: {cron_error}",
                        available_creds=available_creds,
                    )
                    return
            config = {
                "name": name,
                "description": form.get("description", "").strip(),
                "labels": _parse_labels(form.get("labels", "")),
                "steps": steps,
                "env_script": form.get("env_script", ""),
                "parameters": params,
                "credentials": _parse_credentials_json(
                    form.get("credentials_json", "[]")
                ),
                "max_builds": _parse_max_builds(form.get("max_builds", "")),
                "notify_on_failure": notify_on_failure,
                "mount_docker_socket": form.get("mount_docker_socket") == "1",
                "trigger": trigger,
                "git": _parse_git_config(form),
            }
            self._manager.save_job(config)
            self._redirect(f"/jobs/{name}")

        def _post_job_update(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            form = self._read_form()
            notify_on_failure = form.get("notify_on_failure") == "1"
            available_creds = [c["name"] for c in self._manager.list_credentials()]
            try:
                params = _parse_params_json(form.get("params_json", "[]"))
                steps = _parse_steps_json(form.get("steps_json", "[]"))
            except ValueError as exc:
                updated_job = {
                    "name": job["name"],
                    "description": form.get("description", "").strip(),
                    "steps": _load_raw_steps_json(form.get("steps_json", "[]")),
                    "env_script": form.get("env_script", ""),
                    "parameters": _load_raw_params_json(form.get("params_json", "[]")),
                    "credentials": _parse_credentials_json(
                        form.get("credentials_json", "[]")
                    ),
                    "notify_on_failure": notify_on_failure,
                }
                self._render(
                    ui.job_form,
                    updated_job,
                    error=str(exc),
                    available_creds=available_creds,
                )
                return
            trigger = _parse_trigger(form)
            if trigger["type"] == "cron":
                cron_error = validate_cron(trigger["schedule"])
                if cron_error:
                    updated_job = {
                        "name": job["name"],
                        "description": form.get("description", "").strip(),
                        "steps": _load_raw_steps_json(form.get("steps_json", "[]")),
                        "env_script": form.get("env_script", ""),
                        "parameters": _load_raw_params_json(
                            form.get("params_json", "[]")
                        ),
                        "credentials": _parse_credentials_json(
                            form.get("credentials_json", "[]")
                        ),
                        "notify_on_failure": notify_on_failure,
                        "trigger": trigger,
                    }
                    self._render(
                        ui.job_form,
                        updated_job,
                        error=f"Invalid cron schedule: {cron_error}",
                        available_creds=available_creds,
                    )
                    return
            job["description"] = form.get("description", "").strip()
            job["labels"] = _parse_labels(form.get("labels", ""))
            job["steps"] = steps
            job["env_script"] = form.get("env_script", "")
            job["parameters"] = params
            job["credentials"] = _parse_credentials_json(
                form.get("credentials_json", "[]")
            )
            job["max_builds"] = _parse_max_builds(form.get("max_builds", ""))
            job["notify_on_failure"] = notify_on_failure
            job["mount_docker_socket"] = form.get("mount_docker_socket") == "1"
            job["enabled"] = form.get("disabled") != "1"
            job["trigger"] = trigger
            job["git"] = _parse_git_config(form)
            self._manager.save_job(job)
            self._redirect(f"/jobs/{name}")

        def _post_job_delete(self, name):
            if not _valid_job_name(name):
                self._redirect("/")
                return
            self._manager.delete_job(name)
            self._redirect("/")

        def _post_job_trigger(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            form = self._read_form()
            if not job.get("enabled", True):
                self._redirect(f"/jobs/{name}")
                return
            params = {}
            for p in job.get("parameters") or []:
                pname = p.get("name", "")
                if pname:
                    params[pname] = form.get(f"param_{pname}", p.get("default", ""))
            error = _validate_build_params(job, params)
            if error:
                self._render(ui.build_form, job, error=error, values=params)
                return
            build_id = self._manager.trigger_build(
                name, params, triggered_by=self._authed_user
            )
            self._redirect(f"/jobs/{name}/builds/{build_id}")

        def _post_workspace_clear(self, name):
            job = self._load_job_or_404(name)
            if job is None:
                return
            self._manager.clear_workspace(name)
            self._redirect(f"/jobs/{name}/workspace")

        def _post_build_cancel(self, name, bid):
            if not _valid_job_name(name) or not _valid_build_id(bid):
                self._send_404()
                return
            self._manager.cancel_build(name, int(bid))
            self._redirect(f"/jobs/{name}/builds/{bid}")

        def _post_build_rerun(self, name, bid):
            if not _valid_build_id(bid):
                self._send_404()
                return
            job = self._load_job_or_404(name)
            if job is None:
                return
            if not job.get("enabled", True) or not job.get("parameters"):
                self._redirect(f"/jobs/{name}/builds/{bid}")
                return
            source_build = self._manager.get_build(name, int(bid))
            if not source_build:
                self._send_404()
                return
            self._redirect(f"/jobs/{name}/build?rerun_from={int(bid)}")

        # ── Credentials handlers ─────────────────────────────────────────────

        def _get_credentials_list(self):
            creds = self._manager.list_credentials()
            self._render(ui.credentials_list, creds)

        def _get_credential_new(self):
            self._render(ui.credentials_form)

        def _get_credential_edit(self, name):
            if not _valid_cred_name(name):
                self._send_404()
                return
            cred = self._manager.get_credential(name)
            if not cred:
                self._send_404()
                return
            self._render(ui.credentials_form, cred)

        def _post_credential_create(self):
            form = self._read_form()
            name = form.get("name", "").strip()
            if not _valid_cred_name(name):
                self._render(
                    ui.credentials_form,
                    error="Invalid name. Use letters, numbers, hyphens and underscores only.",
                )
                return
            if self._manager.get_credential(name):
                self._render(
                    ui.credentials_form,
                    error=f'A credential named "{name}" already exists.',
                )
                return
            self._manager.save_credential(
                name,
                form.get("value", ""),
                form.get("description", "").strip(),
            )
            self._redirect("/credentials")

        def _post_credential_update(self, name):
            if not _valid_cred_name(name):
                self._send_404()
                return
            cred = self._manager.get_credential(name)
            if not cred:
                self._send_404()
                return
            form = self._read_form()
            value = form.get("value", "") or cred["value"]
            description = form.get("description", "").strip()
            self._manager.save_credential(name, value, description)
            self._redirect("/credentials")

        def _post_credential_delete(self, name):
            if not _valid_cred_name(name):
                self._redirect("/credentials")
                return
            self._manager.delete_credential(name)
            self._redirect("/credentials")

        # ── Templates handlers ───────────────────────────────────────────────

        def _get_templates_list(self):
            self._render(ui.templates_list, self._manager.list_templates())

        def _get_template_new(self):
            self._render(ui.template_form)

        def _get_template_edit(self, name):
            if not _valid_template_name(name):
                self._send_404()
                return
            template = self._manager.get_template(name)
            if not template:
                self._send_404()
                return
            self._render(ui.template_form, template)

        def _post_template_create(self):
            form = self._read_form()
            name = form.get("name", "").strip()
            if not _valid_template_name(name):
                self._render(
                    ui.template_form,
                    self._template_from_form(name, form),
                    error="Invalid name. Use letters, numbers, hyphens and underscores only.",
                )
                return
            if self._manager.get_template(name):
                self._render(
                    ui.template_form,
                    self._template_from_form(name, form),
                    error=f'A template named "{name}" already exists.',
                )
                return
            self._manager.save_template(self._template_from_form(name, form))
            self._redirect("/templates")

        def _post_template_update(self, name):
            if not _valid_template_name(name):
                self._send_404()
                return
            if not self._manager.get_template(name):
                self._send_404()
                return
            form = self._read_form()
            self._manager.save_template(self._template_from_form(name, form))
            self._redirect("/templates")

        def _post_template_delete(self, name):
            if not _valid_template_name(name):
                self._redirect("/templates")
                return
            self._manager.delete_template(name)
            self._redirect("/templates")

        def _template_from_form(self, name, form):
            return {
                "name": name,
                "description": form.get("description", "").strip(),
                "image": form.get("image", "").strip(),
                "script": form.get("script", ""),
                "env_vars": _parse_template_env_vars(form.get("env_vars_json", "[]")),
            }

        def _get_settings(self):
            cfg = self._manager.get_server_config()
            creds = self._manager.list_credentials()
            self._render(ui.settings, cfg, available_creds=[c["name"] for c in creds])

        def _get_users_list(self):
            users = self._auth.list_user_records()
            self._render(ui.users_list, users, self._authed_user)

        def _get_user_new(self):
            self._render(ui.user_new_form)

        def _get_user_password(self, target):
            if target not in self._auth.list_users():
                self._send_404()
                return
            self._render(ui.user_password_form, target)

        def _get_user_edit(self, target):
            if target not in self._auth.list_users():
                self._send_404()
                return
            self._render(
                ui.user_edit_form,
                target,
                user_role=self._auth.get_user_role(target) or "user",
                disabled=self._auth.get_user_disabled(target),
            )

        def _post_user_create(self):
            form = self._read_form()
            uname = form.get("username", "").strip()
            role = form.get("role", "user").strip()
            password = form.get("password", "")
            confirm = form.get("confirm", "")
            if role not in ("admin", "user", "viewer"):
                role = "user"
            if not uname or not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,49}$", uname):
                self._render(
                    ui.user_new_form,
                    error="Invalid username. Use letters, numbers, ., - and _ only.",
                )
                return
            if len(password) < 8:
                self._render(
                    ui.user_new_form,
                    error="Password must be at least 8 characters.",
                )
                return
            if password != confirm:
                self._render(ui.user_new_form, error="Passwords do not match.")
                return
            if uname in self._auth.list_users():
                self._render(
                    ui.user_new_form,
                    error=f'A user named "{uname}" already exists.',
                )
                return
            self._auth.add_user(uname, password, role=role)
            self._redirect("/settings/users")

        def _post_user_password(self, target):
            if target not in self._auth.list_users():
                self._send_404()
                return
            form = self._read_form()
            password = form.get("password", "")
            confirm = form.get("confirm", "")
            if len(password) < 8:
                self._render(
                    ui.user_password_form,
                    target,
                    error="Password must be at least 8 characters.",
                )
                return
            if password != confirm:
                self._render(
                    ui.user_password_form, target, error="Passwords do not match."
                )
                return
            self._auth.change_password(target, password)
            self._redirect("/settings/users")

        def _post_user_edit(self, target):
            if target not in self._auth.list_users():
                self._redirect("/settings/users")
                return

            form = self._read_form()
            new_role = form.get("role", "").strip()
            new_disabled = form.get("disabled") == "1"
            password = form.get("password", "")
            confirm = form.get("confirm", "")

            if password or confirm:
                if len(password) < 8:
                    self._render(
                        ui.user_edit_form,
                        target,
                        user_role=new_role
                        or (self._auth.get_user_role(target) or "user"),
                        disabled=self._auth.get_user_disabled(target),
                        error="Password must be at least 8 characters.",
                    )
                    return
                if password != confirm:
                    self._render(
                        ui.user_edit_form,
                        target,
                        user_role=new_role
                        or (self._auth.get_user_role(target) or "user"),
                        disabled=self._auth.get_user_disabled(target),
                        error="Passwords do not match.",
                    )
                    return

            ok, error = self._auth.set_user_role(target, new_role)
            if not ok:
                self._render(
                    ui.user_edit_form,
                    target,
                    user_role=self._auth.get_user_role(target) or "user",
                    disabled=self._auth.get_user_disabled(target),
                    error=error,
                )
                return

            if password:
                self._auth.change_password(target, password)

            self._auth.set_user_disabled(target, new_disabled)
            # if the target user is now disabled, kill their session
            if new_disabled and target != self._authed_user:
                for token, uname in list(self._auth._sessions.items()):
                    if uname == target:
                        self._auth.destroy_session(token)

            if target == self._authed_user and new_role != "admin":
                self._redirect("/")
                return
            self._redirect("/settings/users")

        def _post_user_delete(self, target):
            users = self._auth.list_users()
            if target not in users:
                self._redirect("/settings/users")
                return
            if len(users) <= 1:
                records = self._auth.list_user_records()
                self._render(ui.users_list, records, self._authed_user)
                return
            self._auth.delete_user(target)
            # if the user deleted themselves, log out
            if target == self._authed_user:
                token = self._get_cookie("pipeline_session")
                if token:
                    self._auth.destroy_session(token)
                self._clear_session_cookie()
                self._redirect("/login")
                return
            self._redirect("/settings/users")

        def _post_user_role(self, target):
            records = self._auth.list_user_records()
            usernames = {r.get("username", "") for r in records}
            if target not in usernames:
                self._redirect("/settings/users")
                return

            form = self._read_form()
            new_role = form.get("role", "").strip()
            ok, error = self._auth.set_user_role(target, new_role)
            if not ok:
                records = self._auth.list_user_records()
                self._render(ui.users_list, records, self._authed_user, error=error)
                return

            if target == self._authed_user and new_role != "admin":
                self._redirect("/")
                return
            self._redirect("/settings/users")

        def _get_login(self):
            if self._current_user():
                self._redirect("/")
                return
            if not self._auth.has_users():
                self._redirect("/setup")
                return
            self._send_html(ui.login_page())

        def _post_login(self):
            if not self._auth.has_users():
                self._redirect("/setup")
                return
            form = self._read_form()
            username = form.get("username", "").strip()
            password = form.get("password", "")
            if self._auth.verify_user(username, password):
                token = self._auth.create_session(username)
                self.send_response(303)
                self._set_session_cookie(token)
                self.send_header("Location", "/")
                self.send_header("Content-Length", "0")
                self.end_headers()
            else:
                self._send_html(ui.login_page(error="Invalid username or password."))

        def _get_logout(self):
            token = self._get_cookie("pipeline_session")
            if token:
                self._auth.destroy_session(token)
            self.send_response(303)
            self._clear_session_cookie()
            self.send_header("Location", "/login")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _get_setup(self):
            if self._auth.has_users():
                self._redirect("/")
                return
            self._send_html(ui.setup_page())

        def _post_setup(self):
            if self._auth.has_users():
                self._redirect("/")
                return
            form = self._read_form()
            username = form.get("username", "").strip()
            password = form.get("password", "")
            confirm = form.get("confirm", "")
            if not username or not re.match(
                r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,49}$", username
            ):
                self._send_html(
                    ui.setup_page(
                        error="Invalid username. Use letters, numbers, ., - and _ only."
                    )
                )
                return
            if len(password) < 8:
                self._send_html(
                    ui.setup_page(error="Password must be at least 8 characters.")
                )
                return
            if password != confirm:
                self._send_html(ui.setup_page(error="Passwords do not match."))
                return
            self._auth.add_user(username, password, role="admin")
            token = self._auth.create_session(username)
            self.send_response(303)
            self._set_session_cookie(token)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _post_settings(self):
            form = self._read_form()
            default_script_header = form.get("default_script_header", "")
            queue_paused = form.get("queue_paused") == "1"
            queue_pause_message = form.get("queue_pause_message", "").strip()
            git_poll_log_max_lines = form.get("git_poll_log_max_lines", "").strip()
            email_settings = {
                "recipients": form.get("notification_recipients", ""),
                "from_address": form.get("notification_from_address", "").strip(),
                "smtp_host": form.get("notification_smtp_host", "").strip(),
                "smtp_port": form.get("notification_smtp_port", "").strip(),
                "smtp_security": form.get(
                    "notification_smtp_security", "starttls"
                ).strip(),
                "smtp_username": form.get("notification_smtp_username", "").strip(),
                "smtp_credential": form.get("notification_smtp_credential", "").strip(),
            }
            try:
                max_builds = max(1, int(form.get("max_builds", 10)))
            except (TypeError, ValueError):
                cfg = self._manager.get_server_config()
                cfg["default_script_header"] = default_script_header
                cfg["queue_paused"] = queue_paused
                cfg["queue_pause_message"] = queue_pause_message
                cfg["email_notifications"] = email_settings
                cfg["git_poll_log_max_lines"] = git_poll_log_max_lines
                creds = self._manager.list_credentials()
                self._render(
                    ui.settings,
                    cfg,
                    available_creds=[c["name"] for c in creds],
                    error="Max builds must be a number.",
                )
                return
            try:
                max_concurrent_jobs = max(1, int(form.get("max_concurrent_jobs", 2)))
            except (TypeError, ValueError):
                cfg = self._manager.get_server_config()
                cfg["default_script_header"] = default_script_header
                cfg["max_builds"] = max_builds
                cfg["queue_paused"] = queue_paused
                cfg["queue_pause_message"] = queue_pause_message
                cfg["email_notifications"] = email_settings
                cfg["git_poll_log_max_lines"] = git_poll_log_max_lines
                creds = self._manager.list_credentials()
                self._render(
                    ui.settings,
                    cfg,
                    available_creds=[c["name"] for c in creds],
                    error="Max concurrent jobs must be a number.",
                )
                return
            try:
                smtp_port = int(email_settings["smtp_port"] or 587)
                if smtp_port < 1 or smtp_port > 65535:
                    raise ValueError()
            except (TypeError, ValueError):
                cfg = self._manager.get_server_config()
                cfg["default_script_header"] = default_script_header
                cfg["max_builds"] = max_builds
                cfg["max_concurrent_jobs"] = max_concurrent_jobs
                cfg["queue_paused"] = queue_paused
                cfg["queue_pause_message"] = queue_pause_message
                cfg["email_notifications"] = email_settings
                cfg["git_poll_log_max_lines"] = git_poll_log_max_lines
                creds = self._manager.list_credentials()
                self._render(
                    ui.settings,
                    cfg,
                    available_creds=[c["name"] for c in creds],
                    error="SMTP port must be a number between 1 and 65535.",
                )
                return
            email_settings["smtp_port"] = smtp_port
            if (
                email_settings["smtp_credential"]
                and not email_settings["smtp_username"]
            ):
                cfg = self._manager.get_server_config()
                cfg["default_script_header"] = default_script_header
                cfg["max_builds"] = max_builds
                cfg["max_concurrent_jobs"] = max_concurrent_jobs
                cfg["queue_paused"] = queue_paused
                cfg["queue_pause_message"] = queue_pause_message
                cfg["email_notifications"] = email_settings
                cfg["git_poll_log_max_lines"] = git_poll_log_max_lines
                creds = self._manager.list_credentials()
                self._render(
                    ui.settings,
                    cfg,
                    available_creds=[c["name"] for c in creds],
                    error="SMTP username is required when an SMTP credential is selected.",
                )
                return
            cfg = self._manager.get_server_config()
            cfg["max_builds"] = max_builds
            cfg["max_concurrent_jobs"] = max_concurrent_jobs
            cfg["default_script_header"] = default_script_header
            cfg["queue_paused"] = queue_paused
            cfg["queue_pause_message"] = queue_pause_message
            cfg["email_notifications"] = email_settings
            cfg["git_poll_log_max_lines"] = git_poll_log_max_lines
            self._manager.save_server_config(cfg)
            self._redirect("/settings")

    return PipelineHandler


def _parse_params_json(raw):
    params = _load_raw_params_json(raw)
    result = []
    for p in params:
        name = str(p.get("name", "")).strip()
        if not _JOB_NAME_RE.match(name):
            continue
        regex = str(p.get("regex", "")).strip()
        try:
            _compile_param_regex(regex)
        except re.error as exc:
            raise ValueError(f'Invalid regex for parameter "{name}": {exc}')
        result.append(
            {
                "name": name,
                "description": str(p.get("description", "")).strip(),
                "default": str(p.get("default", "")),
                "regex": regex,
            }
        )
    return result


def _load_raw_params_json(raw):
    try:
        params = json.loads(raw)
        if not isinstance(params, list):
            return []
        return params
    except (ValueError, TypeError):
        return []


def _parse_steps_json(raw):
    sections = _load_raw_steps_json(raw)
    result = []
    for section in sections:
        if not isinstance(section, dict):
            continue
        name = str(section.get("name", "")).strip()
        script = str(section.get("script", ""))
        template = str(section.get("template", "")).strip()
        if not name and not script and not template:
            continue
        image = _parse_step_image(section)
        result.append(
            {
                "name": name or f"Script {len(result) + 1}",
                "script": script,
                "image": image,
                "reuse_container": bool(section.get("reuse_container", False)),
                "template": template,
            }
        )
    if result:
        return result
    return [{"name": "Script 1", "script": "", "image": ""}]


def _parse_template_env_vars(raw):
    try:
        items = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(items, list):
        return []
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        result.append(
            {
                "name": name,
                "description": str(item.get("description", "")).strip(),
            }
        )
    return result


def _parse_step_image(section):
    image = str(section.get("image", "")).strip()
    if not image:
        execution = section.get("execution")
        if isinstance(execution, dict):
            image = str(execution.get("image", "")).strip()
    if not image:
        return "alpine:latest"
    return image


def _load_raw_steps_json(raw):
    try:
        sections = json.loads(raw)
        if not isinstance(sections, list):
            return []
        return sections
    except (ValueError, TypeError):
        return []


def _parse_labels(raw):
    result = []
    for part in raw.replace(",", " ").split():
        label = part.strip().lower()
        if label and re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", label):
            result.append(label)
    return result


def _parse_max_builds(raw):
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = int(raw)
        return max(1, v) if v > 0 else None
    except (TypeError, ValueError):
        return None


def _parse_trigger(form):
    trigger_type = form.get("trigger_type", "manual").strip()
    if trigger_type == "cron":
        return {"type": "cron", "schedule": form.get("cron_schedule", "").strip()}
    if trigger_type == "gitpoll":
        interval = form.get("gitpoll_interval", "").strip()
        try:
            interval = int(interval)
        except Exception:
            interval = None
        if interval and interval < 300:
            interval = 300
        return (
            {"type": "gitpoll", "interval": interval}
            if interval
            else {"type": "gitpoll"}
        )
    return {"type": "manual"}


def _parse_git_config(form):
    url = form.get("git_url", "").strip()
    if not url:
        return None
    return {
        "url": url,
        "branch": form.get("git_branch", "").strip() or "main",
        "credential": form.get("git_credential", "").strip(),
        "shallow": form.get("git_shallow") == "1",
    }


def _parse_credentials_json(raw):
    try:
        bindings = json.loads(raw)
        if not isinstance(bindings, list):
            return []
    except (ValueError, TypeError):
        return []
    result = []
    for b in bindings:
        if not isinstance(b, dict):
            continue
        credential = str(b.get("credential", "")).strip()
        env_var = str(b.get("env_var", "")).strip()
        bind_type = str(b.get("type", "value")).strip()
        if not credential or not env_var:
            continue
        if bind_type not in ("value", "file"):
            bind_type = "value"
        result.append({"credential": credential, "env_var": env_var, "type": bind_type})
    return result


def _guess_mime(path):
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {
        "txt": "text/plain; charset=utf-8",
        "log": "text/plain; charset=utf-8",
        "csv": "text/plain; charset=utf-8",
        "json": "application/json",
        "html": "text/html; charset=utf-8",
        "htm": "text/html; charset=utf-8",
        "xml": "text/xml; charset=utf-8",
        "md": "text/plain; charset=utf-8",
        "sh": "text/plain; charset=utf-8",
        "py": "text/plain; charset=utf-8",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
    }.get(ext, "application/octet-stream")


def run_server(host, port, data_dir):
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S",
    )
    manager = JobManager(data_dir)
    auth = AuthManager(data_dir)
    handler = make_handler(manager, auth)
    server = http.server.ThreadingHTTPServer((host, port), handler)
    if not auth.has_users():
        print(
            f"No users found. Visit http://{host}:{port}/setup to create the first user.",
            flush=True,
        )
    print(f"Pipeline listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
