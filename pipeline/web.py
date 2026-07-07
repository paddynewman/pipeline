import html as _html
import json
import os
from urllib.parse import quote

import yaml
from bottle import Bottle, redirect, request, response, static_file, template

from . import __version__
from .auth import AuthService
from .config_store import JsonStore
from .kube_client import KubeGateway
from .services import PipelineService


def _parse_label_entries(forms):
    names = forms.getall("label_name")
    values = forms.getall("label_value")
    descriptions = forms.getall("label_description")

    labels = []
    for index, raw_name in enumerate(names):
        name = (raw_name or "").strip()
        value = (values[index] if index < len(values) else "").strip()
        description = (descriptions[index] if index < len(descriptions) else "").strip()
        if not name:
            continue
        labels.append(
            {
                "name": name,
                "value": value,
                "description": description,
            }
        )

    return labels


def _parse_yaml_mapping(value, field_label="YAML mapping"):
    raw = (value or "").strip()
    if not raw:
        return {}, ""

    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"{field_label} is invalid: {exc}"

    if parsed is None:
        return {}, ""
    if not isinstance(parsed, dict):
        return None, f"{field_label} must be a YAML mapping (key/value object)."

    variables = {}
    for key, mapped_value in parsed.items():
        key_name = (str(key) if key is not None else "").strip()
        if not key_name:
            return None, f"{field_label} contains an empty key."
        variables[key_name] = mapped_value

    return variables, ""


def _parse_secret_yaml_mapping(value, field_label="Secrets YAML mapping"):
    parsed, error = _parse_yaml_mapping(value, field_label=field_label)
    if error:
        return None, error

    normalized = {}
    for key, mapped_value in (parsed or {}).items():
        if isinstance(mapped_value, (dict, list)):
            return None, f"{field_label} value for '{key}' must be a scalar value."
        normalized[key] = "" if mapped_value is None else str(mapped_value)

    return normalized, ""


def _parse_secret_entries(forms):
    keys = forms.getall("secret_key")
    values = forms.getall("secret_value")

    entries = {}
    errors = []
    for index, raw_key in enumerate(keys):
        key_name = (raw_key or "").strip()
        value_name = (values[index] if index < len(values) else "")
        if not key_name:
            continue
        if key_name in entries:
            errors.append(f"Duplicate secret key '{key_name}'.")
            continue
        entries[key_name] = "" if value_name is None else str(value_name)

    return entries, errors


