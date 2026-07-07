% rebase("layout.tpl")

<section class="panel">
  <h1>{{title}}</h1>
  <p class="muted">{{subtitle}}</p>
</section>

<section class="panel">
  <h2>YAML</h2>
  <pre>{{!yaml_text or "No YAML output."}}</pre>
</section>
