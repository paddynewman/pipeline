% rebase("layout.tpl")

<section class="panel">
  <h1>Environment Overrides: {{env_item.get("name")}}</h1>
  <p class="muted">Apply instance-level overrides for application template variables.</p>
</section>

% if errors:
  <section class="panel error">
    <h2>Validation Errors</h2>
    <ul>
      % for item in errors:
        <li>{{item}}</li>
      % end
    </ul>
  </section>
% end

<section class="panel">
  <form id="environment-configure-form" action="/applications/{{app_item.get('name')}}/environments/{{env_item.get('name')}}/configure" method="post" class="form">
    <label>
      Variable Overrides (YAML mapping)
      <textarea name="variable_overrides_yaml" rows="14" class="yaml-config-field">{{variable_overrides_yaml}}</textarea>
      <span class="field-note">Only include keys that should differ from the application defaults.</span>
    </label>

    <p class="field-note">Application templates configured: {{app_template_count}}</p>
  </form>

  <hr class="section-divider" />
  <div class="actions">
    <button class="button" type="submit" name="action" value="save" form="environment-configure-form">Save Configuration</button>
    <button class="button subtle" type="submit" name="action" value="render" form="environment-configure-form">Render Templates (Dry Run)</button>
    <a class="button subtle" href="/applications/{{app_item.get('name')}}">Cancel</a>
  </div>
</section>

% if rendered_templates:
  <section class="panel">
    <h2>Rendered Templates (Dry Run)</h2>
    <p class="muted">These results are rendered only and are not applied to Kubernetes.</p>
    % for item in rendered_templates:
      <h3>Template {{item.get("index")}}</h3>
      <pre>{{item.get("content", "")}}</pre>
    % end
  </section>
% end
