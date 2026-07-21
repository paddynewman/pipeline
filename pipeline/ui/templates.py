from .layout import *  # noqa: F401,F403


def templates_list(ctx, templates):
    bc = _breadcrumb(("Dashboard", "/"), ("Templates", None))
    header = _html(
        """
        <div class="page-header">
          <h1>Step Templates</h1>
          <div class="actions">
            <a href="/templates/new" class="btn btn-primary">+ New Template</a>
          </div>
        </div>
        """
    )
    if not templates:
        body = _html(
            f"""
            {bc}
            {header}
            <div class="empty-state">
              <p>No templates yet. <a href="/templates/new">Create your first template</a>.</p>
            </div>
            """
        )
        return _page(ctx, "Templates", body)
    rows_list = []
    for t in templates:
        tname = esc(t["name"])
        tdesc = esc(t.get("description", ""))
        desc_html = f'<div class="job-desc">{tdesc}</div>' if tdesc else ""
        image = esc(t.get("image", ""))
        image_html = (
            f'<code style="font-size:12px">{image}</code>'
            if image
            else '<span class="text-muted">\u2014</span>'
        )
        rows_list.append(
            f"<tr>"
            f"<td><strong>{tname}</strong>{desc_html}</td>"
            f"<td>{image_html}</td>"
            f'<td style="width:180px;text-align:right">'
            f'<a href="/templates/{tname}/edit" class="btn btn-secondary btn-sm">Edit</a> '
            f'<form class="inline-form" method="POST" action="/templates/{tname}/delete"'
            f" onsubmit=\"return confirm('Delete template {tname}?')\">"
            f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
            f"</form>"
            f"</td></tr>"
        )
    rows = "".join(rows_list)
    table = _html(
        f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Name</th><th>Image</th><th style="width:180px"></th></tr></thead>
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
    return _page(ctx, "Templates", body)


def template_form(ctx, template=None, error=None):
    is_new = template is None
    title = "New Template" if is_new else f'Edit: {template["name"]}'
    bc = _breadcrumb(("Dashboard", "/"), ("Templates", "/templates"), (title, None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    name_val = esc(template["name"]) if template else ""
    name_input = (
        (
            f'<input type="text" id="name" name="name" value="{name_val}" required'
            f' pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="my-template">'
        )
        if is_new
        else (
            f'<input type="text" id="name" value="{name_val}" readonly'
            f' style="background:#f6f8fa;cursor:not-allowed">'
            f'<input type="hidden" name="name" value="{name_val}">'
        )
    )
    desc_val = esc(template.get("description", "")) if template else ""
    image_val = esc(template.get("image", "")) if template else ""
    script_val = esc(template.get("script", "")) if template else ""
    env_vars_json = json_str(template.get("env_vars", []) if template else [])
    action = "/templates/new" if is_new else f'/templates/{esc(template["name"])}/edit'
    submit_label = "Create Template" if is_new else "Save Changes"
    delete_btn = (
        f'<button type="submit" class="btn btn-danger" formmethod="POST"'
        f' formaction="/templates/{esc(template["name"])}/delete" formnovalidate'
        f" onclick=\"return confirm('Delete template {esc(template['name'])}?')\">Delete Template</button>"
        if not is_new
        else ""
    )
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
              <label for="template-desc">Description <span class="hint">(optional)</span></label>
              <input type="text" id="template-desc" name="description" value="{desc_val}" placeholder="What does this template do?">
            </div>
            <div class="form-group">
              <label for="template-image">Docker image</label>
              <input type="text" id="template-image" name="image" value="{image_val}" placeholder="alpine:latest">
            </div>
            <div class="form-group">
              <label>Expected environment variables <span class="hint">(documentation shown to users; not enforced)</span></label>
              <div class="envvars-editor" id="env-vars-editor">
                <div class="envvars-header"><span>Name</span><span>Description</span><span></span></div>
                <div class="envvars-add"><button type="button" id="add-env-var-btn" class="btn btn-secondary btn-sm">+ Add Variable</button></div>
              </div>
              <input type="hidden" id="env-vars-json" name="env_vars_json" value="{esc(env_vars_json)}">
              <div class="form-section-hint">Document the variables this script expects (e.g. <code>ARTIFACTORY_API_KEY</code> should hold your API key value or a path to a file containing it). Users satisfy them with parameters, credentials or an environment script.</div>
            </div>
            <div class="form-group">
              <label for="template-script">Script</label>
              <textarea id="template-script" name="script" class="code" rows="10" spellcheck="false" placeholder="#!/bin/sh&#10;set -eu&#10;echo Hello">{script_val}</textarea>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">{submit_label}</button>
              {delete_btn}
              <a href="/templates" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(
        ctx,
        title,
        body,
        extra_js=f"<script>{_TEMPLATE_ENV_EDITOR_JS}</script>",
    )
