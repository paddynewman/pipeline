from .layout import *  # noqa: F401,F403


def settings(ctx, cfg, available_creds=None, error=None):
    bc = _breadcrumb(("Dashboard", "/"), ("Settings", None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    max_builds = esc(str(cfg.get("max_builds", 10)))
    max_concurrent_jobs = esc(str(cfg.get("max_concurrent_jobs", 2)))
    queue_paused = bool(cfg.get("queue_paused", False))
    queue_pause_message = esc(cfg.get("queue_pause_message", "Job queue is paused."))
    default_script_header = esc(cfg.get("default_script_header", ""))
    mount_docker_socket = bool(cfg.get("mount_docker_socket", False))
    email_cfg = cfg.get("email_notifications", {}) or {}
    available_creds = available_creds or []
    recipients = email_cfg.get("recipients", [])
    if isinstance(recipients, list):
        recipients_val = esc("\n".join(recipients))
    else:
        recipients_val = esc(recipients)
    from_address_val = esc(email_cfg.get("from_address", ""))
    smtp_host_val = esc(email_cfg.get("smtp_host", ""))
    smtp_port_val = esc(str(email_cfg.get("smtp_port", 587)))
    smtp_security = email_cfg.get("smtp_security", "starttls")
    smtp_username_val = esc(email_cfg.get("smtp_username", ""))
    smtp_credential_val = email_cfg.get("smtp_credential", "")
    queue_paused_attr = " checked" if queue_paused else ""
    mount_docker_socket_attr = " checked" if mount_docker_socket else ""
    smtp_credential_field = (
        (
            '<select id="notification-smtp-credential" name="notification_smtp_credential" style="max-width:300px">'
            + '<option value="">None</option>'
            + "".join(
                f'<option value="{esc(c)}"{" selected" if c == smtp_credential_val else ""}>{esc(c)}</option>'
                for c in available_creds
            )
            + "</select>"
        )
        if available_creds
        else (
            '<input type="hidden" name="notification_smtp_credential" value="">'
            '<p class="text-muted" style="font-size:13px;margin-top:4px">No credentials defined. <a href="/credentials/new">Add a credential</a> to enable SMTP auth.</p>'
        )
    )
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Settings</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings">
            <div class="form-section" style="margin-top:0;padding-top:0;border-top:none">
              <div class="form-section-title">Execution Defaults</div>
              <div class="form-group">
                <label for="default-script-header">Default script header <span class="hint">(prepended only when a step script does not define its own shebang)</span></label>
                <textarea id="default-script-header" name="default_script_header" class="code" rows="6" spellcheck="false">{default_script_header}</textarea>
              </div>
              <div class="form-group">
                <label for="max-builds">Max build history <span class="hint">(default for all jobs; jobs can override this)</span></label>
                <input type="number" id="max-builds" name="max_builds" value="{max_builds}" min="1" style="max-width:120px">
              </div>
              <div class="form-group">
                <label for="max-concurrent-jobs">Max concurrent jobs <span class="hint">(server-wide queue limit; default: 2)</span></label>
                <input type="number" id="max-concurrent-jobs" name="max_concurrent_jobs" value="{max_concurrent_jobs}" min="1" style="max-width:120px">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="queue_paused" value="1"{queue_paused_attr} style="width:auto">
                  Pause the job queue <span class="hint">(running jobs continue; queued jobs wait)</span>
                </label>
              </div>
              <div class="form-group">
                <label for="queue-pause-message">Queue pause banner message</label>
                <input type="text" id="queue-pause-message" name="queue_pause_message" value="{queue_pause_message}" placeholder="Job queue is paused.">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="mount_docker_socket" value="1"{mount_docker_socket_attr} style="width:auto">
                  Mount host Docker socket into job containers <span class="hint">(disabled by default; enable to allow job containers to talk to the host Docker daemon)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Failure Notifications</div>
              <div class="form-section-hint">Configure where failed build emails are sent. Jobs notify by default unless they opt out.</div>
              <div class="form-group">
                <label for="notification-recipients">Notification email addresses <span class="hint">(comma or newline separated; leave blank to disable)</span></label>
                <input type="text" id="notification-recipients" name="notification_recipients" value="{recipients_val}" spellcheck="false" placeholder="user1@example.com, user2@example.com">
              </div>
              <div class="form-group">
                <label for="notification-from-address">From address <span class="hint">(optional; defaults to SMTP username or the first recipient)</span></label>
                <input type="text" id="notification-from-address" name="notification_from_address" value="{from_address_val}" placeholder="pipeline@example.com">
              </div>
              <div class="form-group">
                <label for="notification-smtp-host">SMTP host</label>
                <input type="text" id="notification-smtp-host" name="notification_smtp_host" value="{smtp_host_val}" placeholder="smtp.example.com">
              </div>
              <div class="form-group">
                <label for="notification-smtp-port">SMTP port</label>
                <input type="number" id="notification-smtp-port" name="notification_smtp_port" value="{smtp_port_val}" min="1" max="65535" style="max-width:120px">
              </div>
              <div class="form-group">
                <label for="notification-smtp-security">SMTP security</label>
                <select id="notification-smtp-security" name="notification_smtp_security" style="max-width:180px">
                  <option value="none"{" selected" if smtp_security == "none" else ""}>None</option>
                  <option value="starttls"{" selected" if smtp_security == "starttls" else ""}>STARTTLS</option>
                  <option value="ssl"{" selected" if smtp_security == "ssl" else ""}>SSL/TLS</option>
                </select>
              </div>
              <div class="form-group">
                <label for="notification-smtp-username">SMTP username <span class="hint">(optional)</span></label>
                <input type="text" id="notification-smtp-username" name="notification_smtp_username" value="{smtp_username_val}" placeholder="pipeline-user">
              </div>
              <div class="form-group">
                <label for="notification-smtp-credential">SMTP credential <span class="hint">(optional password from Credentials)</span></label>
                {smtp_credential_field}
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save Settings</button>
            </div>
          </form>
        </div>
        """
    )
    return _page(ctx, "Settings", body)
