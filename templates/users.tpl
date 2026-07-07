% rebase("layout.tpl")

<section class="panel">
  <h1>User Accounts</h1>
  <p class="muted">Manage console users from a single table.</p>
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="card">
  <div class="panel-title-row">
    <h2>Users</h2>
    <div class="actions">
      <a class="button" href="/accounts/new">Create User</a>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Username</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      % for item in users:
        % username = item.get("username")
        <tr>
          <td>{{username}}</td>
          <td>
            <div class="actions">
              <a class="button subtle" href="/accounts/{{username}}/edit">Edit</a>
            </div>
          </td>
        </tr>
      % end
    </tbody>
  </table>
</section>