def create_app(base_dir=None):
    if not base_dir:
        base_dir = os.getcwd()

    data_dir = os.path.join(base_dir, "data")
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)

    store = JsonStore(data_dir)
    kube = KubeGateway()
    service = PipelineService(store=store, kube=kube, template_dir=template_dir)
    auth = AuthService(store=store)

    cookie_name = "pipeline_user"
    cookie_secret = os.getenv("PIPELINE_COOKIE_SECRET", "pipeline-dev-cookie-secret")
    cookie_secure = os.getenv("PIPELINE_COOKIE_SECURE", "false").lower() == "true"

    app = Bottle()

    def breadcrumbs(*items):
        result = []
        for item in items:
            if len(item) == 1:
                result.append({"label": item[0], "href": ""})
            else:
                result.append({"label": item[0], "href": item[1]})
        return result

    def current_user():
        username = request.get_cookie(cookie_name, secret=cookie_secret)
        if username and auth.user_exists(username):
            return username
        return ""

    def set_login_cookie(username):
        response.set_cookie(
            cookie_name,
            username,
            secret=cookie_secret,
            httponly=True,
            secure=cookie_secure,
            samesite="lax",
            path="/",
        )

    def clear_login_cookie():
        response.delete_cookie(cookie_name, path="/")

    @app.hook("before_request")
    def require_login():
        path = request.path or "/"
        public_paths = ["/login", "/setup", "/health"]
        public_prefixes = ["/static/"]

        if path in public_paths or any(path.startswith(item) for item in public_prefixes):
            return

        if not auth.has_users():
            redirect("/setup")

        if current_user():
            return

        next_path = quote(request.fullpath or "/", safe="/?=&")
        redirect(f"/login?next={next_path}")

    def render_view(name, **context):
        return template(
            name,
            template_lookup=[template_dir],
            json_dumps=lambda value, indent=2: json.dumps(value, indent=indent, sort_keys=True),
            current_user=current_user(),
            app_version=__version__,
            **context,
        )

    def normalized_template_entries(config_item):
        entries = []
        for item in config_item.get("templates", []):
            if isinstance(item, dict):
                content = (item.get("content") or item.get("template") or "").strip()
                if not content:
                    continue
                entries.append({"content": content})
            else:
                content = (item or "").strip()
                if not content:
                    continue
                entries.append({"content": content})

        if not entries:
            legacy_template = (config_item.get("template") or "").strip()
            if legacy_template:
                entries.append({"content": legacy_template})

        if not entries:
            entries = [{"content": ""}]

        return entries

    def parse_environment_form():
        env_item = {
            "name": request.forms.get("name", "").strip(),
            "description": request.forms.get("description", "").strip(),
            "namespace": request.forms.get("namespace", "").strip(),
            "variable_overrides": {},
            "secret_overrides": {},
            "secret_set_overrides": {},
            "labels": _parse_label_entries(request.forms),
        }

        errors = []
        if not env_item["name"]:
            errors.append("Environment name is required.")
        if not env_item["namespace"]:
            errors.append("Namespace is required.")

        return env_item, errors

    @app.get("/login")
    def login_page():
        if not auth.has_users():
            redirect("/setup")
        if current_user():
            redirect("/")

        return render_view(
            "login",
            error="",
            next_path=request.query.get("next", "/"),
            breadcrumbs=[],
        )

    @app.post("/login")
    def login_submit():
        if not auth.has_users():
            redirect("/setup")

        username = request.forms.get("username", "").strip()
        password = request.forms.get("password", "")
        next_path = request.forms.get("next", "/")

        if auth.verify(username=username, password=password):
            set_login_cookie(username)
            if not next_path.startswith("/"):
                next_path = "/"
            redirect(next_path)

        return render_view(
            "login",
            error="Invalid username or password.",
            next_path=next_path,
            breadcrumbs=[],
        )

    @app.post("/logout")
    def logout():
        clear_login_cookie()
        redirect("/login")

    @app.get("/logout")
    def logout_via_get():
        clear_login_cookie()
        redirect("/login")

    @app.get("/setup")
    def setup_page():
        if auth.has_users():
            redirect("/login")

        return render_view("setup", error="", breadcrumbs=[])

    @app.post("/setup")
    def setup_submit():
        if auth.has_users():
            redirect("/login")

        username = request.forms.get("username", "").strip()
        password = request.forms.get("password", "")
        confirm_password = request.forms.get("confirm_password", "")

        if not username:
            return render_view("setup", error="Username is required.", breadcrumbs=[])
        if not password:
            return render_view("setup", error="Password is required.", breadcrumbs=[])
        if password != confirm_password:
            return render_view("setup", error="Passwords do not match.", breadcrumbs=[])

        try:
            auth.create_user(username=username, password=password)
        except ValueError as exc:
            return render_view("setup", error=str(exc), breadcrumbs=[])

        set_login_cookie(username)
        redirect("/")

    @app.get("/static/<filename:path>")
    def static_assets(filename):
        return static_file(filename, root=static_dir)

    @app.get("/")
    def dashboard():
        connected, cluster_state = kube.reachable()
        return render_view(
            "dashboard",
            dashboard_items=service.dashboard_items(),
            cluster_connected=connected,
            cluster_state=cluster_state,
            breadcrumbs=breadcrumbs(("Dashboard", "")),
        )

    @app.get("/applications/new")
    def new_application():
        return render_view(
            "application_form",
            app_item=None,
            required_application_labels=service.required_labels_for_scope("application"),
            errors=[],
            message="",
            submit_path="/applications/new",
            cancel_path="/",
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("New Application", "")),
        )

    @app.post("/applications/new")
    def create_application():
        app_item = {
            "name": request.forms.get("name", "").strip(),
            "description": request.forms.get("description", "").strip(),
            "application_type": "kubernetes",
            "labels": _parse_label_entries(request.forms),
            "templates": [],
            "variables": {},
            "secrets": {},
            "secret_sets": {},
            "environments": [],
            "namespaces": [],
        }

        errors = []
        if not app_item["name"]:
            errors.append("Application name is required.")
        errors.extend(service.validation_errors(app_item))

        if errors:
            return render_view(
                "application_form",
                app_item=app_item,
                required_application_labels=service.required_labels_for_scope("application"),
                errors=errors,
                message="",
                submit_path="/applications/new",
                cancel_path="/",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), ("New Application", "")),
            )

        service.save_app(app_item)
        redirect(f"/applications/{app_item['name']}")

    @app.get("/applications/<app_name>")
    def application_detail(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespaces = service.namespaces(app_item)
        environments = service.environments(app_item)
        app_missing_required_labels = service.missing_required_application_labels(app_item)
        namespace_missing_required_labels = {}
        for namespace_item in namespaces:
            namespace_missing_required_labels[namespace_item.get("name", "")] = service.missing_required_namespace_labels(
                namespace_item
            )

        namespace_lookup = {}
        for namespace_item in namespaces:
            namespace_name = namespace_item.get("name", "")
            namespace_lookup[namespace_name] = namespace_item

        environment_health = {}
        app_runtime_name = app_item.get("name", "")
        for env in environments:
            env_name = env.get("name", "")
            namespace_name = (env.get("namespace") or "").strip()

            if not namespace_name:
                environment_health[env_name] = {"healthy": False, "detail": "Namespace is not set."}
                continue

            namespace_item = namespace_lookup.get(namespace_name)
            if not namespace_item:
                environment_health[env_name] = {
                    "healthy": False,
                    "detail": f"Namespace '{namespace_name}' is not configured.",
                }
                continue

            kubeconfig_text = namespace_item.get("kubeconfig", "")
            try:
                runtime_data = kube.application_runtime(
                    namespace_name,
                    app_runtime_name,
                    kubeconfig_text=kubeconfig_text,
                )

                not_ready = 0
                workload_count = 0

                for item in runtime_data.get("deployments", []):
                    spec = item.get("spec", {}) or {}
                    status = item.get("status", {}) or {}
                    desired = spec.get("replicas") or 0
                    ready = status.get("ready_replicas") or 0
                    workload_count += 1
                    if ready < desired:
                        not_ready += 1

                for item in runtime_data.get("stateful_sets", []):
                    spec = item.get("spec", {}) or {}
                    status = item.get("status", {}) or {}
                    desired = spec.get("replicas") or 0
                    ready = status.get("ready_replicas") or 0
                    workload_count += 1
                    if ready < desired:
                        not_ready += 1

                if workload_count == 0:
                    environment_health[env_name] = {
                        "healthy": True,
                        "detail": "No workloads found for this environment yet.",
                    }
                elif not_ready == 0:
                    environment_health[env_name] = {
                        "healthy": True,
                        "detail": "All workloads are ready.",
                    }
                else:
                    environment_health[env_name] = {
                        "healthy": False,
                        "detail": f"{not_ready} of {workload_count} workloads are not ready.",
                    }
            except Exception as exc:
                environment_health[env_name] = {
                    "healthy": False,
                    "detail": str(exc),
                }

        return render_view(
            "application_detail",
            app_item=app_item,
            namespaces=namespaces,
            environments=environments,
            app_missing_required_labels=app_missing_required_labels,
            namespace_missing_required_labels=namespace_missing_required_labels,
            environment_health=environment_health,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, "")),
        )

    @app.post("/applications/<app_name>/operations/scale")
    def scale_workload_for_application(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace = request.forms.get("namespace", "").strip()
        kind = request.forms.get("kind", "").strip()
        name = request.forms.get("name", "").strip()

        try:
            replicas = int(request.forms.get("replicas", "1"))
        except ValueError:
            replicas = 1

        namespace_item = service.namespace_config(app_item, namespace)
        if not namespace_item:
            redirect(
                f"/applications/{app_name}?namespace={namespace}&"
                "message=Scale+failed%3A+namespace+is+not+configured"
            )

        kubeconfig_text = namespace_item.get("kubeconfig", "")
        try:
            kube.scale_workload(
                namespace=namespace,
                kind=kind,
                name=name,
                replicas=replicas,
                kubeconfig_text=kubeconfig_text,
            )
            msg = f"Scaled {kind}/{name} to {replicas} replicas"
        except Exception as exc:
            msg = f"Scale failed: {exc}"

        redirect(f"/applications/{app_name}?namespace={namespace}&message={quote(msg, safe='')}")

    @app.get("/applications/<app_name>/edit")
    def edit_application(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found")

        return render_view(
            "application_form",
            app_item=app_item,
            required_application_labels=service.required_labels_for_scope("application"),
            errors=[],
            message="",
            submit_path=f"/applications/{app_name}/edit",
            cancel_path=f"/applications/{app_name}",
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit", "")),
        )

    @app.post("/applications/<app_name>/edit")
    def update_application(app_name):
        existing = service.get_app(app_name)
        if not existing:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        updated = {
            "name": request.forms.get("name", "").strip(),
            "description": request.forms.get("description", "").strip(),
            "application_type": "kubernetes",
            "labels": _parse_label_entries(request.forms),
            "templates": existing.get("templates", []),
            "template": existing.get("template", ""),
            "template_files": existing.get("template_files", []),
            "variables": existing.get("variables", {}),
            "secrets": existing.get("secrets", {}),
            "secret_sets": existing.get("secret_sets", {}),
            "environments": existing.get("environments", []),
            "namespaces": existing.get("namespaces", []),
        }

        errors = []
        if not updated["name"]:
            errors.append("Application name is required.")
        for required in service.missing_required_application_labels(updated):
            key = required.get("name")
            errors.append(f"Missing required application label '{key}': {required.get('description', '')}")

        if errors:
            return render_view(
                "application_form",
                app_item=updated,
                required_application_labels=service.required_labels_for_scope("application"),
                errors=errors,
                message="",
                submit_path=f"/applications/{app_name}/edit",
                cancel_path=f"/applications/{app_name}",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit", "")),
            )

        if updated["name"] != app_name:
            service.delete_app(app_name)
        service.save_app(updated)
        redirect(f"/applications/{updated['name']}")

    @app.get("/applications/<app_name>/configure")
    def configure_application(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        template_entries = normalized_template_entries(app_item)
        app_variables = service.app_variable_defaults(app_item) or {}
        variables_yaml = yaml.safe_dump(app_variables, sort_keys=True).strip() if app_variables else ""

        return render_view(
            "application_configure",
            app_item=app_item,
            errors=[],
            template_entries=template_entries,
            variables_yaml=variables_yaml,
            rendered_templates=[],
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                ("Configure Application", ""),
            ),
        )

    @app.post("/applications/<app_name>/configure")
    def update_application_configuration(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        template_texts = request.forms.getall("template_text")

        template_entries = []
        row_count = len(template_texts)
        for index in range(row_count):
            content = (template_texts[index] if index < len(template_texts) else "").strip()
            if not content:
                continue
            template_entries.append({"content": content})

        variables_yaml = request.forms.get("variables_yaml", "")
        action = request.forms.get("action", "save")

        variables, variables_error = _parse_yaml_mapping(variables_yaml, field_label="Template variable defaults YAML")

        errors = []
        if variables_error:
            errors.append(variables_error)
        if not template_entries:
            errors.append("At least one template is required.")

        config_preview = dict(app_item)
        config_preview["templates"] = template_entries
        config_preview["variables"] = variables or {}

        rendered_templates = []
        if action == "render" and not errors:
            preview_env = {
                "name": "preview",
                "namespace": "preview",
                "variable_overrides": {},
            }
            context_info = service.resolve_environment_context(config_preview, preview_env)
            render_context = context_info.get("context", {})
            for index, item in enumerate(template_entries):
                try:
                    rendered_templates.append(
                        {
                            "index": index + 1,
                            "content": template(item.get("content", ""), **render_context),
                        }
                    )
                except Exception as exc:
                    errors.append(f"Template {index + 1} render failed: {exc}")

        if errors or action == "render":
            return render_view(
                "application_configure",
                app_item=config_preview,
                errors=errors,
                template_entries=template_entries if template_entries else [{"content": ""}],
                variables_yaml=variables_yaml,
                rendered_templates=rendered_templates,
                breadcrumbs=breadcrumbs(
                    ("Dashboard", "/"),
                    (app_name, f"/applications/{app_name}"),
                    ("Configure Application", ""),
                ),
            )

        updated = dict(app_item)
        updated["templates"] = template_entries
        updated["template"] = ""
        updated["template_files"] = updated.get("template_files", [])
        updated["variables"] = variables or {}
        updated["secrets"] = app_item.get("secrets", {})
        updated["secret_sets"] = app_item.get("secret_sets", {})

        service.save_app(updated)
        redirect(f"/applications/{app_name}")

    @app.post("/applications/<app_name>/delete")
    def delete_application(app_name):
        service.delete_app(app_name)
        redirect("/")

    @app.get("/applications/<app_name>/namespaces/new")
    def new_namespace(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        return render_view(
            "namespace_form",
            app_item=app_item,
            namespace_item={"name": "", "description": "", "labels": [], "kubeconfig": ""},
            errors=[],
            required_namespace_labels=service.required_labels_for_scope("namespace"),
            page_title="Add Namespace",
            submit_label="Add Namespace",
            submit_path=f"/applications/{app_name}/namespaces/new",
            test_message="",
            test_error="",
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Namespace", "")),
        )

    @app.post("/applications/<app_name>/namespaces/new")
    def create_namespace(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace_item = {
            "name": request.forms.get("name", "").strip(),
            "description": request.forms.get("description", "").strip(),
            "labels": _parse_label_entries(request.forms),
            "kubeconfig": request.forms.get("kubeconfig", ""),
        }

        errors = []
        if not namespace_item["name"]:
            errors.append("Namespace name is required.")
        if not namespace_item["kubeconfig"].strip():
            errors.append("Kubeconfig is required.")

        action = request.forms.get("action", "save")
        if action == "test":
            if errors:
                return render_view(
                    "namespace_form",
                    app_item=app_item,
                    namespace_item=namespace_item,
                    errors=errors,
                    required_namespace_labels=service.required_labels_for_scope("namespace"),
                    page_title="Add Namespace",
                    submit_label="Add Namespace",
                    submit_path=f"/applications/{app_name}/namespaces/new",
                    test_message="",
                    test_error="",
                    breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Namespace", "")),
                )

            healthy, detail = kube.check_namespace_access(
                namespace=namespace_item["name"],
                kubeconfig_text=namespace_item["kubeconfig"],
            )
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=[],
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Add Namespace",
                submit_label="Add Namespace",
                submit_path=f"/applications/{app_name}/namespaces/new",
                test_message=detail if healthy else "",
                test_error="" if healthy else detail,
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Namespace", "")),
            )

        if errors:
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=errors,
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Add Namespace",
                submit_label="Add Namespace",
                submit_path=f"/applications/{app_name}/namespaces/new",
                test_message="",
                test_error="",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Namespace", "")),
            )

        try:
            service.add_namespace(app_name, namespace_item)
        except ValueError as exc:
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=[str(exc)],
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Add Namespace",
                submit_label="Add Namespace",
                submit_path=f"/applications/{app_name}/namespaces/new",
                test_message="",
                test_error="",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Namespace", "")),
            )

        redirect(f"/applications/{app_name}")

    @app.get("/applications/<app_name>/namespaces/<namespace_name>/edit")
    def edit_namespace(app_name, namespace_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            response.status = 404
            return render_view(
                "error",
                message="Namespace not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        missing_required_namespace_labels = service.missing_required_namespace_labels(namespace_item)

        return render_view(
            "namespace_form",
            app_item=app_item,
            namespace_item=namespace_item,
            errors=[],
            required_namespace_labels=service.required_labels_for_scope("namespace"),
            page_title="Edit Namespace",
            submit_label="Save Namespace",
            submit_path=f"/applications/{app_name}/namespaces/{namespace_name}/edit",
            test_message="",
            test_error="",
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Namespace", "")),
        )

    @app.post("/applications/<app_name>/namespaces/<namespace_name>/edit")
    def update_namespace(app_name, namespace_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace_item = {
            "name": request.forms.get("name", "").strip(),
            "description": request.forms.get("description", "").strip(),
            "labels": _parse_label_entries(request.forms),
            "kubeconfig": request.forms.get("kubeconfig", ""),
        }

        errors = []
        if not namespace_item["name"]:
            errors.append("Namespace name is required.")
        if not namespace_item["kubeconfig"].strip():
            errors.append("Kubeconfig is required.")

        action = request.forms.get("action", "save")
        if action == "test":
            if errors:
                return render_view(
                    "namespace_form",
                    app_item=app_item,
                    namespace_item=namespace_item,
                    errors=errors,
                    required_namespace_labels=service.required_labels_for_scope("namespace"),
                    page_title="Edit Namespace",
                    submit_label="Save Namespace",
                    submit_path=f"/applications/{app_name}/namespaces/{namespace_name}/edit",
                    test_message="",
                    test_error="",
                    breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Namespace", "")),
                )

            healthy, detail = kube.check_namespace_access(
                namespace=namespace_item["name"],
                kubeconfig_text=namespace_item["kubeconfig"],
            )
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=[],
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Edit Namespace",
                submit_label="Save Namespace",
                submit_path=f"/applications/{app_name}/namespaces/{namespace_name}/edit",
                test_message=detail if healthy else "",
                test_error="" if healthy else detail,
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Namespace", "")),
            )

        if errors:
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=errors,
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Edit Namespace",
                submit_label="Save Namespace",
                submit_path=f"/applications/{app_name}/namespaces/{namespace_name}/edit",
                test_message="",
                test_error="",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Namespace", "")),
            )

        try:
            service.update_namespace(app_name, namespace_name, namespace_item)
        except ValueError as exc:
            return render_view(
                "namespace_form",
                app_item=app_item,
                namespace_item=namespace_item,
                errors=[str(exc)],
                required_namespace_labels=service.required_labels_for_scope("namespace"),
                page_title="Edit Namespace",
                submit_label="Save Namespace",
                submit_path=f"/applications/{app_name}/namespaces/{namespace_name}/edit",
                test_message="",
                test_error="",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Namespace", "")),
            )

        redirect(f"/applications/{app_name}")

    @app.post("/applications/<app_name>/namespaces/<namespace_name>/delete")
    def delete_namespace(app_name, namespace_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        try:
            service.delete_namespace(app_name, namespace_name)
        except ValueError as exc:
            return render_view(
                "error",
                message=str(exc),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        redirect(f"/applications/{app_name}")

    @app.get("/applications/<app_name>/environments/new")
    def new_environment(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespaces = service.namespaces(app_item)
        default_namespace = namespaces[0].get("name", "") if namespaces else ""
        env_item = {
            "name": "",
            "description": "",
            "namespace": default_namespace,
            "variable_overrides": {},
            "labels": [],
        }

        return render_view(
            "environment_form",
            app_item=app_item,
            env_item=env_item,
            is_edit=False,
            errors=[],
            page_title="Add Environment",
            submit_label="Add Environment",
            submit_path=f"/applications/{app_name}/environments/new",
            namespaces=namespaces,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Environment", "")),
        )

    @app.post("/applications/<app_name>/environments/new")
    def create_environment(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item, errors = parse_environment_form()

        if not service.namespaces(app_item):
            errors.append("Add at least one namespace before creating an environment.")

        if errors:
            return render_view(
                "environment_form",
                app_item=app_item,
                env_item=env_item,
                is_edit=False,
                errors=errors,
                page_title="Add Environment",
                submit_label="Add Environment",
                submit_path=f"/applications/{app_name}/environments/new",
                namespaces=service.namespaces(app_item),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Environment", "")),
            )

        try:
            service.add_environment(app_name, env_item)
        except ValueError as exc:
            return render_view(
                "environment_form",
                app_item=app_item,
                env_item=env_item,
                is_edit=False,
                errors=[str(exc)],
                page_title="Add Environment",
                submit_label="Add Environment",
                submit_path=f"/applications/{app_name}/environments/new",
                namespaces=service.namespaces(app_item),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Add Environment", "")),
            )

        redirect(f"/applications/{app_name}")

    @app.get("/applications/<app_name>/environments/<env_name>/edit")
    def edit_environment(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        return render_view(
            "environment_form",
            app_item=app_item,
            env_item=env_item,
            is_edit=True,
            errors=[],
            page_title="Edit Environment",
            submit_label="Save Environment",
            submit_path=f"/applications/{app_name}/environments/{env_name}/edit",
            namespaces=service.namespaces(app_item),
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Environment", "")),
        )

    @app.post("/applications/<app_name>/environments/<env_name>/edit")
    def update_environment(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item, errors = parse_environment_form()

        existing_env = service.environment(app_item, env_name) or {}
        env_item["variable_overrides"] = existing_env.get("variable_overrides", {})
        env_item["secret_overrides"] = existing_env.get("secret_overrides", existing_env.get("secrets", {}))
        env_item["secret_set_overrides"] = existing_env.get("secret_set_overrides", {})
        env_item["templates"] = existing_env.get("templates", [])
        env_item["template"] = existing_env.get("template", "")
        env_item["template_files"] = existing_env.get("template_files", [])
        env_item["variables"] = existing_env.get("variables", {})
        env_item["release"] = existing_env.get("release", 0)

        if errors:
            return render_view(
                "environment_form",
                app_item=app_item,
                env_item=env_item,
                is_edit=True,
                errors=errors,
                page_title="Edit Environment",
                submit_label="Save Environment",
                submit_path=f"/applications/{app_name}/environments/{env_name}/edit",
                namespaces=service.namespaces(app_item),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Environment", "")),
            )

        try:
            service.update_environment(app_name, env_name, env_item)
        except ValueError as exc:
            return render_view(
                "environment_form",
                app_item=app_item,
                env_item=env_item,
                is_edit=True,
                errors=[str(exc)],
                page_title="Edit Environment",
                submit_label="Save Environment",
                submit_path=f"/applications/{app_name}/environments/{env_name}/edit",
                namespaces=service.namespaces(app_item),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Edit Environment", "")),
            )

        redirect(f"/applications/{app_name}")

    @app.post("/applications/<app_name>/environments/<env_name>/delete")
    def delete_environment(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        try:
            service.delete_environment(app_name, env_name)
        except ValueError as exc:
            return render_view(
                "error",
                message=str(exc),
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        redirect(f"/applications/{app_name}")

    @app.get("/applications/<app_name>/environments/<env_name>/configure")
    def configure_environment(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        env_overrides = service.environment_variable_overrides(env_item) or {}
        variable_overrides_yaml = yaml.safe_dump(env_overrides, sort_keys=True).strip() if env_overrides else ""

        return render_view(
            "environment_configure",
            app_item=app_item,
            env_item=env_item,
            errors=[],
            variable_overrides_yaml=variable_overrides_yaml,
            rendered_templates=[],
            app_template_count=len(service.templates_for_environment(app_item, env_item)),
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                (f"Environment Overrides: {env_name}", ""),
            ),
        )

    @app.post("/applications/<app_name>/environments/<env_name>/configure")
    def update_environment_configuration(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        existing_env = service.environment(app_item, env_name)
        if not existing_env:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        variable_overrides_yaml = request.forms.get("variable_overrides_yaml", "")
        action = request.forms.get("action", "save")
        variable_overrides, variable_overrides_error = _parse_yaml_mapping(
            variable_overrides_yaml,
            field_label="Variable overrides YAML",
        )

        errors = []
        if variable_overrides_error:
            errors.append(variable_overrides_error)

        env_for_page = dict(existing_env)
        env_for_page["variable_overrides"] = variable_overrides or {}

        rendered_templates = []
        if action == "render" and not errors:
            context_info = service.resolve_environment_context(app_item, env_for_page)
            templates_for_render = service.templates_for_environment(app_item, env_for_page)
            render_context = context_info.get("context", {})
            for index, template_item in enumerate(templates_for_render):
                try:
                    rendered_templates.append(
                        {
                            "index": index + 1,
                            "name": template_item.get("name", ""),
                            "content": template(template_item.get("content", ""), **render_context),
                        }
                    )
                except Exception as exc:
                    errors.append(f"Template {index + 1} render failed: {exc}")

        if errors or action == "render":
            return render_view(
                "environment_configure",
                app_item=app_item,
                env_item=env_for_page,
                errors=errors,
                variable_overrides_yaml=variable_overrides_yaml,
                rendered_templates=rendered_templates,
                app_template_count=len(service.templates_for_environment(app_item, env_for_page)),
                breadcrumbs=breadcrumbs(
                    ("Dashboard", "/"),
                    (app_name, f"/applications/{app_name}"),
                    (f"Environment Overrides: {env_name}", ""),
                ),
            )

        env_item = dict(existing_env)
        env_item["variable_overrides"] = variable_overrides or {}
        env_item["secret_set_overrides"] = existing_env.get("secret_set_overrides", {})
        env_item["secret_overrides"] = existing_env.get("secret_overrides", existing_env.get("secrets", {}))

        try:
            service.update_environment(app_name, env_name, env_item)
        except ValueError as exc:
            return render_view(
                "environment_configure",
                app_item=app_item,
                env_item=env_item,
                errors=[str(exc)],
                variable_overrides_yaml=variable_overrides_yaml,
                rendered_templates=[],
                app_template_count=len(service.templates_for_environment(app_item, env_item)),
                breadcrumbs=breadcrumbs(
                    ("Dashboard", "/"),
                    (app_name, f"/applications/{app_name}"),
                    (f"Environment Overrides: {env_name}", ""),
                ),
            )

        redirect(f"/applications/{app_name}")

    @app.get("/applications/<app_name>/secrets")
    def application_secrets(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        message = request.query.get("message", "")
        error = request.query.get("error", "")
        secret_sets = service.app_secret_sets(app_item)
        return render_view(
            "application_secrets",
            app_item=app_item,
            secret_sets=secret_sets,
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Secrets", "")),
        )

    @app.post("/applications/<app_name>/secrets/add")
    def application_secret_add(app_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        secret_name = service.validate_secret_set_name(request.forms.get("secret_name", ""))
        if not secret_name:
            redirect(f"/applications/{app_name}/secrets?error=Secret+name+must+match+kubernetes+naming+rules")

        entries, entry_errors = _parse_secret_entries(request.forms)
        if entry_errors:
            redirect(f"/applications/{app_name}/secrets?error={quote(entry_errors[0], safe='')}")
        if not entries:
            redirect(f"/applications/{app_name}/secrets?error=At+least+one+secret+entry+is+required")

        secret_sets = service.app_secret_sets(app_item)
        if secret_name in secret_sets:
            redirect(f"/applications/{app_name}/secrets?error=Secret+name+already+exists")

        secret_sets[secret_name] = entries
        app_item["secret_sets"] = secret_sets
        app_item["secrets"] = {}
        service.save_app(app_item)
        redirect(f"/applications/{app_name}/secrets?message=Secret+added")

    @app.get("/applications/<app_name>/secrets/<secret_name>/edit")
    def application_secret_edit(app_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        normalized_name = service.validate_secret_set_name(secret_name)
        secret_sets = service.app_secret_sets(app_item)
        entries = secret_sets.get(normalized_name)
        if not normalized_name or entries is None:
            response.status = 404
            return render_view("error", message="Secret not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        message = request.query.get("message", "")
        error = request.query.get("error", "")
        return render_view(
            "secret_edit",
            app_item=app_item,
            env_item=None,
            scope_label="Application Secret",
            post_path=f"/applications/{app_name}/secrets/{normalized_name}/edit",
            cancel_path=f"/applications/{app_name}/secrets",
            secret_name=normalized_name,
            entries=entries,
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                ("Secrets", f"/applications/{app_name}/secrets"),
                (f"Edit: {normalized_name}", ""),
            ),
        )

    @app.post("/applications/<app_name>/secrets/<secret_name>/edit")
    def application_secret_update(app_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        current_name = service.validate_secret_set_name(secret_name)
        updated_name = service.validate_secret_set_name(request.forms.get("secret_name", ""))
        if not current_name or not updated_name:
            redirect(f"/applications/{app_name}/secrets/{secret_name}/edit?error=Secret+name+must+match+kubernetes+naming+rules")

        entries, entry_errors = _parse_secret_entries(request.forms)
        if entry_errors:
            redirect(f"/applications/{app_name}/secrets/{current_name}/edit?error={quote(entry_errors[0], safe='')}")
        if not entries:
            redirect(f"/applications/{app_name}/secrets/{current_name}/edit?error=At+least+one+secret+entry+is+required")

        secret_sets = service.app_secret_sets(app_item)
        if current_name not in secret_sets:
            redirect(f"/applications/{app_name}/secrets?error=Secret+not+found")
        if updated_name != current_name and updated_name in secret_sets:
            redirect(f"/applications/{app_name}/secrets/{current_name}/edit?error=Secret+name+already+exists")

        del secret_sets[current_name]
        secret_sets[updated_name] = entries
        app_item["secret_sets"] = secret_sets
        app_item["secrets"] = {}
        service.save_app(app_item)
        redirect(f"/applications/{app_name}/secrets/{updated_name}/edit?message=Secret+updated")

    @app.post("/applications/<app_name>/secrets/<secret_name>/delete")
    def application_secret_delete(app_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        normalized_name = service.validate_secret_set_name(secret_name)
        secret_sets = service.app_secret_sets(app_item)
        if normalized_name in secret_sets:
            del secret_sets[normalized_name]
            app_item["secret_sets"] = secret_sets
            app_item["secrets"] = {}
            service.save_app(app_item)
        redirect(f"/applications/{app_name}/secrets")

    @app.get("/applications/<app_name>/environments/<env_name>/secrets")
    def environment_secrets(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view("error", message="Environment not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        message = request.query.get("message", "")
        error = request.query.get("error", "")
        override_sets = service.environment_secret_set_overrides(env_item)
        secret_resource_names = {}
        for set_name in override_sets.keys():
            secret_resource_names[set_name] = service.secret_name_for_environment(app_item, env_item, set_name)
        return render_view(
            "environment_secrets",
            app_item=app_item,
            env_item=env_item,
            override_sets=override_sets,
            secret_resource_names=secret_resource_names,
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                (f"Secrets: {env_name}", ""),
            ),
        )

    @app.post("/applications/<app_name>/environments/<env_name>/secrets/add")
    def environment_secret_add(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view("error", message="Environment not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        secret_name = service.validate_secret_set_name(request.forms.get("secret_name", ""))
        if not secret_name:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets?error=Secret+name+must+match+kubernetes+naming+rules")

        entries, entry_errors = _parse_secret_entries(request.forms)
        if entry_errors:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets?error={quote(entry_errors[0], safe='')}")
        if not entries:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets?error=At+least+one+secret+entry+is+required")

        override_sets = service.environment_secret_set_overrides(env_item)
        if secret_name in override_sets:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets?error=Secret+name+already+exists")

        override_sets[secret_name] = entries
        updated_env = dict(env_item)
        updated_env["secret_set_overrides"] = override_sets
        updated_env["secret_overrides"] = env_item.get("secret_overrides", env_item.get("secrets", {}))
        service.update_environment(app_name, env_name, updated_env)
        redirect(f"/applications/{app_name}/environments/{env_name}/secrets?message=Secret+override+added")

    @app.get("/applications/<app_name>/environments/<env_name>/secrets/<secret_name>/edit")
    def environment_secret_edit(app_name, env_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view("error", message="Environment not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        normalized_name = service.validate_secret_set_name(secret_name)
        override_sets = service.environment_secret_set_overrides(env_item)
        entries = override_sets.get(normalized_name)
        if not normalized_name or entries is None:
            response.status = 404
            return render_view("error", message="Secret override not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        message = request.query.get("message", "")
        error = request.query.get("error", "")
        return render_view(
            "secret_edit",
            app_item=app_item,
            env_item=env_item,
            scope_label="Environment Secret Override",
            post_path=f"/applications/{app_name}/environments/{env_name}/secrets/{normalized_name}/edit",
            cancel_path=f"/applications/{app_name}/environments/{env_name}/secrets",
            secret_name=normalized_name,
            entries=entries,
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                (f"Secrets: {env_name}", f"/applications/{app_name}/environments/{env_name}/secrets"),
                (f"Edit: {normalized_name}", ""),
            ),
        )

    @app.post("/applications/<app_name>/environments/<env_name>/secrets/<secret_name>/edit")
    def environment_secret_update(app_name, env_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view("error", message="Environment not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        current_name = service.validate_secret_set_name(secret_name)
        updated_name = service.validate_secret_set_name(request.forms.get("secret_name", ""))
        if not current_name or not updated_name:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets/{secret_name}/edit?error=Secret+name+must+match+kubernetes+naming+rules")

        entries, entry_errors = _parse_secret_entries(request.forms)
        if entry_errors:
            redirect(
                f"/applications/{app_name}/environments/{env_name}/secrets/{current_name}/edit?"
                f"error={quote(entry_errors[0], safe='')}"
            )
        if not entries:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets/{current_name}/edit?error=At+least+one+secret+entry+is+required")

        override_sets = service.environment_secret_set_overrides(env_item)
        if current_name not in override_sets:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets?error=Secret+override+not+found")
        if updated_name != current_name and updated_name in override_sets:
            redirect(f"/applications/{app_name}/environments/{env_name}/secrets/{current_name}/edit?error=Secret+name+already+exists")

        del override_sets[current_name]
        override_sets[updated_name] = entries

        updated_env = dict(env_item)
        updated_env["secret_set_overrides"] = override_sets
        updated_env["secret_overrides"] = env_item.get("secret_overrides", env_item.get("secrets", {}))
        service.update_environment(app_name, env_name, updated_env)
        redirect(f"/applications/{app_name}/environments/{env_name}/secrets/{updated_name}/edit?message=Secret+override+updated")

    @app.post("/applications/<app_name>/environments/<env_name>/secrets/<secret_name>/delete")
    def environment_secret_delete(app_name, env_name, secret_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env_item = service.environment(app_item, env_name)
        if not env_item:
            response.status = 404
            return render_view("error", message="Environment not found", breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")))

        normalized_name = service.validate_secret_set_name(secret_name)
        override_sets = service.environment_secret_set_overrides(env_item)
        if normalized_name in override_sets:
            del override_sets[normalized_name]
            updated_env = dict(env_item)
            updated_env["secret_set_overrides"] = override_sets
            updated_env["secret_overrides"] = env_item.get("secret_overrides", env_item.get("secrets", {}))
            service.update_environment(app_name, env_name, updated_env)
        redirect(f"/applications/{app_name}/environments/{env_name}/secrets")

    @app.get("/applications/<app_name>/namespaces/<namespace_name>/runtime")
    def namespace_runtime(app_name, namespace_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            response.status = 404
            return render_view(
                "error",
                message="Namespace not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        missing_required_namespace_labels = service.missing_required_namespace_labels(namespace_item)

        workloads = {}
        namespace_quotas = []
        namespace_rolebinding_users = []
        cluster_error = ""
        try:
            workloads = kube.namespace_workloads(
                namespace=namespace_name,
                kubeconfig_text=namespace_item.get("kubeconfig", ""),
            )

            namespace_metadata = kube.namespace_metadata(
                namespace=namespace_name,
                kubeconfig_text=namespace_item.get("kubeconfig", ""),
            )
            for quota in namespace_metadata.get("quotas", []):
                metadata = quota.get("metadata", {}) or {}
                spec = quota.get("spec", {}) or {}
                hard = spec.get("hard", {}) or {}

                hard_parts = []
                for key in sorted(hard.keys()):
                    hard_parts.append(f"{key}: {hard.get(key)}")

                scopes = spec.get("scopes", []) or []
                scopes_text = ", ".join(scopes) if scopes else "all"

                namespace_quotas.append(
                    {
                        "name": metadata.get("name", ""),
                        "scopes": scopes_text,
                        "hard": ", ".join(hard_parts) if hard_parts else "none",
                    }
                )

            users_by_name = {}
            for role_binding in namespace_metadata.get("role_bindings", []):
                binding_metadata = role_binding.get("metadata", {}) or {}
                binding_name = binding_metadata.get("name", "")

                role_ref = role_binding.get("role_ref", {}) or {}
                role_ref_kind = role_ref.get("kind", "")
                role_ref_name = role_ref.get("name", "")
                role_name = f"{role_ref_kind}/{role_ref_name}" if role_ref_kind and role_ref_name else role_ref_name

                for subject in role_binding.get("subjects", []) or []:
                    if (subject.get("kind") or "") != "User":
                        continue

                    username = (subject.get("name") or "").strip()
                    if not username:
                        continue

                    user_entry = users_by_name.setdefault(
                        username,
                        {
                            "name": username,
                            "role_bindings": set(),
                            "roles": set(),
                        },
                    )

                    if binding_name:
                        user_entry["role_bindings"].add(binding_name)
                    if role_name:
                        user_entry["roles"].add(role_name)

            namespace_rolebinding_users = []
            for username in sorted(users_by_name.keys()):
                entry = users_by_name[username]
                namespace_rolebinding_users.append(
                    {
                        "name": username,
                        "role_bindings": sorted(entry["role_bindings"]),
                        "roles": sorted(entry["roles"]),
                    }
                )
        except Exception as exc:
            cluster_error = str(exc)

        return render_view(
            "namespace_runtime",
            app_item=app_item,
            namespace_item=namespace_item,
            missing_required_namespace_labels=missing_required_namespace_labels,
            workloads=workloads,
            namespace_quotas=namespace_quotas,
            namespace_rolebinding_users=namespace_rolebinding_users,
            cluster_error=cluster_error,
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                (namespace_name, ""),
            ),
        )

    @app.get("/applications/<app_name>/namespaces/<namespace_name>/pods/<pod_name>/containers/<container_name>/logs")
    def container_logs(app_name, namespace_name, pod_name, container_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            response.status = 404
            return render_view(
                "error",
                message="Namespace not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        logs = kube.pod_logs(
            namespace=namespace_name,
            pod_name=pod_name,
            container_name=container_name,
            kubeconfig_text=namespace_item.get("kubeconfig", ""),
        )

        return render_view(
            "container_logs",
            app_item=app_item,
            namespace_name=namespace_name,
            pod_name=pod_name,
            container_name=container_name,
            logs=_html.escape(logs),
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                (namespace_name, f"/applications/{app_name}/namespaces/{namespace_name}/runtime"),
                (f"{pod_name} / {container_name}", ""),
            ),
        )

    @app.post("/applications/<app_name>/deploy/<env_name>")
    def deploy_application(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        try:
            summary = service.deploy_environment(app_name, env_name)
            message = (
                f"Deployed {app_name} to {summary['namespace']}. "
                f"Applied {summary['manifests']} manifests. "
                f"Release #{summary['release']}."
            )
        except Exception as exc:
            message = f"Deployment failed: {exc}"

        redirect(f"/applications/{app_name}/environment/{env_name}/runtime?message={message}")

    @app.post("/applications/<app_name>/undeploy/<env_name>")
    def undeploy_application(app_name, env_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        try:
            summary = service.undeploy_environment(app_name, env_name)
            message = (
                f"Undeployed {app_name} from {summary['namespace']}. "
                f"Deleted {summary['deleted']} manifests."
            )
            if summary.get("skipped"):
                message += f" Skipped {summary['skipped']} unsupported manifests."
        except Exception as exc:
            message = f"Undeploy failed: {exc}"

        redirect(f"/applications/{app_name}/environment/{env_name}/runtime?message={message}")

    @app.get("/applications/<app_name>/environment/<env_name>/runtime")
    def runtime(app_name, env_name):
        message = request.query.get("message", "")
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env = service.environment(app_item, env_name)
        if not env:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        namespace_name = env.get("namespace", "default")
        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            return render_view(
                "runtime",
                app_item=app_item,
                env=env,
                runtime={},
                namespace_data={},
                component_statuses=[],
                pod_details=[],
                cluster_error=(
                    f"Namespace '{namespace_name}' is not configured for this application. "
                    "Add namespace configuration before viewing runtime."
                ),
                message=message,
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Runtime", "")),
            )

        kubeconfig_text = namespace_item.get("kubeconfig", "")

        runtime_data = {}
        namespace_data = {}
        component_statuses = []
        pod_details = []
        cluster_error = ""
        try:
            runtime_data = kube.application_runtime(
                env.get("namespace", "default"),
                app_name,
                kubeconfig_text=kubeconfig_text,
            )
            namespace_data = kube.namespace_metadata(
                env.get("namespace", "default"),
                kubeconfig_text=kubeconfig_text,
            )

            manifests = service.deployment_plan(app_item, env)
            component_statuses = kube.component_runtime_status(
                manifests=manifests,
                kubeconfig_text=kubeconfig_text,
            )

            for pod in runtime_data.get("pods", []):
                metadata = pod.get("metadata", {}) or {}
                status = pod.get("status", {}) or {}
                spec = pod.get("spec", {}) or {}

                container_statuses = status.get("container_statuses") or []
                ready_count = 0
                restart_count = 0
                for item in container_statuses:
                    if item.get("ready"):
                        ready_count += 1
                    restart_count += item.get("restart_count") or 0

                declared_containers = spec.get("containers") or []
                container_total = len(declared_containers)
                if container_total == 0 and container_statuses:
                    container_total = len(container_statuses)

                container_names = []
                for item in declared_containers:
                    container_name = (item.get("name") or "").strip()
                    if container_name:
                        container_names.append(container_name)

                pod_details.append(
                    {
                        "name": metadata.get("name", ""),
                        "namespace": metadata.get("namespace", env.get("namespace", "default")),
                        "containers": container_names,
                        "phase": status.get("phase", "Unknown"),
                        "ready": f"{ready_count}/{container_total}",
                        "restarts": restart_count,
                    }
                )
        except Exception as exc:
            cluster_error = str(exc)

        return render_view(
            "runtime",
            app_item=app_item,
            env=env,
            runtime=runtime_data,
            namespace_data=namespace_data,
            component_statuses=component_statuses,
            pod_details=pod_details,
            cluster_error=cluster_error,
            message=message,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}"), ("Runtime", "")),
        )

    @app.get("/applications/<app_name>/environment/<env_name>/resources/<kind>/<name>/yaml")
    def runtime_resource_yaml(app_name, env_name, kind, name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env = service.environment(app_item, env_name)
        if not env:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        namespace_name = (request.query.get("namespace", "") or "").strip() or env.get("namespace", "default")
        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            response.status = 404
            return render_view(
                "error",
                message=f"Namespace '{namespace_name}' not configured for this application",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        try:
            yaml_text = kube.resource_yaml(
                kind=kind,
                namespace=namespace_name,
                name=name,
                kubeconfig_text=namespace_item.get("kubeconfig", ""),
            )
        except Exception as exc:
            response.status = 400
            return render_view(
                "error",
                message=f"Unable to fetch resource YAML: {exc}",
                breadcrumbs=breadcrumbs(
                    ("Dashboard", "/"),
                    (app_name, f"/applications/{app_name}"),
                    ("Runtime", f"/applications/{app_name}/environment/{env_name}/runtime"),
                ),
            )

        return render_view(
            "resource_yaml",
            title=f"{kind} / {name}",
            subtitle=f"Namespace: {namespace_name}",
            yaml_text=_html.escape(yaml_text),
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                ("Runtime", f"/applications/{app_name}/environment/{env_name}/runtime"),
                (f"{kind} YAML", ""),
            ),
        )

    @app.get("/applications/<app_name>/environment/<env_name>/pods/<pod_name>/yaml")
    def runtime_pod_yaml(app_name, env_name, pod_name):
        app_item = service.get_app(app_name)
        if not app_item:
            response.status = 404
            return render_view("error", message="Application not found", breadcrumbs=breadcrumbs(("Dashboard", "/")))

        env = service.environment(app_item, env_name)
        if not env:
            response.status = 404
            return render_view(
                "error",
                message="Environment not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        namespace_name = (request.query.get("namespace", "") or "").strip() or env.get("namespace", "default")
        namespace_item = service.namespace_config(app_item, namespace_name)
        if not namespace_item:
            response.status = 404
            return render_view(
                "error",
                message=f"Namespace '{namespace_name}' not configured for this application",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), (app_name, f"/applications/{app_name}")),
            )

        try:
            yaml_text = kube.pod_yaml(
                namespace=namespace_name,
                pod_name=pod_name,
                kubeconfig_text=namespace_item.get("kubeconfig", ""),
            )
        except Exception as exc:
            response.status = 400
            return render_view(
                "error",
                message=f"Unable to fetch pod YAML: {exc}",
                breadcrumbs=breadcrumbs(
                    ("Dashboard", "/"),
                    (app_name, f"/applications/{app_name}"),
                    ("Runtime", f"/applications/{app_name}/environment/{env_name}/runtime"),
                ),
            )

        return render_view(
            "resource_yaml",
            title=f"Pod / {pod_name}",
            subtitle=f"Namespace: {namespace_name}",
            yaml_text=_html.escape(yaml_text),
            breadcrumbs=breadcrumbs(
                ("Dashboard", "/"),
                (app_name, f"/applications/{app_name}"),
                ("Runtime", f"/applications/{app_name}/environment/{env_name}/runtime"),
                ("Pod YAML", ""),
            ),
        )

    @app.get("/operations")
    def operations_home():
        namespace = request.query.get("namespace", "default")
        app_name = request.query.get("application", "")
        message = request.query.get("message", "")
        workloads = []
        error = ""

        try:
            workloads = kube.discover_workloads(namespace=namespace, app_name=app_name or None)
        except Exception as exc:
            error = str(exc)

        return render_view(
            "operations",
            namespace=namespace,
            app_name=app_name,
            workloads=workloads,
            error=error,
            message=message,
            apps=service.all_apps(),
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("Operations", "")),
        )

    @app.post("/operations/scale")
    def scale_workload():
        namespace = request.forms.get("namespace", "default")
        kind = request.forms.get("kind", "")
        name = request.forms.get("name", "")
        try:
            replicas = int(request.forms.get("replicas", "1"))
        except ValueError:
            replicas = 1

        try:
            kube.scale_workload(namespace=namespace, kind=kind, name=name, replicas=replicas)
            msg = f"Scaled {kind}/{name} to {replicas} replicas"
        except Exception as exc:
            msg = f"Scale failed: {exc}"

        redirect(f"/operations?namespace={namespace}&message={msg}")

    @app.get("/settings")
    def settings():
        message = request.query.get("message", "")
        error = request.query.get("error", "")
        edit_name = request.query.get("edit_name", "").strip()
        edit_scope = request.query.get("edit_scope", "").strip().lower()

        required_labels = service.required_labels()
        edit_label = None
        if edit_name and edit_scope:
            for item in required_labels:
                if item.get("name") == edit_name and item.get("scope") == edit_scope:
                    edit_label = item
                    break

            if not edit_label and not error:
                error = "Required label not found for editing."

        return render_view(
            "settings",
            required_labels=required_labels,
            edit_label=edit_label,
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("Settings", "")),
        )

    @app.get("/accounts")
    def accounts():
        message = request.query.get("message", "")
        error = request.query.get("error", "")
        return render_view(
            "users",
            users=auth.list_users(),
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("User Accounts", "")),
        )

    @app.get("/accounts/new")
    def new_account():
        message = request.query.get("message", "")
        error = request.query.get("error", "")
        return render_view(
            "user_account_form",
            is_edit=False,
            username="",
            page_title="Create User",
            page_subtitle="Add a new console user account.",
            password_label="Initial Password",
            submit_label="Create User",
            submit_path="/settings/users",
            redirect_to="/accounts/new",
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("User Accounts", "/accounts"), ("Create User", "")),
        )

    @app.get("/accounts/<username>/edit")
    def edit_account(username):
        message = request.query.get("message", "")
        error = request.query.get("error", "")
        if not auth.user_exists(username):
            response.status = 404
            return render_view(
                "error",
                message="User not found",
                breadcrumbs=breadcrumbs(("Dashboard", "/"), ("User Accounts", "/accounts")),
            )

        return render_view(
            "user_account_form",
            is_edit=True,
            username=username,
            page_title=f"Edit User: {username}",
            page_subtitle="Set a new password for this account.",
            password_label="New Password",
            submit_label="Update Password",
            submit_path="/settings/users/password",
            redirect_to=f"/accounts/{username}/edit",
            message=message,
            error=error,
            breadcrumbs=breadcrumbs(("Dashboard", "/"), ("User Accounts", "/accounts"), ("Edit User", "")),
        )

    @app.post("/settings/labels")
    def add_required_label():
        name = request.forms.get("name", "").strip()
        description = request.forms.get("description", "").strip()
        scope = request.forms.get("scope", "").strip().lower()
        try:
            service.add_required_label(name=name, description=description, scope=scope)
            redirect("/settings?message=Required+label+added")
        except ValueError as exc:
            redirect(f"/settings?error={quote(str(exc), safe='')}")

    @app.post("/settings/labels/delete")
    def delete_required_label():
        name = request.forms.get("name", "").strip()
        scope = request.forms.get("scope", "").strip().lower()
        if name and scope:
            service.remove_required_label(name, scope)
        redirect("/settings")

    @app.post("/settings/labels/update")
    def update_required_label():
        current_name = request.forms.get("current_name", "").strip()
        current_scope = request.forms.get("current_scope", "").strip().lower()
        name = request.forms.get("name", "").strip()
        description = request.forms.get("description", "").strip()
        scope = request.forms.get("scope", "").strip().lower()

        try:
            service.update_required_label(
                current_name=current_name,
                current_scope=current_scope,
                name=name,
                description=description,
                scope=scope,
            )
            redirect("/settings?message=Required+label+updated")
        except ValueError as exc:
            redirect(
                f"/settings?edit_name={quote(current_name, safe='')}&"
                f"edit_scope={quote(current_scope, safe='')}&"
                f"error={quote(str(exc), safe='')}"
            )

    @app.post("/settings/users")
    def add_user():
        username = request.forms.get("username", "").strip()
        password = request.forms.get("password", "")
        redirect_to = request.forms.get("redirect_to", "/accounts").strip() or "/accounts"
        if not redirect_to.startswith("/"):
            redirect_to = "/accounts"

        try:
            auth.create_user(username=username, password=password)
            redirect(f"{redirect_to}?message=User+created")
        except ValueError as exc:
            redirect(f"{redirect_to}?error={quote(str(exc), safe='')}")

    @app.post("/settings/users/password")
    def update_user_password():
        username = request.forms.get("username", "").strip()
        password = request.forms.get("password", "")
        confirm_password = request.forms.get("confirm_password", "")
        redirect_to = request.forms.get("redirect_to", "/accounts").strip() or "/accounts"
        if not redirect_to.startswith("/"):
            redirect_to = "/accounts"

        if password != confirm_password:
            redirect(f"{redirect_to}?error=Passwords+do+not+match")

        try:
            auth.set_password(username=username, password=password)
            redirect(f"{redirect_to}?message=Password+updated")
        except ValueError as exc:
            redirect(f"{redirect_to}?error={quote(str(exc), safe='')}")

    @app.post("/settings/users/delete")
    def remove_user():
        username = request.forms.get("username", "").strip()
        acting_user = current_user()

        if username == acting_user:
            redirect("/accounts?error=You+cannot+delete+your+own+active+account")

        try:
            auth.delete_user(username=username)
            redirect("/accounts?message=User+deleted")
        except ValueError as exc:
            redirect(f"/accounts?error={quote(str(exc), safe='')}")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


def run(host="0.0.0.0", port=8080, debug=False):
    bottle_app = create_app()
    bottle_app.run(host=host, port=port, debug=debug, reloader=debug)
