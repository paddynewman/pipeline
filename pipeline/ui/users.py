from .layout import *  # noqa: F401,F403


def users_list(ctx, users, current_user, error=None):
    bc = _breadcrumb(("Dashboard", "/"), ("Users", None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    header = _html(
        """
        <div class="page-header">
          <h1>Users</h1>
          <div class="actions">
            <a href="/settings/users/new" class="btn btn-primary">+ New User</a>
          </div>
        </div>
        """
    )
    rows = []
    for user in users:
        if isinstance(user, dict):
            uname = user.get("username", "")
            role_name = user.get("role", "")
            is_disabled = bool(user.get("disabled", False))
        else:
            uname = user
            role_name = ""
            is_disabled = False
        uesc = esc(uname)
        role_name = role_name if role_name in ("admin", "user", "viewer") else "user"
        role_html = esc(role_name.capitalize())
        if is_disabled:
            role_html += ' <span class="badge badge-aborted" style="font-size:10px;vertical-align:middle">Disabled</span>'
        is_self = uname == current_user
        self_badge = (
            ' <span class="label-chip" style="font-size:11px;vertical-align:middle">you</span>'
            if is_self
            else ""
        )
        actions = f'<a href="/settings/users/{uesc}/edit" class="btn btn-secondary btn-sm">Edit User</a> '
        if not is_self:
            actions += (
                f'<form class="inline-form" method="POST" action="/settings/users/{uesc}/delete"'
                f" onsubmit=\"return confirm('Delete user {uesc}?')\">"
                f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
                f"</form>"
            )
        rows.append(
            f"<tr>"
            f"<td><strong>{uesc}</strong>{self_badge}</td>"
            f"<td>{role_html}</td>"
            f'<td style="text-align:right">{actions}</td>'
            f"</tr>"
        )
    table = _html(
        f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Username</th><th>Role</th><th></th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
      """
    )
    empty = '<div class="empty-state"><p>No users.</p></div>'
    body = _html(
        f"""
      {bc}
      {header}
      {error_html}
      {table if rows else empty}
      """
    )
    return _page(ctx, "Users", body)


def user_edit_form(ctx, target_user, user_role="user", disabled=False, error=None):
    bc = _breadcrumb(
        ("Dashboard", "/"),
        ("Users", "/settings/users"),
        (f"Edit user: {target_user}", None),
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    role_value = user_role if user_role in ("admin", "user", "viewer") else "user"
    disabled_attr = " checked" if disabled else ""
    sel_admin = " selected" if role_value == "admin" else ""
    sel_user = " selected" if role_value == "user" else ""
    sel_viewer = " selected" if role_value == "viewer" else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Edit user: {esc(target_user)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/{esc(target_user)}/edit">
            <div class="form-group">
              <label>Username</label>
              <input type="text" value="{esc(target_user)}" readonly style="background:#f6f8fa;cursor:not-allowed">
            </div>
            <div class="form-group">
              <label for="edit-user-role">Role</label>
              <select id="edit-user-role" name="role" required style="max-width:220px">
                <option value="admin"{sel_admin}>Administrator</option>
                <option value="user"{sel_user}>User</option>
                <option value="viewer"{sel_viewer}>Viewer</option>
              </select>
            </div>
            <div class="form-group">
              <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                <input type="checkbox" name="disabled" value="1"{disabled_attr} style="width:auto">
                Disable this user <span class="hint">(prevents login without deleting the account)</span>
              </label>
            </div>
            <div class="form-group">
              <label for="edit-user-password">New password <span class="hint">(optional, leave blank to keep unchanged)</span></label>
              <input type="password" id="edit-user-password" name="password" autocomplete="new-password" minlength="8">
            </div>
            <div class="form-group">
              <label for="edit-user-confirm">Confirm new password</label>
              <input type="password" id="edit-user-confirm" name="confirm" autocomplete="new-password" minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save Changes</button>
              <a href="/settings/users" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(ctx, f"Edit user: {target_user}", body)


def user_new_form(ctx, error=None):
    bc = _breadcrumb(
        ("Dashboard", "/"), ("Users", "/settings/users"), ("New User", None)
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>New User</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/new">
            <div class="form-group">
              <label for="new-username">Username</label>
              <input type="text" id="new-username" name="username" autocomplete="off" autofocus required pattern="[a-zA-Z0-9][a-zA-Z0-9._-]{{0,49}}">
            </div>
            <div class="form-group">
              <label for="new-role">Role</label>
              <select id="new-role" name="role" required>
                <option value="user" selected>User</option>
                <option value="viewer">Viewer</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            <div class="form-group">
              <label for="new-password">Password</label>
              <input type="password" id="new-password" name="password" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-group">
              <label for="new-confirm">Confirm password</label>
              <input type="password" id="new-confirm" name="confirm" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Create User</button>
              <a href="/settings/users" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(ctx, "New User", body)


def user_password_form(ctx, target_user, error=None):
    bc = _breadcrumb(
        ("Dashboard", "/"),
        ("Users", "/settings/users"),
        (f"Change password: {target_user}", None),
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Change password: {esc(target_user)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/{esc(target_user)}/password">
            <div class="form-group">
              <label for="new-password">New password</label>
              <input type="password" id="new-password" name="password" autocomplete="new-password" autofocus required minlength="8">
            </div>
            <div class="form-group">
              <label for="new-confirm">Confirm password</label>
              <input type="password" id="new-confirm" name="confirm" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save</button>
              <a href="/" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(ctx, f"Change password: {target_user}", body)
