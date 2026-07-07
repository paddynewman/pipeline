% rebase("layout.tpl")

<section class="panel">
  <h1>Settings</h1>
  <p class="muted">Manage required labels.</p>
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="grid two">
  <article class="card">
    <h2>Required Labels</h2>
    <form class="form" action="/settings/labels" method="post">
      <label>
        Name
        <input name="name" required />
      </label>
      <label>
        Scope
        <select name="scope" required>
          <option value="application">Application</option>
          <option value="namespace">Namespace</option>
        </select>
      </label>
      <label>
        Description
        <input name="description" required />
      </label>
      <button class="button subtle add-action settings-add-button" type="submit">Add Label Rule</button>
    </form>

    % if edit_label:
      <form class="form spaced-actions" action="/settings/labels/update" method="post">
        <h3>Edit Label Rule</h3>
        <input type="hidden" name="current_name" value="{{edit_label.get('name')}}" />
        <input type="hidden" name="current_scope" value="{{edit_label.get('scope')}}" />
        <label>
          Name
          <input name="name" value="{{edit_label.get('name')}}" required />
        </label>
        <label>
          Scope
          <select name="scope" required>
            <option value="application" {{'selected' if edit_label.get('scope') == 'application' else ''}}>Application</option>
            <option value="namespace" {{'selected' if edit_label.get('scope') == 'namespace' else ''}}>Namespace</option>
          </select>
        </label>
        <label>
          Description
          <input name="description" value="{{edit_label.get('description', '')}}" required />
        </label>
        <div class="actions">
          <button class="button subtle" type="submit">Save Label Rule</button>
          <a class="button subtle" href="/settings">Cancel</a>
        </div>
      </form>
    % end

    % if required_labels:
      <div class="spaced-actions">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Scope</th>
            <th>Description</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          % for item in required_labels:
            <tr>
              <td>{{item.get("name")}}</td>
              <td>{{item.get("scope")}}</td>
              <td>{{item.get("description", "")}}</td>
              <td>
                <form class="inline" action="/settings" method="get">
                  <input type="hidden" name="edit_name" value="{{item.get('name')}}" />
                  <input type="hidden" name="edit_scope" value="{{item.get('scope')}}" />
                  <button class="button subtle" type="submit">Edit</button>
                </form>
                <form class="inline" action="/settings/labels/delete" method="post">
                  <input type="hidden" name="name" value="{{item.get('name')}}" />
                  <input type="hidden" name="scope" value="{{item.get('scope')}}" />
                  <button class="button subtle" type="submit">Remove</button>
                </form>
              </td>
            </tr>
          % end
        </tbody>
      </table>
      </div>
    % end
  </article>

</section>
