% rebase("layout.tpl")

<section class="panel auth-panel">
  <h1>Sign In</h1>
  <p class="muted">Enter your username and password to access Pipeline.</p>

  % if error:
    <p class="error-text">{{error}}</p>
  % end

  <form action="/login" method="post" class="form">
    <input type="hidden" name="next" value="{{next_path}}" />
    <label>
      Username
      <input name="username" autocomplete="username" required />
    </label>
    <label>
      Password
      <input type="password" name="password" autocomplete="current-password" required />
    </label>
    <button class="button" type="submit">Log In</button>
  </form>
</section>
