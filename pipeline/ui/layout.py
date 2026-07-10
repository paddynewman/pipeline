import html
import textwrap

from pipeline import __version__
from .assets import *  # noqa: F401,F403

__all__ = [
    "esc",
    "_html",
    "_BADGE_HTML",
    "_permissions_for_role",
    "PageContext",
    "_page",
    "_badge",
    "queue_paused_banner",
    "_weather",
    "_fmt_duration",
    "_breadcrumb",
    "_page_bare",
    "json_str",
    "_BRAND_ICON_SVG",
    "_FAVICON_HREF",
    "_CSS",
    "_TIMEAGO_JS",
    "_PARAMS_EDITOR_JS",
    "_STEPS_EDITOR_JS",
    "_CREDENTIALS_EDITOR_JS",
]


def esc(s):
    return html.escape(str(s) if s is not None else "", quote=True)


def _html(block):
    return textwrap.dedent(block).strip()


_BADGE_HTML = {
    "success": '<span class="badge badge-success">\u2713 Success</span>',
    "failure": '<span class="badge badge-failure">\u2717 Failure</span>',
    "running": '<span class="badge badge-running">\u29d7 Running</span>',
    "queued": '<span class="badge badge-aborted">\u23f3 Queued</span>',
    "aborted": '<span class="badge badge-aborted">\u25a0 Aborted</span>',
}


def _permissions_for_role(role):
    role = role or "admin"
    return {
        "can_manage_jobs": role == "admin",
        "can_run_builds": role in ("admin", "user"),
        "can_view_workspaces": role in ("admin", "user", "viewer"),
        "can_clear_workspaces": role == "admin",
        "can_manage_credentials": role == "admin",
        "can_manage_settings": role == "admin",
        "can_manage_users": role == "admin",
        "can_change_own_password": role in ("admin", "user", "viewer"),
    }


class PageContext:
    """Per-request rendering context: the current user, role, and permissions."""

    def __init__(self, username=None, role=None):
        self.username = username
        self.role = role
        self.permissions = _permissions_for_role(role)


def _page(ctx, title, body, extra_js=""):
    permissions = ctx.permissions
    username = ctx.username
    nav_links = ['<a href="/">Dashboard</a>']
    if permissions["can_manage_credentials"]:
        nav_links.append('<a href="/credentials">Credentials</a>')
    if permissions["can_manage_settings"]:
        nav_links.append('<a href="/settings">Settings</a>')
    nav_html = " ".join(nav_links)
    new_job_html = (
        '<a href="/jobs/new" class="btn btn-primary btn-sm">+ New Job</a>'
        if permissions["can_manage_jobs"]
        else ""
    )
    user_links = []
    if username and permissions["can_manage_users"]:
        user_links.append('<a href="/settings/users">Manage users</a>')
    elif username and permissions["can_change_own_password"]:
        user_links.append(
            f'<a href="/settings/users/{esc(username)}/password">Change password</a>'
        )
    user_links.append('<a href="/logout">Log out</a>')
    user_links.append(
        f'<div style="padding:8px 14px 4px 14px;color:#8b949e;font-size:12px;border-top:1px solid #2d333b;margin-top:6px;">Version {__version__}</div>'
    )
    user_html = (
        f"""
<div class="user-menu" id="userMenu">
  <button class="user-menu-btn" onclick="toggleUserMenu(event)">{esc(username)}</button>
  <div class="user-dropdown">
  {''.join(user_links)}
  </div>
</div>
"""
        if username
        else '<a href="/login" style="color:#8b949e;font-size:13px">Log in</a>'
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)} Pipeline</title>
  <link rel="icon" href="{_FAVICON_HREF}" type="image/svg+xml">
  <style>{_CSS}</style>
