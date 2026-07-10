from .layout import *  # noqa: F401,F403


def login_page(error=None):
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = f"""
<div style="max-width:360px;margin:80px auto">
  <div class="form-card">
    <h1 style="font-size:20px;font-weight:600;margin-bottom:20px">Sign in to Pipeline</h1>
    {error_html}
    <form method="POST" action="/login">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" autocomplete="username" autofocus required>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" autocomplete="current-password" required>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Sign in</button>
      </div>
    </form>
  </div>
</div>
"""
    return _page_bare("Sign in \u2014 Pipeline", body)


def setup_page(error=None):
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = f"""
<div style="max-width:400px;margin:80px auto">
  <div class="form-card">
    <h1 style="font-size:20px;font-weight:600;margin-bottom:6px">Create administrator account</h1>
    <p class="text-muted" style="margin-bottom:20px;font-size:13px">No users exist yet. Create the first account to get started.</p>
    {error_html}
    <form method="POST" action="/setup">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" autocomplete="username" autofocus required pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="administrator">
      </div>
      <div class="form-group">
        <label for="password">Password <span class="hint">(min 8 characters)</span></label>
        <input type="password" id="password" name="password" autocomplete="new-password" required minlength="8">
      </div>
      <div class="form-group">
        <label for="confirm">Confirm password</label>
        <input type="password" id="confirm" name="confirm" autocomplete="new-password" required>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Create account</button>
      </div>
    </form>
  </div>
</div>
"""
    return _page_bare("Setup \u2014 Pipeline", body)
