% rebase("layout.tpl")

<section class="panel">
  <h1>Configure Application: {{app_item.get("name")}}</h1>
  <p class="muted">Define base templates and default template variables for all environments.</p>
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
  <form id="application-configure-form" action="/applications/{{app_item.get('name')}}/configure" method="post" class="form">
    <label>
      Template Variable Defaults (YAML mapping)
      <textarea name="variables_yaml" rows="14" class="yaml-config-field">{{variables_yaml}}</textarea>
      <span class="field-note">Example: image: ghcr.io/org/app:1.0.0</span>
    </label>

    <label>
      Templates (Kubernetes YAML)
      <div class="template-editor" data-template-editor>
        <div class="template-editor-list" data-template-list>
          % for template_item in template_entries:
            <div class="template-editor-item" data-template-item>
              <div class="template-editor-meta">
                <span class="field-note">Template</span>
                <button type="button" class="icon-button" data-remove-template aria-label="Remove template">x</button>
              </div>
              <label>
                Template (Kubernetes YAML)
                <textarea name="template_text" rows="14" required class="yaml-config-field">{{template_item.get("content", "")}}</textarea>
              </label>
            </div>
          % end
        </div>
        <button type="button" class="button subtle add-action" data-add-template>Add Template</button>
        <template data-template-template>
          <div class="template-editor-item" data-template-item>
            <div class="template-editor-meta">
              <span class="field-note">Template</span>
              <button type="button" class="icon-button" data-remove-template aria-label="Remove template">x</button>
            </div>
            <label>
              Template (Kubernetes YAML)
              <textarea name="template_text" rows="14" required class="yaml-config-field"></textarea>
            </label>
          </div>
        </template>
      </div>
      <span class="field-note">These templates are shared by every environment in this application.</span>
    </label>
  </form>

  <hr class="section-divider" />
  <div class="actions">
    <button class="button" type="submit" name="action" value="save" form="application-configure-form">Save Configuration</button>
    <button class="button subtle" type="submit" name="action" value="render" form="application-configure-form">Render Templates (Dry Run)</button>
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

<script>
  (function () {
    var editors = document.querySelectorAll("[data-template-editor]");

    editors.forEach(function (editor) {
      var addButton = editor.querySelector("[data-add-template]");
      var list = editor.querySelector("[data-template-list]");
      var template = editor.querySelector("template[data-template-template]");

      if (!addButton || !list || !template) {
        return;
      }

      addButton.addEventListener("click", function () {
        var fragment = template.content.cloneNode(true);
        list.appendChild(fragment);
      });

      list.addEventListener("click", function (event) {
        var removeButton = event.target.closest("[data-remove-template]");
        if (!removeButton) {
          return;
        }

        var item = removeButton.closest("[data-template-item]");
        if (!item) {
          return;
        }

        if (list.querySelectorAll("[data-template-item]").length <= 1) {
          var textarea = item.querySelector("textarea[name='template_text']");
          if (textarea) {
            textarea.value = "";
          }
          if (textarea) {
            textarea.focus();
          }
          return;
        }

        item.remove();
      });
    });
  })();
</script>
