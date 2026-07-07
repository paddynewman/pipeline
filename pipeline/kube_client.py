import os

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml


class KubeGateway:
    def configure(self, kubeconfig_text=None):
        if kubeconfig_text:
            parsed = yaml.safe_load(kubeconfig_text)
            if not isinstance(parsed, dict):
                raise ValueError("Invalid kubeconfig content.")
            config.load_kube_config_from_dict(parsed)
            return

        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()

    def reachable(self, kubeconfig_text=None):
        try:
            self.configure(kubeconfig_text=kubeconfig_text)
            client.VersionApi().get_code()
            return True, "Connected"
        except Exception as exc:
            return False, str(exc)

    def apply_manifest(self, manifest, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)

        kind = manifest.get("kind", "")
        namespace = manifest.get("metadata", {}).get("namespace", "default")
        name = manifest.get("metadata", {}).get("name")

        if kind == "Deployment":
            api = client.AppsV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespaced_deployment(name=name, namespace=namespace),
                creator=lambda: api.create_namespaced_deployment(namespace=namespace, body=manifest),
                replacer=lambda: api.replace_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    body=manifest,
                ),
            )
        elif kind == "StatefulSet":
            api = client.AppsV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespaced_stateful_set(name=name, namespace=namespace),
                creator=lambda: api.create_namespaced_stateful_set(namespace=namespace, body=manifest),
                replacer=lambda: api.replace_namespaced_stateful_set(
                    name=name,
                    namespace=namespace,
                    body=manifest,
                ),
            )
        elif kind == "Service":
            api = client.CoreV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespaced_service(name=name, namespace=namespace),
                creator=lambda: api.create_namespaced_service(namespace=namespace, body=manifest),
                replacer=lambda: api.replace_namespaced_service(
                    name=name,
                    namespace=namespace,
                    body=manifest,
                ),
            )
        elif kind == "ConfigMap":
            api = client.CoreV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespaced_config_map(name=name, namespace=namespace),
                creator=lambda: api.create_namespaced_config_map(namespace=namespace, body=manifest),
                replacer=lambda: api.replace_namespaced_config_map(
                    name=name,
                    namespace=namespace,
                    body=manifest,
                ),
            )
        elif kind == "Secret":
            api = client.CoreV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespaced_secret(name=name, namespace=namespace),
                creator=lambda: api.create_namespaced_secret(namespace=namespace, body=manifest),
                replacer=lambda: api.replace_namespaced_secret(
                    name=name,
                    namespace=namespace,
                    body=manifest,
                ),
            )
        elif kind == "Namespace":
            api = client.CoreV1Api()
            self._replace_or_create(
                getter=lambda: api.read_namespace(name=name),
                creator=lambda: api.create_namespace(body=manifest),
                replacer=lambda: api.replace_namespace(name=name, body=manifest),
            )
        else:
            raise ValueError(f"Unsupported manifest kind: {kind}")

    def delete_manifest(self, manifest, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)

        kind = manifest.get("kind", "")
        namespace = manifest.get("metadata", {}).get("namespace", "default")
        name = manifest.get("metadata", {}).get("name")

        if kind == "Deployment":
            api = client.AppsV1Api()
            self._delete_if_exists(
                deleter=lambda: api.delete_namespaced_deployment(name=name, namespace=namespace),
            )
        elif kind == "StatefulSet":
            api = client.AppsV1Api()
            self._delete_if_exists(
                deleter=lambda: api.delete_namespaced_stateful_set(name=name, namespace=namespace),
            )
        elif kind == "Service":
            api = client.CoreV1Api()
            self._delete_if_exists(
                deleter=lambda: api.delete_namespaced_service(name=name, namespace=namespace),
            )
        elif kind == "ConfigMap":
            api = client.CoreV1Api()
            self._delete_if_exists(
                deleter=lambda: api.delete_namespaced_config_map(name=name, namespace=namespace),
            )
        elif kind == "Secret":
            api = client.CoreV1Api()
            self._delete_if_exists(
                deleter=lambda: api.delete_namespaced_secret(name=name, namespace=namespace),
            )
        else:
            raise ValueError(f"Unsupported manifest kind: {kind}")

    def _replace_or_create(self, getter, creator, replacer):
        try:
            getter()
            replacer()
        except ApiException as exc:
            if exc.status == 404:
                creator()
            else:
                raise

    def _delete_if_exists(self, deleter):
        try:
            deleter()
        except ApiException as exc:
            if exc.status == 404:
                return
            raise

    def namespace_metadata(self, namespace, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        core = client.CoreV1Api()
        rbac = client.RbacAuthorizationV1Api()

        quotas = core.list_namespaced_resource_quota(namespace=namespace).items
        role_bindings = rbac.list_namespaced_role_binding(namespace=namespace).items
        events = core.list_namespaced_event(namespace=namespace).items

        warning_events = [
            {
                "reason": item.reason,
                "message": item.message,
                "object": (item.involved_object.name if item.involved_object else ""),
                "last_timestamp": str(item.last_timestamp or item.event_time or ""),
            }
            for item in events
            if (item.type or "").lower() == "warning"
        ]

        return {
            "quotas": [q.to_dict() for q in quotas],
            "role_bindings": [r.to_dict() for r in role_bindings],
            "warnings": warning_events,
        }

    def application_runtime(self, namespace, app_name, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        apps = client.AppsV1Api()
        core = client.CoreV1Api()
        label_selector = f"pipeline.app={app_name}"

        deployments = apps.list_namespaced_deployment(
            namespace=namespace,
            label_selector=label_selector,
        ).items
        stateful_sets = apps.list_namespaced_stateful_set(
            namespace=namespace,
            label_selector=label_selector,
        ).items
        pods = []
        seen_pod_uids = set()

        def selector_from_match_labels(match_labels):
            parts = []
            for key, value in (match_labels or {}).items():
                key_name = (str(key) if key is not None else "").strip()
                value_name = (str(value) if value is not None else "").strip()
                if key_name and value_name:
                    parts.append(f"{key_name}={value_name}")
            return ",".join(parts)

        def collect_pods_for_selector(selector):
            if not selector:
                return
            for pod in core.list_namespaced_pod(namespace=namespace, label_selector=selector).items:
                uid = (pod.metadata.uid if pod.metadata else "") or ""
                if uid and uid in seen_pod_uids:
                    continue
                if uid:
                    seen_pod_uids.add(uid)
                pods.append(pod)

        # Pods often do not carry the pipeline.app label directly.
        # Discover them from the workload selectors instead.
        for dep in deployments:
            match_labels = ((dep.spec.selector or {}).match_labels if dep.spec and dep.spec.selector else {})
            collect_pods_for_selector(selector_from_match_labels(match_labels))

        for sts in stateful_sets:
            match_labels = ((sts.spec.selector or {}).match_labels if sts.spec and sts.spec.selector else {})
            collect_pods_for_selector(selector_from_match_labels(match_labels))

        # Fallback for legacy workloads where selectors could not be resolved.
        if not pods:
            pods = core.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
            ).items
        events = core.list_namespaced_event(namespace=namespace).items

        warning_events = [
            {
                "reason": item.reason,
                "message": item.message,
                "object": (item.involved_object.name if item.involved_object else ""),
                "last_timestamp": str(item.last_timestamp or item.event_time or ""),
            }
            for item in events
            if (item.type or "").lower() == "warning"
        ]

        return {
            "deployments": [item.to_dict() for item in deployments],
            "stateful_sets": [item.to_dict() for item in stateful_sets],
            "pods": [item.to_dict() for item in pods],
            "warnings": warning_events,
        }

    def component_runtime_status(self, manifests, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        apps_api = client.AppsV1Api()
        core_api = client.CoreV1Api()

        components = []
        seen = set()
        for manifest in manifests or []:
            kind = (manifest.get("kind") or "").strip()
            metadata = manifest.get("metadata", {}) or {}
            name = (metadata.get("name") or "").strip()
            namespace = (metadata.get("namespace") or "default").strip() or "default"
            if not kind or not name:
                continue

            key = (namespace, kind, name)
            if key in seen:
                continue
            seen.add(key)

            if kind == "Deployment":
                components.append(self._deployment_component_status(apps_api, namespace, name))
            elif kind == "StatefulSet":
                components.append(self._statefulset_component_status(apps_api, namespace, name))
            elif kind == "Service":
                components.append(self._service_component_status(core_api, namespace, name))
            elif kind == "ConfigMap":
                components.append(self._configmap_component_status(core_api, namespace, name))
            else:
                components.append(
                    {
                        "kind": kind,
                        "name": name,
                        "namespace": namespace,
                        "status": "Unknown",
                        "message": "Runtime status not implemented for this kind.",
                    }
                )

        return components

    def _deployment_component_status(self, apps_api, namespace, name):
        try:
            dep = apps_api.read_namespaced_deployment(name=name, namespace=namespace)
            desired = dep.spec.replicas or 0
            ready = dep.status.ready_replicas or 0
            available = dep.status.available_replicas or 0
            status = "Ready" if desired > 0 and ready == desired else "Progressing"
            if desired == 0:
                status = "Scaled to zero"
            return {
                "kind": "Deployment",
                "name": name,
                "namespace": namespace,
                "status": status,
                "message": f"ready {ready}/{desired}, available {available}",
            }
        except ApiException as exc:
            if exc.status == 404:
                return self._missing_component_status("Deployment", namespace, name)
            return self._error_component_status("Deployment", namespace, name, str(exc))

    def _statefulset_component_status(self, apps_api, namespace, name):
        try:
            sts = apps_api.read_namespaced_stateful_set(name=name, namespace=namespace)
            desired = sts.spec.replicas or 0
            ready = sts.status.ready_replicas or 0
            current = sts.status.current_replicas or 0
            status = "Ready" if desired > 0 and ready == desired else "Progressing"
            if desired == 0:
                status = "Scaled to zero"
            return {
                "kind": "StatefulSet",
                "name": name,
                "namespace": namespace,
                "status": status,
                "message": f"ready {ready}/{desired}, current {current}",
            }
        except ApiException as exc:
            if exc.status == 404:
                return self._missing_component_status("StatefulSet", namespace, name)
            return self._error_component_status("StatefulSet", namespace, name, str(exc))

    def _service_component_status(self, core_api, namespace, name):
        try:
            svc = core_api.read_namespaced_service(name=name, namespace=namespace)
            svc_type = (svc.spec.type or "ClusterIP") if svc.spec else "ClusterIP"
            status = "Ready"
            message = f"type {svc_type}"

            ingress_items = []
            if svc.status and svc.status.load_balancer and svc.status.load_balancer.ingress:
                ingress_items = svc.status.load_balancer.ingress

            if svc_type == "LoadBalancer":
                if ingress_items:
                    status = "Ready"
                    addresses = []
                    for ingress in ingress_items:
                        host_or_ip = ingress.hostname or ingress.ip or ""
                        if host_or_ip:
                            addresses.append(host_or_ip)
                    if addresses:
                        message = f"type {svc_type}, ingress {', '.join(addresses)}"
                    else:
                        message = f"type {svc_type}, ingress assigned"
                else:
                    status = "Provisioning"
                    message = f"type {svc_type}, waiting for ingress"

            return {
                "kind": "Service",
                "name": name,
                "namespace": namespace,
                "status": status,
                "message": message,
            }
        except ApiException as exc:
            if exc.status == 404:
                return self._missing_component_status("Service", namespace, name)
            return self._error_component_status("Service", namespace, name, str(exc))

    def _configmap_component_status(self, core_api, namespace, name):
        try:
            core_api.read_namespaced_config_map(name=name, namespace=namespace)
            return {
                "kind": "ConfigMap",
                "name": name,
                "namespace": namespace,
                "status": "Ready",
                "message": "Present",
            }
        except ApiException as exc:
            if exc.status == 404:
                return self._missing_component_status("ConfigMap", namespace, name)
            return self._error_component_status("ConfigMap", namespace, name, str(exc))

    def _missing_component_status(self, kind, namespace, name):
        return {
            "kind": kind,
            "name": name,
            "namespace": namespace,
            "status": "Missing",
            "message": "Resource not found",
        }

    def _error_component_status(self, kind, namespace, name, detail):
        return {
            "kind": kind,
            "name": name,
            "namespace": namespace,
            "status": "Error",
            "message": detail,
        }

    def discover_workloads(self, namespace, app_name=None, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        apps = client.AppsV1Api()
        label_selector = ""
        if app_name:
            label_selector = f"pipeline.app={app_name}"

        deployments = apps.list_namespaced_deployment(
            namespace=namespace,
            label_selector=label_selector,
        ).items
        stateful_sets = apps.list_namespaced_stateful_set(
            namespace=namespace,
            label_selector=label_selector,
        ).items

        result = []
        for dep in deployments:
            result.append(
                {
                    "kind": "Deployment",
                    "name": dep.metadata.name,
                    "replicas": dep.spec.replicas,
                    "ready": dep.status.ready_replicas or 0,
                }
            )

        for sts in stateful_sets:
            result.append(
                {
                    "kind": "StatefulSet",
                    "name": sts.metadata.name,
                    "replicas": sts.spec.replicas,
                    "ready": sts.status.ready_replicas or 0,
                }
            )

        return result

    def scale_workload(self, namespace, kind, name, replicas, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        apps = client.AppsV1Api()
        body = {"spec": {"replicas": replicas}}
        if kind == "Deployment":
            apps.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=body)
        elif kind == "StatefulSet":
            apps.patch_namespaced_stateful_set_scale(name=name, namespace=namespace, body=body)
        else:
            raise ValueError("Only Deployment and StatefulSet scaling are supported.")

    def namespace_workloads(self, namespace, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        apps_api = client.AppsV1Api()
        core_api = client.CoreV1Api()

        deployments = apps_api.list_namespaced_deployment(namespace=namespace).items
        stateful_sets = apps_api.list_namespaced_stateful_set(namespace=namespace).items
        pods = core_api.list_namespaced_pod(namespace=namespace).items

        def deployment_row(dep):
            spec_replicas = dep.spec.replicas or 0
            ready = dep.status.ready_replicas or 0
            return {
                "name": dep.metadata.name,
                "desired": spec_replicas,
                "ready": ready,
                "available": dep.status.available_replicas or 0,
            }

        def stateful_set_row(sts):
            spec_replicas = sts.spec.replicas or 0
            ready = sts.status.ready_replicas or 0
            return {
                "name": sts.metadata.name,
                "desired": spec_replicas,
                "ready": ready,
                "current": sts.status.current_replicas or 0,
            }

        def pod_row(pod):
            phase = pod.status.phase or "Unknown"
            ready_containers = sum(
                1
                for cs in (pod.status.container_statuses or [])
                if cs.ready
            )
            total_containers = len(pod.spec.containers or [])
            restarts = sum(
                cs.restart_count or 0
                for cs in (pod.status.container_statuses or [])
            )
            containers = [c.name for c in (pod.spec.containers or [])]
            return {
                "name": pod.metadata.name,
                "phase": phase,
                "ready": f"{ready_containers}/{total_containers}",
                "restarts": restarts,
                "node": pod.spec.node_name or "",
                "containers": containers,
            }

        workloads = []
        for dep in deployments:
            row = deployment_row(dep)
            row["kind"] = "Deployment"
            workloads.append(row)
        for sts in stateful_sets:
            row = stateful_set_row(sts)
            row["kind"] = "StatefulSet"
            workloads.append(row)

        events = core_api.list_namespaced_event(namespace=namespace).items

        def event_row(ev):
            return {
                "type": ev.type or "",
                "reason": ev.reason or "",
                "object": ev.involved_object.name if ev.involved_object else "",
                "message": ev.message or "",
                "last_seen": str(ev.last_timestamp or ev.event_time or ""),
            }

        return {
            "workloads": workloads,
            "pods": [pod_row(p) for p in pods],
            "events": [event_row(e) for e in events],
        }

    def pod_logs(self, namespace, pod_name, container_name, kubeconfig_text=None, tail_lines=200):
        self.configure(kubeconfig_text=kubeconfig_text)
        core_api = client.CoreV1Api()
        try:
            raw = core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                tail_lines=tail_lines,
            )
            if isinstance(raw, (bytes, bytearray)):
                text = raw.decode("utf-8", errors="replace")
            else:
                text = str(raw)

            # Handle the case where the client returned bytes repr: b'...'
            for quote in ('"', "'"):
                if text.startswith("b" + quote) and text.endswith(quote):
                    text = text[2:-1]
                    text = (
                        text.replace("\\n", "\n")
                            .replace("\\t", "\t")
                            .replace("\\'", "'")
                            .replace('\\"', '"')
                            .replace("\\\\", "\\")
                    )
                    break

            # Normalise escaped newlines from some API response formats.
            if "\\n" in text and "\n" not in text:
                text = text.replace("\\n", "\n")

            return text
        except Exception as exc:
            return f"Unable to retrieve logs: {exc}"

    def resource_yaml(self, kind, namespace, name, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)

        kind_name = (kind or "").strip()
        if kind_name == "Deployment":
            api = client.AppsV1Api()
            obj = api.read_namespaced_deployment(name=name, namespace=namespace)
        elif kind_name == "StatefulSet":
            api = client.AppsV1Api()
            obj = api.read_namespaced_stateful_set(name=name, namespace=namespace)
        elif kind_name == "Service":
            api = client.CoreV1Api()
            obj = api.read_namespaced_service(name=name, namespace=namespace)
        elif kind_name == "ConfigMap":
            api = client.CoreV1Api()
            obj = api.read_namespaced_config_map(name=name, namespace=namespace)
        elif kind_name == "Namespace":
            api = client.CoreV1Api()
            obj = api.read_namespace(name=name)
        else:
            raise ValueError(f"Unsupported resource kind: {kind_name}")

        return yaml.safe_dump(obj.to_dict(), sort_keys=True)

    def pod_yaml(self, namespace, pod_name, kubeconfig_text=None):
        self.configure(kubeconfig_text=kubeconfig_text)
        core_api = client.CoreV1Api()
        pod = core_api.read_namespaced_pod(name=pod_name, namespace=namespace)
        return yaml.safe_dump(pod.to_dict(), sort_keys=True)

    def check_namespace_access(self, namespace, kubeconfig_text=None, timeout_seconds=3):
        try:
            self.configure(kubeconfig_text=kubeconfig_text)
            core = client.CoreV1Api()

            # Verifies both namespace visibility and namespaced read permissions.
            request_timeout = (timeout_seconds, timeout_seconds)
            core.read_namespace(name=namespace, _request_timeout=request_timeout)
            core.list_namespaced_pod(
                namespace=namespace,
                limit=1,
                _request_timeout=request_timeout,
            )
            return True, "Connection healthy"
        except Exception as exc:
            return False, str(exc)
