% rebase("layout.tpl")

<section class="panel">
  <h1>{{page_title}}</h1>
  <p class="muted">{{page_subtitle}}</p>
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="card">
  <form class="form" action="{{submit_path}}" method="post">
    % if is_edit:
      <label>
        Username
        <input value="{{username}}" readonly />
      </label>
      <input type="hidden" name="username" value="{{username}}" />
    % else:
      <label>
        Username
        <input name="username" required autofocus />
      </label>
    % end

    <label>
      {{password_label}}
      <input type="password" name="password" required />
    </label>

    % if is_edit:
      <label>
        Confirm Password
        <input type="password" name="confirm_password" required />
      </label>
    % end

    <input type="hidden" name="redirect_to" value="{{redirect_to}}" />

    % if is_edit:
      <hr class="section-divider" />
    % end

    <div class="actions">
      <button class="button" type="submit">{{submit_label}}</button>
      <a class="button subtle" href="/accounts">Cancel</a>
      % if is_edit and username != current_user:
        <button class="button danger" type="submit" form="delete-user-form">Delete User</button>
      % end
    </div>
  </form>

  % if is_edit and username != current_user:
    <form id="delete-user-form" class="inline" action="/settings/users/delete" method="post">
      <input type="hidden" name="username" value="{{username}}" />
    </form>
  % end
</section>
