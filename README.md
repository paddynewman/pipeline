# Pipeline

Pipeline is a lightweight CI/CD console for Kubernetes workloads.
It provides a web dashboard for managing applications, environments,
templated deployments, and operational actions.

## Features

- Dashboard listing applications, labels, and state hints.
- Application model with:
	- Description
	- Labels (name, value, description)
	- Base templates (inline Kubernetes YAML)
	- Base template variable defaults (YAML mapping)
	- Namespace configurations (name, description, labels, kubeconfig)
	- Environments (namespace plus instance-level variable overrides)
- Promotion checks for missing template variables.
- Deployment flow using Bottle template rendering and Kubernetes API apply logic.
- Runtime view with workloads, warning events, logs, and namespace metadata.
- Application-scoped operations section for workload discovery and scaling using configured namespaces.
- Username/password login required for all console pages.
- Local JSON-backed configuration in `data/*.json` with sorted keys and indentation.

Application configurations are stored per app under:

- `data/<application-name>/application.json`

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Start

Simple start command:

```bash
python run.py
```

Alternative module start:

```bash
python -m pipeline
```

Server defaults:

- Host: `0.0.0.0`
- Port: `8080`

Optional environment variables:

- `PIPELINE_HOST`
- `PIPELINE_PORT`
- `PIPELINE_DEBUG=true|false`
- `PIPELINE_COOKIE_SECRET` (set this in non-dev environments)
- `PIPELINE_COOKIE_SECURE=true|false` (set to `true` behind HTTPS)

## Authentication

- Users must log in to access the console.
- User credentials are stored in `data/users.json` with PBKDF2 password hashes.
- On first startup, if no users exist, Pipeline redirects to a first-time setup page to create the initial user.
- Additional users can be created, removed, and have passwords reset from Settings.

## Templates

Create Bottle-based YAML templates in `templates/`.
Example `templates/my-app.yaml.tpl`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
	name: my-app
spec:
	replicas: {{replicas}}
	selector:
		matchLabels:
			app: my-app
	template:
		metadata:
			labels:
				app: my-app
		spec:
			containers:
			- name: my-app
				image: {{image}}
```

Configure templates from the application detail page using Template Config:

- Application configuration owns templates and default variables.
- Environment configuration owns only overrides:
	- `variable_overrides`: override default template variable values for one environment.

Deployments render templates with the merged context:

- `effective_variables = application.variables + environment.variable_overrides`

## Namespace Configuration

- Add namespaces per application from the application detail page.
- Edit existing namespace configuration from the application detail page.
- Namespace forms require:
	- Namespace name
	- Description
	- Labels (name/value/description rows in the console)
	- Kubeconfig YAML (required)
- Deployments and runtime operations for an environment use the kubeconfig configured for that environment's namespace.

## Required Labels

- Required labels are configured in Settings.
- Each required label must include:
	- Name
	- Scope (`application` or `namespace`)
	- Description
- The description is shown on application and namespace forms wherever that label is required.

