from .layout import *  # noqa: F401,F403


def dashboard(ctx, jobs):
    permissions = ctx.permissions
    can_manage_jobs = permissions["can_manage_jobs"]
    if not jobs:
        create_html = (
            '<a href="/jobs/new">Create your first job</a>' if can_manage_jobs else ""
        )
        empty_text = f"No jobs yet. {create_html}." if create_html else "No jobs yet."
        body = f"""
      <div class="page-header"><h1>Dashboard</h1></div>
      <div class="empty-state">
        <p>{empty_text}</p>
      </div>
      """
        return _page(ctx, "Dashboard", body)

    all_labels = sorted({label for job in jobs for label in (job.get("labels") or [])})
    rows = []
    for job in jobs:
        lb = job.get("last_build")
        name = job["name"]
        labels = job.get("labels") or []
        label_key = "|" + "|".join(labels) + "|" if labels else ""
        labels_html = (
            (
                '<div class="label-list" style="margin-top:3px">'
                + "".join(
                    f'<span class="label-chip">{esc(label)}</span>' for label in labels
                )
                + "</div>"
            )
            if labels
            else ""
        )
        if lb:
            build_link = f'<a href="/jobs/{esc(name)}/builds/{esc(lb["id"])}"># {esc(lb["id"])}</a>'
            status_html = _badge(lb.get("status"))
            dur = esc(_fmt_duration(lb.get("duration")))
            started = lb.get("started_at") or lb.get("queued_at", "")
            time_html = f'<span data-time="{esc(started)}">{esc(started)}</span>'
        else:
            build_link = '<span class="text-muted">\u2014</span>'
            status_html = '<span class="text-muted">\u2014</span>'
            dur = "\u2014"
            time_html = "\u2014"
        desc = esc(job.get("description", ""))
        desc_html = f'<div class="job-desc">{desc}</div>' if desc else ""
        is_job_enabled = job.get("enabled", True)
        disabled_badge = (
            ' <span class="badge badge-disabled" style="font-size:11px">Disabled</span>'
            if not is_job_enabled
            else ""
        )
        labels_cell_html = labels_html or '<span class="text-muted">\u2014</span>'
        row_style = ' style="opacity:0.6"' if not is_job_enabled else ""
        rows.append(
            f"""
<tr data-labels="{esc(label_key)}"{row_style}>
  <td><a href="/jobs/{esc(name)}" class="job-link">{esc(name)}</a>{disabled_badge}{desc_html}</td>
  <td class="col-labels">{labels_cell_html}</td>
  <td class="col-num">{build_link}</td>
  <td class="col-time">{time_html}</td>
  <td class="col-dur">{dur}</td>
  <td class="col-status">{status_html}</td>
  <td class="col-weather weather-cell">{_weather(job.get("weather"), compact=True)}</td>
</tr>
"""
        )

    tabs = ""
    if all_labels:
        tab_buttons = [
            '<button type="button" class="dashboard-tab dashboard-tab-active" data-label="">All</button>'
        ]
        tab_buttons.extend(
            f'<button type="button" class="dashboard-tab" data-label="{esc(label)}">{esc(label)}</button>'
            for label in all_labels
        )
        tabs = (
            '<div class="dashboard-tabs" aria-label="Job label filters">'
            + "".join(tab_buttons)
            + "</div>"
        )

    table = f"""
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Job</th>
        <th class="col-labels">Labels</th>
        <th class="col-num">Last Build</th>
        <th class="col-time">Last Started</th>
        <th class="col-dur">Last Duration</th>
        <th class="col-status">Last Status</th>
        <th class="col-weather weather-cell">Stability</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>
"""
    body = '<div class="page-header"><h1>Dashboard</h1></div>' + tabs + table
    filter_js = """
      <script>
      (function() {
        var buttons = [].slice.call(document.querySelectorAll(".dashboard-tab"));
        var rows = [].slice.call(document.querySelectorAll("tbody tr[data-labels]"));
        if (!rows.length) {
          return;
        }
        function apply(label) {
          var token = label ? "|" + label + "|" : "";
          rows.forEach(function(row) {
            var labels = row.getAttribute("data-labels") || "";
            row.hidden = !!token && labels.indexOf(token) === -1;
          });
          buttons.forEach(function(button) {
            button.classList.toggle("dashboard-tab-active", (button.getAttribute("data-label") || "") === label);
          });
        }
        buttons.forEach(function(button) {
          button.addEventListener("click", function() {
            apply(button.getAttribute("data-label") || "");
          });
        });
      })();
      </script>
    """
    return _page(ctx, "Dashboard", body, extra_js=filter_js)


