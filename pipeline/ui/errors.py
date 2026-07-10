from .layout import *  # noqa: F401,F403


def error_404(ctx):
    body = _html(
        """
        <div class="empty-state">
          <h1 style="font-size:48px;color:#d0d7de">404</h1>
          <p>Page not found. <a href="/">Go to Dashboard</a>.</p>
        </div>
        """
    )
    return _page(ctx, "Not Found", body)


def error_403(ctx):
    body = _html(
        """
          <div class="empty-state">
            <h1 style="font-size:48px;color:#d0d7de">403</h1>
            <p>You do not have permission to access this page.</p>
          </div>
          """
    )
    return _page(ctx, "Forbidden", body)


def error_500(ctx, message):
    body = _html(
        f"""
        <div class="page-header"><h1>Server Error</h1></div>
        <div class="alert alert-danger"><pre style="white-space:pre-wrap">{esc(str(message))}</pre></div>
        <p><a href="/">Go to Dashboard</a></p>
        """
    )
    return _page(ctx, "Error", body)
