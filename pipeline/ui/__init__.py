"""HTML rendering for the Pipeline web UI.

The templates are split across submodules; this package re-exports the public
page builders used by the server.
"""

from .layout import esc, queue_paused_banner, PageContext
from .errors import error_403, error_404, error_500
from .auth import login_page, setup_page
from .jobs import (
    dashboard,
    job_detail,
    job_form,
    workspace,
)
from .builds import build_detail, build_form
from .credentials import credentials_form, credentials_list
from .templates import template_form, templates_list
from .users import (
    user_edit_form,
    user_new_form,
    user_password_form,
    users_list,
)
from .settings import settings