def job_detail(ctx, job, builds):
    permissions = ctx.permissions
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, None))
    has_params = bool(job.get("parameters"))
    is_enabled = job.get("enabled", True)

    if not is_enabled:
        build_btn = '<button type="button" class="btn btn-primary" disabled title="Job is disabled" style="opacity:0.4;cursor:not-allowed">Build Now</button>'
    elif permissions["can_run_builds"] and has_params:
        build_btn = f'<a href="/jobs/{esc(name)}/build" class="btn btn-primary">Build with Parameters\u2026</a>'
    elif permissions["can_run_builds"]:
        build_btn = (
            f'<form class="inline-form" method="POST" action="/jobs/{esc(name)}/build">'
            '<button type="submit" class="btn btn-primary">Build Now</button>'
            "</form>"
        )
    else:
        build_btn = ""

    workspace_btn = (
        f'<a href="/jobs/{esc(name)}/workspace" class="btn btn-secondary">Workspace</a>'
        if permissions["can_view_workspaces"]
        else ""
    )
    edit_btn = (
        f'<a href="/jobs/{esc(name)}/edit" class="btn btn-secondary">Edit</a>'
        if permissions["can_manage_jobs"]
        else ""
    )

    desc = esc(job.get("description", ""))
    desc_html = (
        f'<p class="text-muted" style="margin-top:6px">{desc}</p>' if desc else ""
    )
    labels = job.get("labels") or []
    labels_html = (
        (
            '<div class="label-list" style="margin-top:8px">'
            + "".join(
                f'<span class="label-chip">{esc(label)}</span>' for label in labels
            )
            + "</div>"
        )
        if labels
        else ""
    )
    header = f"""
<div class="page-header job-header">
  <div class="job-header-main">
    <h1>{esc(name)}{' <span class="badge badge-disabled">Disabled</span>' if not is_enabled else ''}</h1>
    {desc_html}{labels_html}
  </div>
  <div class="actions">
    {build_btn}
    {workspace_btn}
    {edit_btn}
  </div>
</div>
"""

    if not builds:
        builds_html = '<div class="empty-state" style="padding:30px 0"><p>No builds yet.</p></div>'
    else:
        rows = []
        for b in reversed(builds):
            bid = b["id"]
            params = b.get("parameters") or {}
            params_str = (
                ", ".join(f"{k}={v}" for k, v in params.items()) if params else "\u2014"
            )
            started = b.get("started_at") or b.get("queued_at", "")
            tb = b.get("triggered_by") or ""
            if tb == "cron":
                triggered_html = '<span class="text-muted" style="font-size:12px">&#9201; Cron</span>'
            elif tb:
                triggered_html = f'<span style="font-size:12px">{esc(tb)}</span>'
            else:
                triggered_html = '<span class="text-muted">\u2014</span>'
            rows.append(
                f"""
<tr>
  <td class="col-num"><a href="/jobs/{esc(name)}/builds/{esc(bid)}"># {esc(bid)}</a></td>
  <td class="col-time"><span data-time="{esc(started)}">{esc(started)}</span></td>
  <td class="col-dur">{esc(_fmt_duration(b.get("duration")))}</td>
  <td class="col-status">{_badge(b.get("status"))}</td>
  <td style="font-size:12px">{triggered_html}</td>
  <td class="text-muted" style="font-size:12px">{esc(params_str)}</td>
</tr>
"""
            )

        builds_html = f"""
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th class="col-num">#</th>
        <th class="col-time">Started</th>
        <th class="col-dur">Duration</th>
        <th class="col-status">Status</th>
        <th>Triggered by</th>
        <th>Parameters</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>
"""

    body = (
        bc
        + header
        + '<div class="section-title-row">'
        + '<div class="section-title">Build History</div>'
        + _weather(job.get("weather"), compact=True)
        + "</div>"
        + builds_html
    )
    return _page(ctx, name, body)


