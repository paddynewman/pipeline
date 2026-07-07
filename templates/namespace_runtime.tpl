% rebase("layout.tpl")

<section class="panel">
  <h1>{{namespace_item.get("name")}}</h1>
  <p>{{namespace_item.get("description") or "No description"}}</p>
  % if namespace_item.get("labels") or missing_required_namespace_labels:
    <div class="chips">
      % for label in namespace_item.get("labels", []):
        <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
      % end
      % for required in missing_required_namespace_labels:
        <span class="chip missing" title="{{required.get('description', '')}}">{{required.get("name")}}</span>
      % end
    </div>
  % end
</section>

% if cluster_error:
  <section class="panel error">
    <p class="error-text">{{cluster_error}}</p>
  </section>
% end

% if not cluster_error:
  <section class="panel">
    <h2>Resource Quotas</h2>
    % if namespace_quotas:
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Scopes</th>
            <th>Hard Limits</th>
          </tr>
        </thead>
        <tbody>
          % for item in namespace_quotas:
            <tr>
              <td>{{item.get("name")}}</td>
              <td>{{item.get("scopes")}}</td>
              <td>{{item.get("hard")}}</td>
            </tr>
          % end
        </tbody>
      </table>
    % else:
      <p class="muted">No resource quota definitions found.</p>
    % end
  </section>

  <section class="panel">
    <h2>RoleBinding Users</h2>
    % if namespace_rolebinding_users:
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>RoleBindings</th>
            <th>Roles</th>
          </tr>
        </thead>
        <tbody>
          % for item in namespace_rolebinding_users:
            <tr>
              <td>{{item.get("name")}}</td>
              <td>{{", ".join(item.get("role_bindings", [])) or "none"}}</td>
              <td>{{", ".join(item.get("roles", [])) or "none"}}</td>
            </tr>
          % end
        </tbody>
      </table>
    % else:
      <p class="muted">No users found in namespace RoleBindings.</p>
    % end
  </section>

  <section class="panel">
    <h2>Workloads</h2>
    % if workloads.get("workloads"):
      <table>
        <thead>
          <tr>
            <th>Kind</th>
            <th>Name</th>
            <th>Desired</th>
            <th>Ready</th>
          </tr>
        </thead>
        <tbody>
          % for item in workloads.get("workloads", []):
            <tr>
              <td>{{item.get("kind")}}</td>
              <td>{{item.get("name")}}</td>
              <td>{{item.get("desired")}}</td>
              <td>{{item.get("ready")}}</td>
            </tr>
          % end
        </tbody>
      </table>
    % else:
      <p class="muted">No workloads found.</p>
    % end
  </section>

  <section class="panel">
    <h2>Pods</h2>
    % if workloads.get("pods"):
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Containers</th>
            <th>Phase</th>
            <th>Ready</th>
            <th>Restarts</th>
          </tr>
        </thead>
        <tbody>
          % for item in workloads.get("pods", []):
            <tr>
              <td>{{item.get("name")}}</td>
              <td>
                % for container in item.get("containers", []):
                  <a href="/applications/{{app_item['name']}}/namespaces/{{namespace_item.get('name')}}/pods/{{item.get('name')}}/containers/{{container}}/logs">{{container}}</a>
                % end
              </td>
              <td>{{item.get("phase")}}</td>
              <td>{{item.get("ready")}}</td>
              <td>{{item.get("restarts")}}</td>
            </tr>
          % end
        </tbody>
      </table>
    % else:
      <p class="muted">No Pods found.</p>
    % end
  </section>

  <section class="panel">
    <h2>Events</h2>
    % if workloads.get("events"):
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Reason</th>
            <th>Object</th>
            <th>Message</th>
            <th>Last Seen</th>
          </tr>
        </thead>
        <tbody>
          % for item in workloads.get("events", []):
            <tr>
              <td>{{item.get("type")}}</td>
              <td>{{item.get("reason")}}</td>
              <td>{{item.get("object")}}</td>
              <td>{{item.get("message")}}</td>
              <td>{{item.get("last_seen")}}</td>
            </tr>
          % end
        </tbody>
      </table>
    % else:
      <p class="muted">No events found.</p>
    % end
  </section>
% end
