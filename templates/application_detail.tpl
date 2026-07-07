% rebase("layout.tpl")

<section class="panel">
  <div class="panel-title-row">
    <h1>{{app_item['name']}}</h1>
    <div class="actions">
      <a class="button subtle" href="/applications/{{app_item['name']}}/configure">Templates</a>
      <a class="button subtle" href="/applications/{{app_item['name']}}/secrets">Secrets</a>
      <a class="button" href="/applications/{{app_item['name']}}/edit">Edit</a>
    </div>
  </div>
  <p>{{app_item.get("description") or "No description"}}</p>
  % if app_item.get("labels"):
    <div class="chips">
      % for label in app_item.get("labels", []):
        <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
      % end
      % for required in app_missing_required_labels:
        <span class="chip missing" title="{{required.get('description', '')}}">{{required.get("name")}}</span>
      % end
    </div>
  % elif app_missing_required_labels:
    <div class="chips">
      % for required in app_missing_required_labels:
        <span class="chip missing" title="{{required.get('description', '')}}">{{required.get("name")}}</span>
      % end
    </div>
  % end
</section>

<section class="panel">
  <h2>Namespaces</h2>
  % if namespaces:
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Labels</th>
          <th>Label Rules</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        % for item in namespaces:
          <tr>
            <td>{{item.get("name")}}</td>
            <td>{{item.get("description", "")}}</td>
            <td>
              % namespace_missing = namespace_missing_required_labels.get(item.get("name"), [])
              % if item.get("labels") or namespace_missing:
                <div class="chips">
                  % for label in item.get("labels", []):
                    <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
                  % end
                  % for required in namespace_missing:
                    <span class="chip missing" title="{{required.get('description', '')}}">{{required.get("name")}}</span>
                  % end
                </div>
              % else:
                <span class="muted">none</span>
              % end
            </td>
            <td>
              % missing_required = namespace_missing_required_labels.get(item.get("name"), [])
              % if missing_required:
                <span class="health-pill unhealthy" title="Missing required namespace labels">{{len(missing_required)}} missing</span>
              % else:
                <span class="health-pill healthy">Complete</span>
              % end
            </td>
            <td>
              <div class="actions">
                <a class="button subtle" href="/applications/{{app_item['name']}}/namespaces/{{item.get('name')}}/edit">Edit</a>
                <a class="button subtle" href="/applications/{{app_item['name']}}/namespaces/{{item.get('name')}}/runtime">Runtime</a>
              </div>
            </td>
          </tr>
        % end
      </tbody>
    </table>
    <div class="actions spaced-actions">
      <a class="button subtle add-action" href="/applications/{{app_item['name']}}/namespaces/new">Add Namespace</a>
    </div>
  % else:
    <p>No namespaces configured yet.</p>
    <a class="button" href="/applications/{{app_item['name']}}/namespaces/new">Add first namespace</a>
  % end
</section>

<section class="panel">
  <h2>Environments</h2>
  % if environments:
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Release</th>
          <th>Namespace</th>
          <th>Overrides</th>
          <th>Labels</th>
          <th>Health</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        % for env in environments:
          <tr>
            <td>{{env.get("name")}}</td>
            <td>
              <span class="muted">#{{env.get("release", 0)}}</span>
            </td>
            <td>{{env.get("namespace", "")}}</td>
            <td>
              % variable_override_source = env.get("variable_overrides", None)
              % if variable_override_source is None:
                % variable_override_source = env.get("variables") or {}
              % end
              % variable_override_count = len(variable_override_source or {})
              % if variable_override_count:
                <span class="muted">vars: {{variable_override_count}}</span>
              % else:
                <span class="muted">none</span>
              % end
            </td>
            <td>
              % if env.get("labels"):
                <div class="chips">
                  % for label in env.get("labels", []):
                    <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
                  % end
                </div>
              % else:
                <span class="muted">none</span>
              % end
            </td>
            <td>
              % env_status = environment_health.get(env.get("name"), {})
              % if env_status.get("healthy"):
                <span class="health-pill healthy" title="{{env_status.get('detail', '')}}">Healthy</span>
              % else:
                <span class="health-pill unhealthy" title="{{env_status.get('detail', '')}}">Unhealthy</span>
              % end
            </td>
            <td>
              <div class="actions">
                <a class="button subtle" href="/applications/{{app_item['name']}}/environments/{{env.get('name')}}/edit">Edit</a>
                <a class="button subtle" href="/applications/{{app_item['name']}}/environments/{{env.get('name')}}/configure">Overrides</a>
                <a class="button subtle" href="/applications/{{app_item['name']}}/environments/{{env.get('name')}}/secrets">Secrets</a>
                <a class="button subtle" href="/applications/{{app_item['name']}}/environment/{{env.get('name')}}/runtime">Runtime</a>
                <form action="/applications/{{app_item['name']}}/deploy/{{env.get('name')}}" method="post" class="inline">
                  <button class="button" type="submit">Deploy</button>
                </form>
                <form action="/applications/{{app_item['name']}}/undeploy/{{env.get('name')}}" method="post" class="inline">
                  <button class="button subtle" type="submit">Undeploy</button>
                </form>
              </div>
            </td>
          </tr>
        % end
      </tbody>
    </table>
    <div class="actions spaced-actions">
      <a class="button subtle add-action" href="/applications/{{app_item['name']}}/environments/new">Add Environment</a>
    </div>
  % else:
    <p>No environments configured yet.</p>
    <a class="button" href="/applications/{{app_item['name']}}/environments/new">Add first environment</a>
  % end
</section>