def workspace(ctx, job, files):
    permissions = ctx.permissions
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, f"/jobs/{name}"), ("Workspace", None))

    if not files:
        files_html = (
            '<div class="empty-state" style="padding:30px 0">'
            "<p>The workspace is empty. Run the job to generate files.</p>"
            "</div>"
        )
    else:

        def _fmt_size(n):
            if n < 1024:
                return f"{n} B"
            if n < 1024 * 1024:
                return f"{n / 1024:.1f} KB"
            return f"{n / 1024 / 1024:.1f} MB"

        rows = "".join(
            f"<tr>"
            f'<td><a href="/jobs/{esc(name)}/workspace/{esc(f["path"])}">{esc(f["path"])}</a></td>'
            f'<td class="text-muted" style="font-size:12px;white-space:nowrap">{esc(_fmt_size(f["size"]))}</td>'
            f'<td class="text-muted col-time"><span data-time="{esc(f["mtime"])}">{esc(f["mtime"])}</span></td>'
            f"</tr>"
            for f in files
        )
        files_html = (
            '<div class="table-wrap"><table>'
            '<thead><tr><th>File</th><th>Size</th><th class="col-time">Modified</th></tr></thead>'
            f"<tbody>{rows}</tbody>"
            "</table></div>"
        )

    clear_btn = (
        f'<form class="inline-form" method="POST" action="/jobs/{esc(name)}/workspace/clear"'
        f" onsubmit=\"return confirm('Clear the workspace for {esc(name)}?')\">"
        f'<button type="submit" class="btn btn-danger">Clear Workspace</button>'
        f"</form>"
        if permissions["can_clear_workspaces"]
        else ""
    )

    header = (
        f'<div class="page-header">'
        f"<h1>Workspace: {esc(name)}</h1>"
        f'<div class="actions">'
        f"{clear_btn}"
        f'<a href="/jobs/{esc(name)}" class="btn btn-secondary">Back to Job</a>'
        f"</div></div>"
    )
    body = bc + header + files_html
    return _page(ctx, f"Workspace: {name}", body)


