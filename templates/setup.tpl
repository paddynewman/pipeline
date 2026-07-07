% rebase("layout.tpl")

<section class="panel auth-panel">
  <h1>First-Time Setup</h1>
  <p class="muted">Create the first Pipeline user account to enable console access.</p>

  % if error:
    <p class="error-text">{{error}}</p>
  % end

  <form action="/setup" method="post" class="form">
    <label>
      Username
      <input name="username" autocomplete="username" required />
    </label>
    <label>
      Password
      <input type="password" name="password" autocomplete="new-password" required />
    </label>
    <label>
      Confirm Password
      <input type="password" name="confirm_password" autocomplete="new-password" required />
    </label>
    <button class="button" type="submit">Create First User</button>
  </form>
</section>
