import os
import json
import shutil
import re

from .template_engine import collect_template_variables, render_template_text, render_templates


class PipelineService:
    def __init__(self, store, kube, template_dir):
        self.store = store
        self.kube = kube
        self.template_dir = template_dir

    def all_apps(self):
        apps = []
        if not os.path.exists(self.store.base_dir):
            return apps

        for entry in sorted(os.listdir(self.store.base_dir)):
            app_dir = os.path.join(self.store.base_dir, entry)
            if not os.path.isdir(app_dir):
                continue

            app_file = self._app_file(entry)
            if not os.path.exists(app_file):
                continue

            with open(app_file, "r", encoding="utf-8") as handle:
                try:
                    app_item = json.load(handle)
                except json.JSONDecodeError:
                    continue

            if isinstance(app_item, dict) and app_item.get("name"):
                apps.append(app_item)

        return sorted(apps, key=lambda item: item.get("name", ""))

    def get_app(self, app_name):
        for app in self.all_apps():
            if app.get("name") == app_name:
                return app
        return None

    def save_app(self, app):
        app_name = self._validated_app_name(app.get("name", ""))
        app_dir = self._app_dir(app_name)
        os.makedirs(app_dir, exist_ok=True)

        app_file = self._app_file(app_name)
        with open(app_file, "w", encoding="utf-8") as handle:
            json.dump(app, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def delete_app(self, app_name):
        app_name = (app_name or "").strip()
        app_dir = self._app_dir(app_name)
        if os.path.isdir(app_dir):
            shutil.rmtree(app_dir)

    def _validated_app_name(self, app_name):
        name = (app_name or "").strip()
        if not name:
            raise ValueError("Application name is required.")
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError("Application name contains invalid path characters.")
        return name

    def _app_dir(self, app_name):
        return os.path.join(self.store.base_dir, app_name)

    def _app_file(self, app_name):
        return os.path.join(self._app_dir(app_name), "application.json")

    def required_labels(self):
        payload = self.store.load("policies", {"required_labels": []})
        labels = payload.get("required_labels", [])
        normalized = []
        for item in labels:
            scope = (item.get("scope") or "application").strip().lower()
            if scope not in {"application", "namespace"}:
                scope = "application"
            normalized.append(
                {
                    "name": (item.get("name") or "").strip(),
                    "description": (item.get("description") or "").strip(),
                    "scope": scope,
                }
            )
        return sorted(normalized, key=lambda item: (item.get("scope", ""), item.get("name", "")))

    def required_labels_for_scope(self, scope):
        scoped = []
        expected = (scope or "").strip().lower()
        for item in self.required_labels():
            if item.get("scope") == expected:
                scoped.append(item)
        return scoped

    def add_required_label(self, name, description, scope):
        name = (name or "").strip()
        description = (description or "").strip()
        scope = (scope or "").strip().lower()

        if not name:
            raise ValueError("Label name is required.")
        if not description:
            raise ValueError("Label description is required.")
        if scope not in {"application", "namespace"}:
            raise ValueError("Label scope must be application or namespace.")

        payload = self.store.load("policies", {"required_labels": []})
        labels = payload.get("required_labels", [])

        for item in labels:
            if item.get("name") == name and (item.get("scope") or "application") == scope:
                raise ValueError("Required label already exists for this scope.")

        labels.append({"name": name, "description": description, "scope": scope})
        payload["required_labels"] = sorted(
            labels,
            key=lambda item: ((item.get("scope") or "application"), item.get("name", "")),
        )
        self.store.save("policies", payload)

    def update_required_label(self, current_name, current_scope, name, description, scope):
        current_name = (current_name or "").strip()
        current_scope = (current_scope or "").strip().lower()
        name = (name or "").strip()
        description = (description or "").strip()
        scope = (scope or "").strip().lower()

        if not current_name:
            raise ValueError("Current label name is required.")
        if current_scope not in {"application", "namespace"}:
            raise ValueError("Current label scope must be application or namespace.")
        if not name:
            raise ValueError("Label name is required.")
        if not description:
            raise ValueError("Label description is required.")
        if scope not in {"application", "namespace"}:
            raise ValueError("Label scope must be application or namespace.")

        payload = self.store.load("policies", {"required_labels": []})
        labels = payload.get("required_labels", [])

        target_index = -1
        for index, item in enumerate(labels):
            item_scope = (item.get("scope") or "application").strip().lower()
            if item.get("name") == current_name and item_scope == current_scope:
                target_index = index
                break

        if target_index < 0:
            raise ValueError("Required label not found.")

        for index, item in enumerate(labels):
            if index == target_index:
                continue
            item_scope = (item.get("scope") or "application").strip().lower()
            if item.get("name") == name and item_scope == scope:
                raise ValueError("Required label already exists for this scope.")

        labels[target_index] = {"name": name, "description": description, "scope": scope}
        payload["required_labels"] = sorted(
            labels,
            key=lambda item: ((item.get("scope") or "application"), item.get("name", "")),
        )
        self.store.save("policies", payload)

    def remove_required_label(self, name, scope):
        payload = self.store.load("policies", {"required_labels": []})
        name = (name or "").strip()
        scope = (scope or "").strip().lower()
        labels = []
        for item in payload.get("required_labels", []):
            item_scope = (item.get("scope") or "application").strip().lower()
            if item.get("name") == name and item_scope == scope:
                continue
            labels.append(item)
        payload["required_labels"] = labels
        self.store.save("policies", payload)

    def validation_errors(self, app):
        errors = []
        for required in self.missing_required_application_labels(app):
            key = required.get("name")
            errors.append(f"Missing required application label '{key}': {required.get('description', '')}")

        errors.extend(self.namespace_validation_errors(app))
        errors.extend(self.environment_validation_errors(app))
        return errors

    def missing_required_application_labels(self, app):
        labels = {item.get("name"): item.get("value") for item in app.get("labels", [])}
        missing = []
        for required in self.required_labels_for_scope("application"):
            key = required.get("name")
            if key and not labels.get(key):
                missing.append(required)
        return missing

    def missing_required_namespace_labels(self, namespace_item):
        namespace_labels = {lbl.get("name"): lbl.get("value") for lbl in namespace_item.get("labels", [])}
        missing = []
        for required in self.required_labels_for_scope("namespace"):
            key = required.get("name")
            if key and not namespace_labels.get(key):
                missing.append(required)
        return missing

    def namespace_validation_errors(self, app):
        errors = []
        seen = set()

        for item in app.get("namespaces", []):
            name = (item.get("name") or "").strip()
            if not name:
                errors.append("Each namespace entry must have a name.")
                continue

            if name in seen:
                errors.append(f"Duplicate namespace configuration: {name}")
            seen.add(name)

            if not (item.get("kubeconfig") or "").strip():
                errors.append(f"Namespace '{name}' is missing kubeconfig.")

            namespace_labels = {lbl.get("name"): lbl.get("value") for lbl in item.get("labels", [])}
            for required in self.required_labels_for_scope("namespace"):
                key = required.get("name")
                if key and not namespace_labels.get(key):
                    errors.append(
                        f"Namespace '{name}' is missing required label '{key}': {required.get('description', '')}"
                    )

        return errors

    def namespaces(self, app):
        return sorted(app.get("namespaces", []), key=lambda item: item.get("name", ""))

    def namespace_config(self, app, namespace_name):
        for item in app.get("namespaces", []):
            if item.get("name") == namespace_name:
                return item
        return None

    def add_namespace(self, app_name, namespace_item):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        namespace_name = (namespace_item.get("name") or "").strip()
        if not namespace_name:
            raise ValueError("Namespace name is required.")
        if not (namespace_item.get("kubeconfig") or "").strip():
            raise ValueError("Kubeconfig is required.")

        if self.namespace_config(app, namespace_name):
            raise ValueError("Namespace already exists for this application.")

        namespace_labels = {lbl.get("name"): lbl.get("value") for lbl in namespace_item.get("labels", [])}
        for required in self.required_labels_for_scope("namespace"):
            key = required.get("name")
            if key and not namespace_labels.get(key):
                raise ValueError(f"Missing required namespace label '{key}': {required.get('description', '')}")

        app.setdefault("namespaces", []).append(namespace_item)
        app["namespaces"] = self.namespaces(app)
        self.save_app(app)

    def update_namespace(self, app_name, current_namespace_name, namespace_item):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        current_namespace_name = (current_namespace_name or "").strip()
        updated_namespace_name = (namespace_item.get("name") or "").strip()

        if not current_namespace_name:
            raise ValueError("Current namespace name is required.")
        if not updated_namespace_name:
            raise ValueError("Namespace name is required.")
        if not (namespace_item.get("kubeconfig") or "").strip():
            raise ValueError("Kubeconfig is required.")

        namespaces = app.get("namespaces", [])
        index = -1
        for i, item in enumerate(namespaces):
            if item.get("name") == current_namespace_name:
                index = i
                break

        if index < 0:
            raise ValueError("Namespace does not exist for this application.")

        if updated_namespace_name != current_namespace_name:
            for item in namespaces:
                if item.get("name") == updated_namespace_name:
                    raise ValueError("Namespace already exists for this application.")

        namespace_labels = {lbl.get("name"): lbl.get("value") for lbl in namespace_item.get("labels", [])}
        for required in self.required_labels_for_scope("namespace"):
            key = required.get("name")
            if key and not namespace_labels.get(key):
                raise ValueError(f"Missing required namespace label '{key}': {required.get('description', '')}")

        namespaces[index] = namespace_item

        # Keep environment namespace references consistent on rename.
        if updated_namespace_name != current_namespace_name:
            for env in app.get("environments", []):
                if (env.get("namespace") or "").strip() == current_namespace_name:
                    env["namespace"] = updated_namespace_name

        app["namespaces"] = self.namespaces(app)
        self.save_app(app)

    def delete_namespace(self, app_name, namespace_name):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        namespace_name = (namespace_name or "").strip()
        namespaces = [item for item in app.get("namespaces", []) if item.get("name") != namespace_name]

        if len(namespaces) == len(app.get("namespaces", [])):
            raise ValueError("Namespace not found.")

        app["namespaces"] = namespaces
        self.save_app(app)

    def environment(self, app, env_name):
        for env in app.get("environments", []):
            if env.get("name") == env_name:
                return env
        return None

    def environments(self, app):
        return sorted(app.get("environments", []), key=lambda item: item.get("name", ""))

    def environment_validation_errors(self, app):
        errors = []
        seen = set()
        known_namespaces = {
            (item.get("name") or "").strip()
            for item in app.get("namespaces", [])
            if (item.get("name") or "").strip()
        }

        for env in app.get("environments", []):
            env_name = (env.get("name") or "").strip()
            if not env_name:
                errors.append("Each environment entry must have a name.")
                continue

            if env_name in seen:
                errors.append(f"Duplicate environment configuration: {env_name}")
            seen.add(env_name)

            namespace_name = (env.get("namespace") or "").strip()
            if not namespace_name:
                errors.append(f"Environment '{env_name}' is missing namespace.")
            elif namespace_name not in known_namespaces:
                errors.append(
                    f"Environment '{env_name}' references namespace '{namespace_name}' without configuration."
                )

            template_files = [
                (item or "").strip()
                for item in env.get("template_files", [])
                if (item or "").strip()
            ]

            label_names = set()
            for label in env.get("labels", []):
                label_name = (label.get("name") or "").strip()
                if not label_name:
                    continue
                if label_name in label_names:
                    errors.append(f"Environment '{env_name}' has duplicate label '{label_name}'.")
                label_names.add(label_name)

        return errors

    def add_environment(self, app_name, env_item):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        env_name = (env_item.get("name") or "").strip()
        if not env_name:
            raise ValueError("Environment name is required.")
        if self.environment(app, env_name):
            raise ValueError("Environment already exists for this application.")

        validation_target = dict(app)
        validation_target["environments"] = app.get("environments", []) + [env_item]
        errors = self.environment_validation_errors(validation_target)
        if errors:
            raise ValueError(errors[0])

        if "release" not in env_item:
            env_item["release"] = 0

        app.setdefault("environments", []).append(env_item)
        app["environments"] = self.environments(app)
        self.save_app(app)

    def update_environment(self, app_name, current_env_name, env_item):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        current_env_name = (current_env_name or "").strip()
        updated_env_name = (env_item.get("name") or "").strip()

        if not current_env_name:
            raise ValueError("Current environment name is required.")
        if not updated_env_name:
            raise ValueError("Environment name is required.")

        environments = app.get("environments", [])
        index = -1
        for i, item in enumerate(environments):
            if item.get("name") == current_env_name:
                index = i
                break

        if index < 0:
            raise ValueError("Environment does not exist for this application.")

        if updated_env_name != current_env_name:
            for item in environments:
                if item.get("name") == updated_env_name:
                    raise ValueError("Environment already exists for this application.")

        updated_environments = list(environments)
        updated_environments[index] = env_item
        validation_target = dict(app)
        validation_target["environments"] = updated_environments
        errors = self.environment_validation_errors(validation_target)
        if errors:
            raise ValueError(errors[0])

        app["environments"] = sorted(updated_environments, key=lambda item: item.get("name", ""))
        self.save_app(app)

    def delete_environment(self, app_name, env_name):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        env_name = (env_name or "").strip()
        environments = [item for item in app.get("environments", []) if item.get("name") != env_name]

        if len(environments) == len(app.get("environments", [])):
            raise ValueError("Environment not found.")

        app["environments"] = environments
        self.save_app(app)

    def normalized_templates(self, source):
        entries = []
        for item in source.get("templates", []):
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
        return entries

    def normalized_mapping(self, value):
        if not isinstance(value, dict):
            return {}

        normalized = {}
        for key, item in value.items():
            key_name = (str(key) if key is not None else "").strip()
            if not key_name:
                continue
            normalized[key_name] = item
        return normalized

    def app_templates(self, app):
        return self.normalized_templates(app)

    def app_template_files(self, app):
        return [
            (item or "").strip()
            for item in app.get("template_files", [])
            if (item or "").strip()
        ]

    def app_inline_template(self, app):
        return (app.get("template") or "").strip()

    def app_variable_defaults(self, app):
        return self.normalized_mapping(app.get("variables", {}))

    def app_secret_defaults(self, app):
        secret_sets = self.app_secret_sets(app)
        return dict(secret_sets.get("default", {}))

    def environment_variable_overrides(self, env):
        # If the new override field exists (even as {}), treat it as authoritative.
        if "variable_overrides" in env:
            return self.normalized_mapping(env.get("variable_overrides", {}))

        # Legacy shape where variables were stored directly on the environment.
        return self.normalized_mapping(env.get("variables", {}))

    def environment_secret_overrides(self, env):
        # If the new override field exists (even as {}), treat it as authoritative.
        if "secret_overrides" in env:
            return self.normalized_mapping(env.get("secret_overrides", {}))

        # Legacy shape where secrets were stored directly on the environment.
        return self.normalized_mapping(env.get("secrets", {}))

    def _normalize_secret_sets(self, value):
        if not isinstance(value, dict):
            return {}

        normalized = {}
        for secret_name, payload in value.items():
            name = self._normalized_secret_set_name(secret_name)
            if not name:
                continue
            if not isinstance(payload, dict):
                continue

            entries = {}
            for key, item in payload.items():
                key_name = (str(key) if key is not None else "").strip()
                if not key_name:
                    continue
                entries[key_name] = "" if item is None else str(item)

            normalized[name] = entries
        return normalized

    def _normalized_secret_set_name(self, value):
        name = (str(value) if value is not None else "").strip().lower()
        if not name:
            return ""
        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name):
            return ""
        return name

    def validate_secret_set_name(self, value):
        return self._normalized_secret_set_name(value)

    def app_secret_sets(self, app):
        # Current shape: named secret sets.
        if "secret_sets" in app:
            return self._normalize_secret_sets(app.get("secret_sets", {}))

        # Legacy shape: one mapping of key/value secrets.
        legacy = self.normalized_mapping(app.get("secrets", {}))
        if not legacy:
            return {}
        return {"default": {key: "" if value is None else str(value) for key, value in legacy.items()}}

    def environment_secret_set_overrides(self, env):
        # Current shape: per-secret-set overrides.
        if "secret_set_overrides" in env:
            return self._normalize_secret_sets(env.get("secret_set_overrides", {}))

        # Compatibility with single mapping override shape.
        legacy = self.environment_secret_overrides(env)
        if not legacy:
            return {}
        return {"default": {key: "" if value is None else str(value) for key, value in legacy.items()}}

    def resolve_environment_secret_sets(self, app, env):
        resolved = {}

        app_sets = self.app_secret_sets(app)
        for name, payload in app_sets.items():
            resolved[name] = dict(payload)

        env_sets = self.environment_secret_set_overrides(env)
        for name, payload in env_sets.items():
            merged = dict(resolved.get(name, {}))
            merged.update(payload)
            resolved[name] = merged

        return resolved

    def templates_for_environment(self, app, env):
        app_templates = self.app_templates(app)
        if app_templates:
            return app_templates

        # Legacy shape where templates were environment-specific.
        return self.normalized_templates(env)

    def template_files_for_environment(self, app, env):
        app_template_files = self.app_template_files(app)
        if app_template_files:
            return app_template_files
        return [
            (item or "").strip()
            for item in env.get("template_files", [])
            if (item or "").strip()
        ]

    def inline_template_for_environment(self, app, env):
        app_inline_template = self.app_inline_template(app)
        if app_inline_template:
            return app_inline_template
        return (env.get("template") or "").strip()

    def resolve_environment_context(self, app, env):
        merged_variables = self.app_variable_defaults(app)
        merged_variables.update(self.environment_variable_overrides(env))

        context = dict(merged_variables)

        return {
            "context": context,
            "variables": merged_variables,
        }

    def resolve_environment_secrets(self, app, env):
        return dict(self.resolve_environment_secret_sets(app, env).get("default", {}))

    def secret_name_for_environment(self, app, env, secret_set_name="default"):
        app_name = (app.get("name") or "app").strip().lower()
        env_name = (env.get("name") or "env").strip().lower()
        set_name = self._normalized_secret_set_name(secret_set_name) or "default"

        combined = f"{app_name}-{env_name}-{set_name}"
        cleaned = re.sub(r"[^a-z0-9-]+", "-", combined)
        cleaned = re.sub(r"-+", "-", cleaned).strip("-")
        return cleaned[:253] if cleaned else "pipeline-default"

    def secret_manifests_for_environment(self, app, env):
        resolved_sets = self.resolve_environment_secret_sets(app, env)
        manifests = []

        namespace = (env.get("namespace") or "default").strip() or "default"
        for set_name, entries in resolved_sets.items():
            if not entries:
                continue

            manifests.append(
                {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": self.secret_name_for_environment(app, env, set_name),
                        "namespace": namespace,
                        "labels": {
                            "pipeline.app": app.get("name"),
                            "pipeline.environment": env.get("name"),
                            "pipeline.secret-set": set_name,
                        },
                    },
                    "type": "Opaque",
                    "stringData": dict(entries),
                },
            )

        return manifests

    def promotion_missing_variables(self, app):
        findings = []
        for env in app.get("environments", []):
            context_info = self.resolve_environment_context(app, env)
            context = context_info.get("context", {})

            inline_templates = self.templates_for_environment(app, env)
            if inline_templates:
                for index, inline_template in enumerate(inline_templates):
                    variables = collect_template_variables(inline_template.get("content", ""))
                    missing = [var for var in variables if var not in context]
                    if missing:
                        findings.append(
                            {
                                "environment": env.get("name"),
                                "template": f"inline-template-{index + 1}",
                                "missing": sorted(missing),
                            }
                        )
                continue

            inline_template = self.inline_template_for_environment(app, env)
            if inline_template:
                variables = collect_template_variables(inline_template)
                missing = [var for var in variables if var not in context]
                if missing:
                    findings.append(
                        {
                            "environment": env.get("name"),
                            "template": "inline-template",
                            "missing": sorted(missing),
                        }
                    )
                continue

            for template_file in self.template_files_for_environment(app, env):
                path = os.path.join(self.template_dir, template_file)
                if not os.path.exists(path):
                    findings.append(
                        {
                            "environment": env.get("name"),
                            "template": template_file,
                            "missing": ["template file is missing"],
                        }
                    )
                    continue

                with open(path, "r", encoding="utf-8") as handle:
                    variables = collect_template_variables(handle.read())

                missing = [var for var in variables if var not in context]
                if missing:
                    findings.append(
                        {
                            "environment": env.get("name"),
                            "template": template_file,
                            "missing": sorted(missing),
                        }
                    )

        return findings

    def deployment_plan(self, app, env):
        context_info = self.resolve_environment_context(app, env)
        context = context_info.get("context", {})

        inline_templates = self.templates_for_environment(app, env)
        if inline_templates:
            manifests = []
            for template_item in inline_templates:
                manifests.extend(render_template_text(template_item.get("content", ""), context=context))
        else:
            inline_template = self.inline_template_for_environment(app, env)
            if inline_template:
                manifests = render_template_text(inline_template, context=context)
            else:
                manifests = render_templates(
                    template_dir=self.template_dir,
                    template_files=self.template_files_for_environment(app, env),
                    context=context,
                )

        labels = {"pipeline.app": app.get("name"), "pipeline.environment": env.get("name")}
        for user_label in app.get("labels", []):
            label_name = user_label.get("name")
            label_value = user_label.get("value")
            if label_name:
                labels[label_name] = label_value
        for env_label in env.get("labels", []):
            label_name = env_label.get("name")
            label_value = env_label.get("value")
            if label_name:
                labels[label_name] = label_value

        for manifest in manifests:
            metadata = manifest.setdefault("metadata", {})
            metadata.setdefault("labels", {})
            metadata["labels"].update(labels)
            metadata.setdefault("namespace", env.get("namespace", "default"))

        return manifests

    def deploy_environment(self, app_name, env_name):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        env = self.environment(app, env_name)
        if not env:
            raise ValueError("Unknown environment")

        namespace_name = env.get("namespace", "default")
        namespace_item = self.namespace_config(app, namespace_name)
        if not namespace_item:
            raise ValueError(f"Namespace '{namespace_name}' is not configured for this application")

        kubeconfig_text = namespace_item.get("kubeconfig", "")

        secret_manifests = self.secret_manifests_for_environment(app, env)
        manifests = self.deployment_plan(app, env)

        for secret_manifest in secret_manifests:
            self.kube.apply_manifest(secret_manifest, kubeconfig_text=kubeconfig_text)

        for manifest in manifests:
            self.kube.apply_manifest(manifest, kubeconfig_text=kubeconfig_text)

        current_release = env.get("release", 0)
        try:
            current_release = int(current_release)
        except (TypeError, ValueError):
            current_release = 0

        next_release = current_release + 1
        env["release"] = next_release
        self.save_app(app)

        history = self.store.load("deployments", {"deployments": []})
        manifest_kinds = [item.get("kind", "Unknown") for item in manifests]
        if secret_manifests:
            manifest_kinds = (["Secret"] * len(secret_manifests)) + manifest_kinds
        history.setdefault("deployments", []).append(
            {
                "application": app_name,
                "environment": env_name,
                "namespace": env.get("namespace", "default"),
                "release": next_release,
                "manifests": manifest_kinds,
            }
        )
        self.store.save("deployments", history)

        return {
            "namespace": env.get("namespace", "default"),
            "manifests": len(manifests) + len(secret_manifests),
            "release": next_release,
        }

    def undeploy_environment(self, app_name, env_name):
        app = self.get_app(app_name)
        if not app:
            raise ValueError("Unknown application")

        env = self.environment(app, env_name)
        if not env:
            raise ValueError("Unknown environment")

        namespace_name = env.get("namespace", "default")
        namespace_item = self.namespace_config(app, namespace_name)
        if not namespace_item:
            raise ValueError(f"Namespace '{namespace_name}' is not configured for this application")

        kubeconfig_text = namespace_item.get("kubeconfig", "")
        secret_manifests = self.secret_manifests_for_environment(app, env)
        manifests = self.deployment_plan(app, env)

        deleted = 0
        skipped = 0
        for secret_manifest in secret_manifests:
            try:
                self.kube.delete_manifest(secret_manifest, kubeconfig_text=kubeconfig_text)
                deleted += 1
            except ValueError:
                skipped += 1

        for manifest in reversed(manifests):
            try:
                self.kube.delete_manifest(manifest, kubeconfig_text=kubeconfig_text)
                deleted += 1
            except ValueError:
                skipped += 1

        history = self.store.load("deployments", {"deployments": []})
        manifest_kinds = [item.get("kind", "Unknown") for item in manifests]
        if secret_manifests:
            manifest_kinds = (["Secret"] * len(secret_manifests)) + manifest_kinds
        history.setdefault("deployments", []).append(
            {
                "application": app_name,
                "environment": env_name,
                "namespace": env.get("namespace", "default"),
                "action": "undeploy",
                "manifests": manifest_kinds,
            }
        )
        self.store.save("deployments", history)

        return {
            "namespace": env.get("namespace", "default"),
            "deleted": deleted,
            "skipped": skipped,
        }

    def dashboard_items(self):
        items = []
        for app in self.all_apps():
            app_missing = self.missing_required_application_labels(app)
            namespace_missing = 0
            for namespace_item in app.get("namespaces", []):
                namespace_missing += len(self.missing_required_namespace_labels(namespace_item))

            item = {
                "name": app.get("name"),
                "description": app.get("description", ""),
                "environments": len(app.get("environments", [])),
                "labels": app.get("labels", []),
                "missing_required_app_labels": app_missing,
                "required_label_status": {
                    "app_missing": len(app_missing),
                    "namespace_missing": namespace_missing,
                    "total_missing": len(app_missing) + namespace_missing,
                },
            }
            items.append(item)
        return sorted(items, key=lambda entry: entry.get("name", ""))
