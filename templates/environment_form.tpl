% rebase("layout.tpl")

<section class="panel">
  <h1>{{page_title}} for {{app_item.get("name")}}</h1>
  <p class="muted">Set environment identity, labels, and namespace.</p>
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
  <form id="environment-form" action="{{submit_path}}" method="post" class="form">
    <label>
      Environment Name
      <input name="name" value="{{env_item.get('name', '')}}" required />
    </label>

    <label>
      Description
      <textarea name="description" rows="2">{{env_item.get("description", "")}}</textarea>
    </label>

    <label>
      Namespace
      <select name="namespace" required>
        <option value="">Select namespace</option>
        % for namespace_item in namespaces:
          % namespace_name = namespace_item.get("name", "")
          <option value="{{namespace_name}}" {{"selected" if env_item.get("namespace", "") == namespace_name else ""}}>{{namespace_name}}</option>
        % end
      </select>
    </label>

    <label>
      Labels
      <div class="label-editor" data-label-editor>
      % existing_labels = env_item.get("labels", [])
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
          % for label in existing_labels:
            <tr data-label-row>
              <td><input name="label_name" value="{{label.get('name', '')}}" /></td>
              <td><input name="label_value" value="{{label.get('value', '')}}" /></td>
              <td><input name="label_description" value="{{label.get('description', '')}}" /></td>
              <td><button type="button" class="icon-button" data-remove-label-row aria-label="Remove label">x</button></td>
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
          <td><button type="button" class="icon-button" data-remove-label-row aria-label="Remove label">x</button></td>
        </tr>
      </template>
      </div>
    </label>
  </form>

  <hr class="section-divider" />
  <div class="actions">
    <button class="button" type="submit" form="environment-form">{{submit_label}}</button>
    <a class="button subtle" href="/applications/{{app_item.get('name')}}">Cancel</a>
    % if env_item.get("name"):
      <form action="/applications/{{app_item.get('name')}}/environments/{{env_item.get('name')}}/delete" method="post" class="inline">
        <button class="button danger" type="submit">Delete Environment</button>
      </form>
    % end
  </div>
</section>
