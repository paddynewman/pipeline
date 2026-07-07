# Pipeline

Pipeline is a CI/CD server for Kubernetes workloads. It's written in Python
using the Bottle framework and the kubernetes Python module.

## Design

- It has a web-based console which is similar to Jenkins and Spinnaker.
- Users configure applications, which are shown on a dashboard. This is the default landing page for the console.
  - The dashboard shows all the applications and some basic information about their type and state.
- Applications are templated Kubernetes configurations which are deployed to a namespace.
- Namespaces, and the credentials for them, are configured as part of the application.
- The templates are based on variables that are applied to Kubernetes YAML files using Bottle's templating feature.
- You can define as many templated YAML files as you like.
  - In the future, you'll also be able to source these from GitHub repositories.
- The templates use variables which are applied to Kubernetes YAML manifests during rendering.
- A combination of templates, variables and a namespace make up an environment for the application.
- Application can define promotion pathways so that they can promote e.g., from non-production through to production.
- The promotion pathways identify templates that refer to variables that have not been defined for an environment.
  - E.g., a missing database password.
- Users deploy applications to environments.
- When an application is deployed, you can view its live status, events, logs, etc through the console.
  - Warning events are shown in the console so that people can easily find and act on them.
- Meta data about the namespace, quotas, rolebindings etc, should all be visiable in the console.
- Basic operations commands can be performed through the console, like scaling up an down.
- You can view deloyed applications even if they weren't deployed by Pipeline, and still perform operational tasks on them.
- You can configure labels for applications, which can be used to help manage a service catalogue.
- Administrators can require that certain labels are supplied, to help with this.
- Labels have a name and a value, as well as a discription.
- Applications also have a description.

## Technical Considerations

- The console should be clean and simple and prioritise functionality over elaberate design.
  - It should still have a modern and consistent design, though.
- Users log in to the console using a username and password.
- All the Kubernetes interactions should be performed using the kubernetes Python module.
- Pipeline should support Google Kubernetes Engine (GKE) Kubernetes clusters.
- All configuration data for Pipeline should be stored in JSON files on the local filesytem.
- The JSON files should be indented for people to read easily, and their keys, etc should always be sorted.
- Don't use type annotations in the Python code.
- All Python code should be formatted using Black.
- There should be a simple start command for the Pipeline server so it's easy to run.
- Document the Python requirements (bottle, kubernetes) in a requirements.txt, but I will provide these.
- Don't use virtual environments. I'll provide the dependencies, so you shouldn't need to install anything else.