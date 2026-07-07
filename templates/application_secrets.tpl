% rebase("layout.tpl")

<section class="panel">
  <h1>Application Secrets: {{app_item.get("name")}}</h1>
  <p class="muted">Define named secrets and key/value entries. These become Kubernetes Secret objects per environment deploy.</p>
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="panel">
  <h2>Add Secret</h2>
  <form class="form label-editor secret-entry-editor" action="/applications/{{app_item.get('name')}}/secrets/add" method="post" data-label-editor>
    <label>
      Secret Name
      <input name="secret_name" required placeholder="db-credentials" />
      <span class="field-note">Use lowercase alphanumeric and hyphens only.</span>
    </label>

    <div data-label-rows>
      <div class="label-row" data-label-row>
        <label>
          Key
          <input name="secret_key" required placeholder="username" />
        </label>
        <label>
          Value
          <textarea name="secret_value" required rows="3" placeholder="password"></textarea>
        </label>
        <button class="icon-button" type="button" data-remove-label-row aria-label="Remove entry">x</button>
      </div>
    </div>

    <button type="button" class="button subtle add-action" data-add-label-row>Add Key/Value</button>
    <template data-label-row-template>
      <div class="label-row" data-label-row>
        <label>
          Key
          <input name="secret_key" required />
        </label>
        <label>
          Value
          <textarea name="secret_value" required rows="3" placeholder="password"></textarea>
        </label>
        <button class="icon-button" type="button" data-remove-label-row aria-label="Remove entry">x</button>
      </div>
    </template>

    <div class="actions">
      <button class="button" type="submit">Add Secret</button>
      <a class="button subtle" href="/applications/{{app_item.get('name')}}">Back to Application</a>
    </div>
  </form>
</section>

<section class="panel">
  <h2>Configured Secrets</h2>
  % if secret_sets:
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Keys</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        % for secret_name in sorted(secret_sets.keys()):
          % entries = secret_sets.get(secret_name, {})
          <tr>
            <td>{{secret_name}}</td>
            <td>{{", ".join(sorted(entries.keys()))}}</td>
            <td>
              <div class="actions">
                <a class="button subtle" href="/applications/{{app_item.get('name')}}/secrets/{{secret_name}}/edit">Edit</a>
                <form class="inline" method="post" action="/applications/{{app_item.get('name')}}/secrets/{{secret_name}}/delete">
                  <button class="button subtle" type="submit">Delete</button>
                </form>
              </div>
            </td>
          </tr>
        % end
      </tbody>
    </table>
  % else:
    <p class="muted">No application secrets configured.</p>
  % end
</section>
