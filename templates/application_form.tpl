% rebase("layout.tpl")

<section class="panel">
  <h1>{{"Edit" if app_item else "Create"}} Application</h1>
  <p class="muted">Define application details and labels.</p>
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
  <form id="application-form" action="{{submit_path}}" method="post" class="form">
    <label>
      Name
      <input name="name" value="{{(app_item or {}).get('name', '')}}" required />
    </label>

    <label>
      Description
      <textarea name="description" rows="2">{{(app_item or {}).get("description", "")}}</textarea>
    </label>

    <label>
      Labels
      <div class="label-editor" data-label-editor>
      % existing_labels = (app_item or {}).get("labels", [])
      % required_names = set([item.get("name") for item in required_application_labels])
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
          % for required_label in required_application_labels:
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

  </form>

  <hr class="section-divider" />
  <div class="actions">
    <button class="button" type="submit" form="application-form">Save Application</button>
    <a class="button subtle" href="{{cancel_path}}">Cancel</a>
    % if app_item:
      <form action="/applications/{{app_item.get('name')}}/delete" method="post" class="inline">
        <button class="button danger" type="submit">Delete Application</button>
      </form>
    % end
  </div>

</section>
