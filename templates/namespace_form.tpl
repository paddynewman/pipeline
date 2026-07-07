% rebase("layout.tpl")

<section class="panel">
  <h1>{{page_title}} for {{app_item.get("name")}}</h1>
  <p class="muted">Namespaces require kubeconfig so Pipeline can authenticate with Kubernetes.</p>
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

% if test_message:
  <section class="panel">
    <p class="success">Namespace connection test passed: {{test_message}}</p>
  </section>
% end

% if test_error:
  <section class="panel error">
    <p class="error-text">Namespace connection test failed: {{test_error}}</p>
  </section>
% end

<section class="panel">
  <form id="namespace-form" action="{{submit_path}}" method="post" class="form">
    <label>
      Namespace Name
      <input name="name" value="{{namespace_item.get('name', '')}}" required />
    </label>

    <label>
      Description
      <textarea name="description" rows="2">{{namespace_item.get("description", "")}}</textarea>
    </label>

    <label>
      Labels
      <div class="label-editor" data-label-editor>
      % existing_labels = namespace_item.get("labels", [])
      % required_names = set([item.get("name") for item in required_namespace_labels])
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Value</th>
            <th>Description</th>
            <th></th>
          </tr>
        </thead>
        <tbody data-label-rows>
          % for required_label in required_namespace_labels:
            % current_value = ""
            % for existing_label in existing_labels:
              % if existing_label.get("name") == required_label.get("name"):
                % current_value = existing_label.get("value", "")
              % end
            % end
            <tr data-label-row>
              <td><input name="label_name" value="{{required_label.get('name', '')}}" readonly /></td>
              <td>
                <input name="label_value" value="{{current_value}}" required />
              </td>
              <td><input name="label_description" value="{{required_label.get('description', '')}}" readonly /></td>
              <td><span class="required-pill">Required</span></td>
            </tr>
          % end
          % for label in existing_labels:
            % if label.get("name") in required_names:
              % continue
            % end
            <tr data-label-row>
              <td><input name="label_name" value="{{label.get('name', '')}}" /></td>
              <td><input name="label_value" value="{{label.get('value', '')}}" /></td>
              <td><input name="label_description" value="{{label.get('description', '')}}" /></td>
              <td><button type="button" class="icon-button" data-remove-label-row aria-label="Remove label">×</button></td>
            </tr>
          % end
        </tbody>
      </table>
      <button type="button" class="button subtle add-action" data-add-label-row aria-label="Add label">Add Label</button>
      <template data-label-row-template>
        <tr data-label-row>
          <td><input name="label_name" /></td>
          <td><input name="label_value" /></td>
          <td><input name="label_description" /></td>
          <td><button type="button" class="icon-button" data-remove-label-row aria-label="Remove label">×</button></td>
        </tr>
      </template>
      </div>
    </label>

    <label>
      Kubeconfig (YAML)
      <textarea name="kubeconfig" rows="16" required>{{namespace_item.get("kubeconfig", "")}}</textarea>
    </label>
  </form>

  <hr class="section-divider" />
  <div class="actions">
    <button class="button" type="submit" name="action" value="save" form="namespace-form">{{submit_label}}</button>
    <button class="button subtle" type="submit" name="action" value="test" form="namespace-form">Test Connection</button>
    <a class="button subtle" href="/applications/{{app_item.get('name')}}">Cancel</a>
    % if namespace_item.get("name"):
      <form action="/applications/{{app_item.get('name')}}/namespaces/{{namespace_item.get('name')}}/delete" method="post" class="inline">
        <button class="button danger" type="submit">Delete Configuration</button>
      </form>
    % end
  </div>
</section>
