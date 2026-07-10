from .layout import *  # noqa: F401,F403


def credentials_list(ctx, creds):
    bc = _breadcrumb(("Dashboard", "/"), ("Credentials", None))
    header = _html(
        """
        <div class="page-header">
          <h1>Credentials</h1>
          <div class="actions">
            <a href="/credentials/new" class="btn btn-primary">+ New Credential</a>
          </div>
        </div>
        """
    )
    if not creds:
        body = _html(
            f"""
            {bc}
            {header}
            <div class="empty-state">
              <p>No credentials yet. <a href="/credentials/new">Add your first credential</a>.</p>
            </div>
            """
        )
        return _page(ctx, "Credentials", body)
    rows_list = []
    for c in creds:
        cname = esc(c["name"])
        cdesc = esc(c.get("description", ""))
        desc_html = f'<div class="job-desc">{cdesc}</div>' if cdesc else ""
        rows_list.append(
            f"<tr>"
            f"<td><strong>{cname}</strong>{desc_html}</td>"
            f'<td style="width:180px;text-align:right">'
            f'<a href="/credentials/{cname}/edit" class="btn btn-secondary btn-sm">Edit</a> '
            f'<form class="inline-form" method="POST" action="/credentials/{cname}/delete"'
            f" onsubmit=\"return confirm('Delete credential {cname}?')\">"
            f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
            f"</form>"
            f"</td></tr>"
        )
    rows = "".join(rows_list)
    table = _html(
        f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Name</th><th style="width:180px"></th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
      """
    )
    body = _html(
        f"""
      {bc}
      {header}
      {table}
      """
    )
    return _page(ctx, "Credentials", body)


def credentials_form(ctx, cred=None, error=None):
    is_new = cred is None
    title = "New Credential" if is_new else f'Edit: {cred["name"]}'
    bc = _breadcrumb(("Dashboard", "/"), ("Credentials", "/credentials"), (title, None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    name_val = esc(cred["name"]) if cred else ""
    name_input = (
        (
            f'<input type="text" id="name" name="name" value="{name_val}" required'
            f' pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="my-credential">'
        )
        if is_new
        else (
            f'<input type="text" id="name" value="{name_val}" readonly'
            f' style="background:#f6f8fa;cursor:not-allowed">'
            f'<input type="hidden" name="name" value="{name_val}">'
        )
    )
    value_hint = "Enter the secret value" if is_new else "Enter the updated value"
    desc_val = esc(cred.get("description", "")) if cred else ""
    value_val = esc(cred.get("value", "")) if cred else ""
    action = "/credentials/new" if is_new else f'/credentials/{esc(cred["name"])}/edit'
    submit_label = "Create Credential" if is_new else "Save Changes"
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>{esc(title)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="{action}">
            <div class="form-group">
              <label for="name">Name <span class="hint">(letters, numbers, - and _ only)</span></label>
              {name_input}
            </div>
            <div class="form-group">
              <label for="cred-desc">Description <span class="hint">(optional)</span></label>
              <input type="text" id="cred-desc" name="description" value="{desc_val}" placeholder="What is this credential for?">
            </div>
            <div class="form-group">
              <label for="cred-value">Value <span class="hint">{esc(value_hint)}</span></label>
              <textarea id="cred-value" name="value" class="code" rows="6" autocomplete="off" spellcheck="false" placeholder="Paste value or multi-line content (e.g. SSH private key)&#10;-----BEGIN OPENSSH PRIVATE KEY-----&#10;...">{value_val}</textarea>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">{submit_label}</button>
              <a href="/credentials" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(ctx, title, body)
