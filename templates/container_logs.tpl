% rebase("layout.tpl")

<section class="panel">
  <h1>{{pod_name}} / {{container_name}}</h1>
  <p class="muted">Namespace: {{namespace_name}}</p>
</section>

<section class="panel">
  <h2>Recent Logs</h2>
  <pre>{{!logs or "No log output."}}</pre>
</section>
