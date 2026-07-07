% rebase("layout.tpl")

<section class="panel">
  <h1>{{scope_label}}: {{secret_name}}</h1>
  <p class="muted">Edit key/value entries for this secret.</p>
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="panel">
  <form class="form label-editor secret-entry-editor" action="{{post_path}}" method="post" data-label-editor>
    <label>
      Secret Name
      <input name="secret_name" required value="{{secret_name}}" />
    </label>

    <div data-label-rows>
      % for key in sorted(entries.keys()):
        <div class="label-row" data-label-row>
          <label>
            Key
            <input name="secret_key" required value="{{key}}" />
          </label>
          <label>
            Value
            <textarea name="secret_value" required rows="3">{{entries.get(key)}}</textarea>
          </label>
          <button class="icon-button" type="button" data-remove-label-row aria-label="Remove entry">x</button>
        </div>
      % end
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
          <textarea name="secret_value" required rows="3"></textarea>
        </label>
        <button class="icon-button" type="button" data-remove-label-row aria-label="Remove entry">x</button>
      </div>
    </template>

    <div class="actions">
      <button class="button" type="submit">Save</button>
      <a class="button subtle" href="{{cancel_path}}">Cancel</a>
    </div>
  </form>
</section>
