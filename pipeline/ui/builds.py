from .layout import *  # noqa: F401,F403


def _render_log_sections(sections):
    def _compact_details(details):
        details = details or ""
        if details.startswith("Docker image: "):
            details = details[len("Docker image: ") :]
        details = details.replace(" | Host: ", " | ")
        if details.endswith(" | localhost"):
            details = details[: -len(" | localhost")]
        return details

    parts = []
    for index, section in enumerate(sections):
        text = section["text"]
        script = section.get("script", "")
        details = _compact_details(section.get("details", ""))
        heading_html = (
            '<div class="log-section-heading">'
            f'<div class="log-section-title">{esc(section["name"])}</div>'
            "</div>"
        )
        # Only show Docker image details when expanded
        details_html = (
            f'<div class="log-section-subtitle">Docker image: {esc(details)}</div>'
            if details
            else ""
        )
        panel_header_html = f'<div class="log-panel-header">{heading_html}</div>'
        if script:
            panel_top_html = (
                '<details class="log-script-details">'
                '<summary class="log-panel-header log-script-summary">'
                f"{heading_html}"
                "</summary>"
                '<div class="log-script-body">'
                + (
                    f'<div class="log-script-meta">{details_html}</div>'
                    if details_html
                    else ""
                )
                + f'<div class="log-script-wrap">{esc(script)}</div>'
                + "</div>"
                "</details>"
            )
        else:
            panel_top_html = panel_header_html
        log_html = (
            f'<div class="log-wrap" id="log-section-{index}">{esc(text)}</div>'
            if text
            else f'<div id="log-section-{index}"></div>'
        )
        parts.append(
            '<div class="log-section">'
            '<div class="log-panel">'
            f"{panel_top_html}"
            f"{log_html}"
            "</div>"
            "</div>"
        )
    return '<div class="log-sections" id="log-sections">' + "".join(parts) + "</div>"


def build_form(ctx, job, error=None, values=None):
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, f"/jobs/{name}"), ("Build", None))
    params = job.get("parameters") or []
    values = values or {}
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""

    fields = []
    has_regex_params = False
    for p in params:
        raw_name = p.get("name", "")
        pname = esc(raw_name)
        pdesc = esc(p.get("description", ""))
        pdef = esc(values.get(raw_name, p.get("default", "")))
        pregex = p.get("regex", "")
        pregex_esc = esc(pregex)
        label_hint = f' <span class="hint">{pdesc}</span>' if pdesc else ""
        regex_hint = f' <span class="hint">Regex: {pregex_esc}</span>' if pregex else ""
        regex_attr = f' data-regex="{pregex_esc}"' if pregex else ""
        if pregex:
            has_regex_params = True
        pattern_attr = f' pattern="{pregex_esc}"' if pregex else ""
        title_attr = f' title="Must match: {pregex_esc}"' if pregex else ""
        fields.append(
            _html(
                f"""
          <div class="form-group">
            <label for="p_{pname}">{pname}{label_hint}{regex_hint}</label>
            <input type="text" id="p_{pname}" name="param_{pname}" value="{pdef}"{regex_attr}{pattern_attr}{title_attr}>
          </div>
          """
            )
        )

    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Build: {esc(name)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/jobs/{esc(name)}/build">
            {''.join(fields)}
            <div class="form-actions">
              <button type="submit" class="btn btn-primary" id="run-build-btn">Run Build</button>
              <a href="/jobs/{esc(name)}" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )

    validate_js = ""
    if has_regex_params:
        validate_js = _html(
            """
            <script>
            (function () {
              var form = document.querySelector('form[action$="/build"]');
              var submitBtn = document.getElementById("run-build-btn");
              if (!form || !submitBtn) return;

              var fields = [].slice.call(form.querySelectorAll("input[data-regex]"));
              if (!fields.length) return;

              function validateField(field, showMessage) {
                var pattern = field.getAttribute("data-regex") || "";
                if (!pattern) {
                  field.setCustomValidity("");
                  return true;
                }
                var ok = false;
                try {
                  ok = new RegExp("^(?:" + pattern + ")$").test(field.value || "");
                } catch (e) {
                  ok = false;
                }
                if (ok) {
                  field.setCustomValidity("");
                } else {
                  field.setCustomValidity("Must match the configured regex.");
                  if (showMessage) {
                    field.reportValidity();
                  }
                }
                return ok;
              }

              function updateSubmitState() {
                var allValid = true;
                fields.forEach(function (field) {
                  if (!validateField(field, false)) {
                    allValid = false;
                  }
                });
                submitBtn.disabled = !allValid;
                submitBtn.title = allValid ? "" : "Fix invalid parameters before running the build.";
              }

              fields.forEach(function (field) {
                field.addEventListener("blur", function () {
                  validateField(field, true);
                  updateSubmitState();
                });
                field.addEventListener("input", function () {
                  validateField(field, false);
                  updateSubmitState();
                });
              });

              form.addEventListener("submit", function (event) {
                updateSubmitState();
                if (submitBtn.disabled) {
                  event.preventDefault();
                }
              });

              updateSubmitState();
            })();
            </script>
            """
        )

    return _page(
        ctx,
        f"Build: {name}",
        body,
        extra_js=validate_js,
    )