def job_form(ctx, job=None, error=None, available_creds=None):
    is_new = job is None
    title = "New Job" if is_new else f'Edit: {job["name"]}'
    bc = _breadcrumb(("Dashboard", "/"), (title, None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""

    name_val = esc(job["name"]) if job else ""
    name_input = (
        (
            f'<input type="text" id="name" name="name" value="{name_val}" required'
            f' pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="my-job">'
        )
        if is_new
        else (
            f'<input type="text" id="name" name="name" value="{name_val}" readonly'
            f' style="background:#f6f8fa;cursor:not-allowed">'
            f'<input type="hidden" name="name" value="{name_val}">'
        )
    )

    desc_val = esc(job.get("description", "")) if job else ""
    raw_mb = job.get("max_builds") if job else None
    max_builds_val = esc(str(raw_mb)) if raw_mb is not None else ""
    enabled_val = True if job is None else bool(job.get("enabled", True))
    disabled_attr = " checked" if not enabled_val else ""
    labels_val = esc(", ".join(job.get("labels") or [])) if job else ""
    trigger = (job.get("trigger") or {}) if job else {}
    trigger_type = trigger.get("type", "manual")
    cron_schedule_val = (
        esc(trigger.get("schedule", "")) if trigger_type == "cron" else ""
    )
    gitpoll_interval_val = (
        esc(str(trigger.get("interval", ""))) if trigger_type == "gitpoll" else ""
    )
    notify_on_failure = (
        True if job is None else bool(job.get("notify_on_failure", True))
    )
    params_json = json_str(job.get("parameters", [])) if job else "[]"
    steps = job.get("steps") if job else None
    if not steps:
        steps = [{"name": "Script 1", "script": "", "image": ""}]
    steps_json = json_str(steps)
    creds_json = json_str(job.get("credentials", []) if job else [])
    available_creds = available_creds or []
    git_cfg = (job.get("git") or {}) if job else {}
    git_url_val = esc(git_cfg.get("url", ""))
    git_branch_val = esc(git_cfg.get("branch", ""))
    git_cred_val = git_cfg.get("credential", "") or ""
    git_shallow = git_cfg.get("shallow", True)
    form_action = "/jobs/new" if is_new else f'/jobs/{esc(job["name"])}/edit'

    git_shallow_attr = " checked" if git_shallow else ""
    notify_on_failure_attr = " checked" if notify_on_failure else ""
    trigger_manual_attr = " checked" if trigger_type not in ("cron", "gitpoll") else ""
    trigger_cron_attr = " checked" if trigger_type == "cron" else ""
    trigger_gitpoll_attr = " checked" if trigger_type == "gitpoll" else ""
    trigger_cron_hidden = " hidden" if trigger_type != "cron" else ""
    trigger_gitpoll_hidden = " hidden" if trigger_type != "gitpoll" else ""
    submit_label = "Create Job" if is_new else "Save Changes"
    cancel_href = "/" if is_new else "/jobs/" + esc(job["name"])
    delete_btn = (
        f'<button type="submit" class="btn btn-danger" formmethod="POST" formaction="/jobs/{esc(job["name"])}/delete" formnovalidate onclick="return confirm(\'Delete job {esc(job["name"])}?\')">Delete Job</button>'
        if not is_new
        else ""
    )

    if available_creds:
        git_credential_field = (
            '<select id="git-credential" name="git_credential" style="max-width:300px">'
            '<option value="">None</option>'
            + "".join(
                f'<option value="{esc(c)}"{" selected" if c == git_cred_val else ""}>{esc(c)}</option>'
                for c in available_creds
            )
            + "</select>"
        )
        credentials_field = _html(
            f"""
            <div class="cred-editor" id="cred-editor">
              <div class="cred-header"><span>Credential</span><span>Env Var Name</span><span>Type</span><span>Actions</span></div>
              <div class="cred-add"><button type="button" id="add-cred-btn" class="btn btn-secondary btn-sm">+ Add</button></div>
            </div>
            <input type="hidden" id="credentials-json" name="credentials_json" value="{esc(creds_json)}">
            """
        )
    else:
        git_credential_field = _html(
            """
            <input type="text" id="git-credential" name="git_credential" value="" style="display:none">
            <p class="text-muted" style="font-size:13px;margin-top:4px">No credentials defined. <a href="/credentials/new">Add a credential</a> to use SSH key auth.</p>
            """
        )
        credentials_field = _html(
            f"""
            <p class="text-muted" style="font-size:13px;margin-top:6px">No credentials defined. <a href="/credentials/new">Add a credential</a> first.</p>
            <input type="hidden" name="credentials_json" value="{esc(creds_json)}">
            """
        )

    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>{esc(title)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="{form_action}">
            <div class="form-section">
              <div class="form-section-title">Basics</div>
              <div class="form-section-hint">Name the job and add the metadata people use to identify it.</div>
              <div class="form-group">
                <label for="name">Name <span class="hint">(letters, numbers, - and _ only)</span></label>
                {name_input}
              </div>
              <div class="form-group">
                <label for="desc">Description <span class="hint">(optional)</span></label>
                <input type="text" id="desc" name="description" value="{desc_val}" placeholder="What does this job do?">
              </div>
              <div class="form-group">
                <label for="job-labels">Labels <span class="hint">(optional, space or comma separated)</span></label>
                <input type="text" id="job-labels" name="labels" value="{labels_val}" placeholder="production qa techops">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="disabled" value="1"{disabled_attr} style="width:auto">
                  Disabled <span class="hint">(check to prevent this job from being built)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Source Code</div>
              <div class="form-section-hint">Optionally check out a Git repository into the workspace before scripts run.</div>
              <div class="form-group">
                <label for="git-url">Repository URL <span class="hint">(leave blank to skip checkout)</span></label>
                <input type="text" id="git-url" name="git_url" value="{git_url_val}" placeholder="git@github.com:user/repo.git">
              </div>
              <div class="form-group">
                <label for="git-branch">Branch <span class="hint">(default: main)</span></label>
                <input type="text" id="git-branch" name="git_branch" value="{git_branch_val}" placeholder="main" style="max-width:220px">
              </div>
              <div class="form-group">
                <label for="git-credential">SSH Key Credential <span class="hint">(optional)</span></label>
                {git_credential_field}
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="git_shallow" value="1"{git_shallow_attr} style="width:auto">
                  Shallow clone <span class="hint">(recommended: fetches only the latest commit)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Scheduling</div>
              <div class="form-section-hint">Control retention and decide whether the job runs manually or on a cron schedule.</div>
              <div class="form-group">
                <label for="job-max-builds">Max build history <span class="hint">(leave blank to use the server default)</span></label>
                <input type="number" id="job-max-builds" name="max_builds" value="{max_builds_val}" min="1" placeholder="e.g. 10" style="max-width:120px">
              </div>
              <div class="form-group">
                <label>Trigger</label>
                <div class="trigger-options">
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="manual"{trigger_manual_attr}> Manual</label>
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="cron"{trigger_cron_attr}> Cron schedule</label>
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="gitpoll"{trigger_gitpoll_attr}> Git poll</label>
                </div>
                <div class="trigger-cron-row" id="trigger-cron-row"{trigger_cron_hidden}>
                  <input type="text" id="cron_schedule" name="cron_schedule" value="{cron_schedule_val}" placeholder="*/5 * * * *" style="max-width:220px;margin-top:6px">
                  <div class="hint" style="margin-top:4px">5 fields: minute hour day month weekday &nbsp;&middot;&nbsp; e.g. <code>0 * * * *</code> = every hour, <code>30 6 * * 1</code> = Mon 06:30</div>
                  <div class="hint" id="cron-next-run" style="margin-top:6px"></div>
                </div>
                <div class="trigger-gitpoll-row" id="trigger-gitpoll-row"{trigger_gitpoll_hidden}>
                  <input type="number" id="gitpoll_interval" name="gitpoll_interval" value="{gitpoll_interval_val}" placeholder="300" min="300" style="max-width:220px;margin-top:6px">
                  <div class="hint" style="margin-top:4px">Polling interval in seconds (default: 300, min: 300)</div>
                </div>
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer;margin-top:10px">
                  <input type="checkbox" name="notify_on_failure" value="1"{notify_on_failure_attr} style="width:auto">
                  Send failure notification emails <span class="hint">(enabled by default; clear to opt out for this job)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Build Inputs</div>
              <div class="form-section-hint">Define user-supplied parameters and any credentials that should be injected into the build environment.</div>
              <div class="form-group">
                <label>Parameters <span class="hint">(passed as environment variables)</span></label>
                <div class="params-editor" id="params-editor">
                  <div class="params-header"><span>Name</span><span>Description</span><span>Default</span><span>Regex</span><span>Actions</span></div>
                  <div class="params-add"><button type="button" id="add-param-btn" class="btn btn-secondary btn-sm">+ Add Parameter</button></div>
                </div>
                <input type="hidden" id="params-json" name="params_json" value="{esc(params_json)}">
              </div>
              <div class="form-group">
                <label>Credentials <span class="hint">(inject secrets into the build environment)</span></label>
                {credentials_field}
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Execution</div>
              <div class="form-section-hint">Add one or more steps. Every step runs inside an ephemeral Docker container.</div>
              <div class="form-group">
                <label>Steps <span class="hint">(run in order)</span></label>
                <div class="script-sections-editor" id="steps-editor">
                  <div class="steps-add"><button type="button" id="add-step-btn" class="btn btn-secondary btn-sm">+ Add Step</button></div>
                </div>
                <input type="hidden" id="steps-json" name="steps_json" value="{esc(steps_json)}">
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">{submit_label}</button>
              {delete_btn}
              <a href="{cancel_href}" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )

    available_creds_js = (
        f"<script>window._pipelineAvailableCreds={json_str(available_creds)};</script>"
    )
    creds_js = (f"<script>{_CREDENTIALS_EDITOR_JS}</script>") if available_creds else ""
    trigger_js = """
  <script>
  (function () {
    var radios = document.querySelectorAll('input[name="trigger_type"]');
    var cronRow = document.getElementById("trigger-cron-row");
    var cronInput = document.getElementById("cron_schedule");
    var preview = document.getElementById("cron-next-run");
    var gitpollRow = document.getElementById("trigger-gitpoll-row");
    var gitpollRadio = document.querySelector('input[name="trigger_type"][value="gitpoll"]');
    var gitUrlInput = document.getElementById("git-url");
    var gitBranchInput = document.getElementById("git-branch");
    var gitCredentialInput = document.getElementById("git-credential");
    var gitShallowInput = document.querySelector('input[name="git_shallow"]');
    var timer = null;

    function hasRepositoryUrl() {
      return !!(gitUrlInput && gitUrlInput.value.trim() !== "");
    }

    function setPreview(text, isError) {
      preview.textContent = text || "";
      preview.style.color = isError ? "#a40e26" : "";
    }

    function fetchPreview() {
      var schedule = cronInput.value.trim();
      if (!schedule) {
        setPreview("Enter a cron schedule to preview the next run.", false);
        return;
      }
      fetch("/cron/preview?schedule=" + encodeURIComponent(schedule), {
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          return r.json().then(function (data) {
            return { ok: r.ok, data: data };
          });
        })
        .then(function (result) {
          if (result.ok) {
            setPreview(result.data.message || "", false);
          } else {
            setPreview(
              result.data.error || "Could not preview the next run.",
              true,
            );
          }
        })
        .catch(function () {
          setPreview("Could not preview the next run.", true);
        });
    }

    function schedulePreview() {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(fetchPreview, 150);
    }

    function updateSourceCodeAvailability() {
      var hasGit = hasRepositoryUrl();
      if (gitBranchInput) {
        gitBranchInput.disabled = !hasGit;
      }
      if (gitCredentialInput) {
        gitCredentialInput.disabled = !hasGit;
      }
      if (gitShallowInput) {
        gitShallowInput.disabled = !hasGit;
      }
      [gitBranchInput, gitCredentialInput, gitShallowInput].forEach(function (el) {
        if (!el) {
          return;
        }
        var group = el.closest(".form-group");
        if (group) {
          group.style.opacity = hasGit ? "" : "0.6";
        }
      });
    }

    function updateGitpollAvailability() {
      var hasGit = hasRepositoryUrl();
      if (gitpollRadio) {
        gitpollRadio.disabled = !hasGit;
      }
      var label = gitpollRadio && gitpollRadio.closest("label");
      if (label) {
        label.style.opacity = hasGit ? "" : "0.4";
        label.style.cursor = hasGit ? "" : "not-allowed";
      }
      if (!hasGit && gitpollRadio && gitpollRadio.checked) {
        var manualRadio = document.querySelector('input[name="trigger_type"][value="manual"]');
        if (manualRadio) {
          manualRadio.checked = true;
        }
      }
    }

    function update() {
      updateSourceCodeAvailability();
      updateGitpollAvailability();
      var val = document.querySelector('input[name="trigger_type"]:checked').value;
      cronRow.hidden = val !== "cron";
      gitpollRow.hidden = val !== "gitpoll";
      if (val === "cron") {
        cronInput.required = true;
        schedulePreview();
      } else {
        cronInput.required = false;
        setPreview("", false);
      }
    }

    cronInput.addEventListener("input", schedulePreview);
    if (gitUrlInput) {
      gitUrlInput.addEventListener("input", update);
    }
    radios.forEach(function (r) {
      r.addEventListener("change", update);
    });
    update();
  })();
  </script>
  """
    return _page(
        ctx,
        title,
        body,
        extra_js=f"{available_creds_js}<script>{_PARAMS_EDITOR_JS}</script><script>{_STEPS_EDITOR_JS}</script>{creds_js}{trigger_js}",
    )