</head>
<body>
  <header class="topbar">
    <span class="brand">PIPELINE</span>
    <nav class="topnav">{nav_html}</nav>
    <span class="topbar-spacer"></span>
    {new_job_html}
    {user_html}
  </header>
  <main class="container">
    {body}
  </main>
  <script>
    function toggleUserMenu(e) {{
      e.stopPropagation();
      var m = document.getElementById("userMenu");
      m.classList.toggle("open");
    }}
    document.addEventListener("click", function () {{
      var m = document.getElementById("userMenu");
      if (m) m.classList.remove("open");
    }});
  </script>
  <script>{_TIMEAGO_JS}</script>
  {extra_js}
</body></html>
"""


def _badge(status):
    labels = {
        "success": ("badge-success", "\u2713 Success"),
        "failure": ("badge-failure", "\u2717 Failure"),
        "running": ("badge-running", "\u29d7 Running"),
        "queued": ("badge-aborted", "\u23f3 Queued"),
        "aborted": ("badge-aborted", "\u25a0 Aborted"),
    }
    cls, text = labels.get(status or "", ("badge-aborted", status or "\u2014"))
    return f'<span class="badge {cls}">{text}</span>'


def queue_paused_banner(queue_state):
    message = esc(queue_state.get("pause_message") or "Job queue is paused.")
    queued = int(queue_state.get("queued_count") or 0)
    running = int(queue_state.get("running_count") or 0)
    max_concurrent = int(queue_state.get("max_concurrent_jobs") or 1)
    summary = (
        f"Queue paused. {queued} waiting, {running} running "
        f"(limit: {max_concurrent})."
    )
    return (
        '<div class="alert alert-warning" style="margin-top:0">'
        f'<strong>{message}</strong><div style="margin-top:4px">{esc(summary)}</div>'
        "</div>"
    )


def _weather(weather, compact=False):
    labels = {
        "sunny": ("weather-sunny", "\u2600\ufe0f", "Stable"),
        "partly-cloudy": ("weather-partly-cloudy", "\u26c5", "Mostly stable"),
        "cloudy": ("weather-cloudy", "\u2601\ufe0f", "Mixed"),
        "rainy": ("weather-rainy", "\U0001f327\ufe0f", "Unstable"),
        "stormy": ("weather-stormy", "\u26c8\ufe0f", "Failing"),
    }
    if not weather:
        title = "No completed builds yet."
        content = (
            '<span class="weather-icon">-</span>'
            if compact
            else '<span class="weather-icon">-</span><span class="weather-label">No builds</span>'
        )
        return (
            f'<span class="weather weather-none" title="{esc(title)}">{content}</span>'
        )
    condition = weather.get("condition") or "cloudy"
    cls, icon, label = labels.get(condition, labels["cloudy"])
    successes = int(weather.get("successes", 0))
    total = int(weather.get("total", 0))
    score = int(weather.get("score", 0))
    title = (
        f"{label}: {successes}/{total} recent completed builds succeeded ({score}%)."
    )
    content = f'<span class="weather-icon">{icon}</span>'
    if not compact:
        content += f'<span class="weather-label">{esc(label)}</span>'
    return f'<span class="weather {cls}" title="{esc(title)}">{content}</span>'


def _fmt_duration(secs):
    if secs is None:
        return "\u2014"
    secs = float(secs)
    if secs < 60:
        return f"{secs:.1f}s"
    m = int(secs // 60)
    s = int(secs % 60)
    return f"{m}m {s}s"


def _breadcrumb(*items):
    parts = []
    for label, href in items:
        if href:
            parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
        else:
            parts.append(f"<span>{esc(label)}</span>")
    return '<nav class="breadcrumb">' + " &rsaquo; ".join(parts) + "</nav>"


def _page_bare(title, body):
    """Minimal page without the authenticated topbar, used for login/setup."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" href="{_FAVICON_HREF}" type="image/svg+xml">
  <style>{_CSS}</style>
</head>
<body>
  <main class="container">{body}</main>
</body>
</html>
"""


def json_str(obj):
    import json

    return json.dumps(obj, ensure_ascii=False)