def _live_log_js(section_log_urls, status_url):
    import json as _json

    urls_js = _json.dumps(section_log_urls)
    su = _json.dumps(status_url)
    return _html(
        f"""
        <script>
        (function() {{
          var sectionUrls = {urls_js};
          var statusUrl = {su};
          var pollTimer = null;

          function poll() {{
            sectionUrls.forEach(function(url, i) {{
              var el = document.getElementById("log-section-" + i);
              if (!el) return;
              fetch(url + "?_=" + Date.now())
                .then(function(r) {{ return r.text(); }})
                .then(function(t) {{
                  if (t) {{
                    el.classList.add("log-wrap");
                    el.textContent = t;
                    el.scrollTop = el.scrollHeight;
                  }}
                }})
                .catch(function() {{}});
            }});
          }}

          var badges = {{
            success: ["badge-success", "\u2713 Success"],
            failure: ["badge-failure", "\u2717 Failure"],
            running: ["badge-running", "\u29d7 Running"],
            queued: ["badge-aborted", "\u23f3 Queued"],
            aborted: ["badge-aborted", "\u25a0 Aborted"]
          }};

          function fmtDuration(secs) {{
            if (secs === null || secs === undefined) return "\u2014";
            secs = parseFloat(secs);
            if (secs < 60) return secs.toFixed(1) + "s";
            var m = Math.floor(secs / 60);
            var s = Math.floor(secs % 60);
            return m + "m " + s + "s";
          }}

          function finish(d) {{
            var badgeEl = document.getElementById("build-status-badge");
            if (badgeEl) {{
              var b = badges[d.status] || ["badge-aborted", d.status || "\u2014"];
              badgeEl.innerHTML =
                '<span class="badge ' + b[0] + '">' + b[1] + "</span>";
            }}
            var durEl = document.getElementById("build-duration");
            if (durEl) durEl.textContent = fmtDuration(d.duration);
            if (d.finished_at) {{
              var finTime = document.getElementById("build-finished-time");
              if (finTime) {{
                finTime.setAttribute("data-time", d.finished_at);
                finTime.title = d.finished_at;
                finTime.textContent = window.timeAgo
                  ? window.timeAgo(d.finished_at)
                  : d.finished_at;
              }}
              var finItem = document.getElementById("build-finished-item");
              if (finItem) finItem.style.display = "";
            }}
            var cancelForm = document.getElementById("cancel-build-form");
            if (cancelForm) cancelForm.style.display = "none";
            var rerunForm = document.getElementById("rerun-build-form");
            if (rerunForm) rerunForm.style.display = "";
          }}

          function check(delay) {{
            window.setTimeout(function() {{
              fetch(statusUrl + "?_=" + Date.now())
                .then(function(r) {{ return r.json(); }})
                .then(function(d) {{
                  if (d.status !== "running") {{
                    poll();
                    if (pollTimer) window.clearInterval(pollTimer);
                    finish(d);
                    return;
                  }}
                  check(500);
                }})
                .catch(function() {{
                  check(1000);
                }});
            }}, delay || 0);
          }}

          pollTimer = setInterval(poll, 2000);
          poll();
          check();
        }})();
        </script>
        """
    )


def build_detail(ctx, job, build, section_logs):
    permissions = ctx.permissions
    name = job["name"]
    bid = build["id"]
    status = build.get("status", "")
    bc = _breadcrumb(
        ("Dashboard", "/"),
        (name, f"/jobs/{name}"),
        (f"Build #{bid}", None),
    )

    params = build.get("parameters") or {}
    params_html = ""
    if params:
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in params.items()
        )
        params_html = (
            '<div class="meta-item" style="min-width:200px">'
            '<div class="meta-label">Parameters</div>'
            '<div class="meta-value">'
            f'<table class="param-table"><tbody>{rows}</tbody></table>'
            "</div></div>"
        )

    cancel_btn = ""
    if permissions["can_run_builds"] and status in ("running", "queued"):
        cancel_btn = (
            f'<form class="inline-form" id="cancel-build-form" method="POST"'
            f' action="/jobs/{esc(name)}/builds/{esc(bid)}/cancel">'
            '<button type="submit" class="btn btn-warning btn-sm">Cancel Build</button>'
            "</form>"
        )

    rerun_eligible = (
        permissions["can_run_builds"]
        and job.get("enabled", True)
        and bool(job.get("parameters"))
    )
    is_live = status == "running"
    rerun_btn = ""
    if rerun_eligible and (status not in ("running", "queued") or is_live):
        hidden = ' style="display:none"' if is_live else ""
        rerun_btn = (
            f'<form class="inline-form" id="rerun-build-form" method="POST"{hidden}'
            f' action="/jobs/{esc(name)}/builds/{esc(bid)}/rerun">'
            '<button type="submit" class="btn btn-primary btn-sm">Re-run Build</button>'
            "</form>"
        )

    started = build.get("started_at", "")
    queued_at = build.get("queued_at", "")
    started_label = "Started"
    started_value = started
    if not started and queued_at:
        started_label = "Queued"
        started_value = queued_at
    finished = build.get("finished_at", "")
    tb = build.get("triggered_by") or ""
    if tb == "cron":
        triggered_html = "&#9201; Cron schedule"
    elif tb:
        triggered_html = esc(tb)
    else:
        triggered_html = "\u2014"
    meta = (
        '<div class="meta-grid">'
        f'<div class="meta-item"><div class="meta-label">Status</div>'
        f'<div class="meta-value" id="build-status-badge">{_badge(status)}</div></div>'
        f'<div class="meta-item"><div class="meta-label">{esc(started_label)}</div>'
        f'<div class="meta-value"><span data-time="{esc(started_value)}">{esc(started_value)}</span></div></div>'
        f'<div class="meta-item"><div class="meta-label">Duration</div>'
        f'<div class="meta-value" id="build-duration">{esc(_fmt_duration(build.get("duration")))}</div></div>'
        f'<div class="meta-item"><div class="meta-label">Triggered by</div>'
        f'<div class="meta-value">{triggered_html}</div></div>'
        + (
            '<div class="meta-item" id="build-finished-item"'
            + ("" if finished else ' style="display:none"')
            + '><div class="meta-label">Finished</div>'
            f'<div class="meta-value"><span id="build-finished-time" data-time="{esc(finished)}">{esc(finished)}</span></div></div>'
        )
        + params_html
        + "</div>"
    )

    log_section = (
        '<div class="section-title">'
        "Log "
        f'<a href="/jobs/{esc(name)}/builds/{esc(bid)}/log" class="text-muted" style="font-size:12px;font-weight:500;margin-left:8px">View as plain text</a>'
        "</div>" + f"{_render_log_sections(section_logs)}"
    )

    header = (
        f'<div class="page-header">'
        f"<h1>Build #{esc(bid)}: {esc(name)}</h1>"
        f'<div class="actions">{rerun_btn}{cancel_btn}</div>'
        f"</div>"
    )

    body = bc + header + meta + log_section

    extra_js = ""
    if status == "running":
        section_urls = [
            f"/jobs/{esc(name)}/builds/{esc(bid)}/log/{i + 1}"
            for i in range(len(section_logs))
        ]
        extra_js = _live_log_js(
            section_urls,
            f"/jobs/{esc(name)}/builds/{esc(bid)}/status",
        )

    return _page(
        ctx,
        f"Build #{bid}: {name}",
        body,
        extra_js=extra_js,
    )
