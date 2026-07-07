% rebase("layout.tpl")

<section class="panel">
  <h1>Runtime: {{app_item.get("name")}} / {{env.get("name")}}</h1>
  <p class="muted">Namespace: {{env.get("namespace", "default")}}</p>
  % if env.get("labels"):
    <div class="chips">
      % for label in env.get("labels", []):
        <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
      % end
    </div>
  % end
  % if message:
    <p class="success">{{message}}</p>
  % end
  % if cluster_error:
    <p class="error-text">Cluster error: {{cluster_error}}</p>
  % end
</section>

<section class="panel">
  <h2>Components</h2>
  % if component_statuses:
    <table>
      <thead>
        <tr>
          <th>Kind</th>
          <th>Name</th>
          <th>Namespace</th>
          <th>Status</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        % for item in component_statuses:
          <tr>
            <td>{{item.get("kind", "")}}</td>
            <td>
              <a href="/applications/{{app_item.get('name')}}/environment/{{env.get('name')}}/resources/{{item.get('kind', '')}}/{{item.get('name', '')}}/yaml?namespace={{item.get('namespace', '')}}">{{item.get("name", "")}}</a>
            </td>
            <td>{{item.get("namespace", "")}}</td>
            <td>{{item.get("status", "")}}</td>
            <td>{{item.get("message", "")}}</td>
          </tr>
        % end
      </tbody>
    </table>
  % else:
    <p>No runtime component status is available.</p>
  % end
</section>

<section class="panel">
  <h2>Pods</h2>
  % if pod_details:
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
        % for pod in pod_details:
          <tr>
            <td>
              <a href="/applications/{{app_item.get('name')}}/environment/{{env.get('name')}}/pods/{{pod.get('name', '')}}/yaml?namespace={{env.get('namespace', '')}}">{{pod.get("name", "")}}</a>
            </td>
            <td>
              % if pod.get("containers"):
                % for container in pod.get("containers", []):
                  <div>
                    <a href="/applications/{{app_item.get('name')}}/namespaces/{{pod.get('namespace', env.get('namespace', ''))}}/pods/{{pod.get('name', '')}}/containers/{{container}}/logs">{{container}}</a>
                  </div>
                % end
              % else:
                <span class="muted">none</span>
              % end
            </td>
            <td>{{pod.get("phase", "")}}</td>
            <td>{{pod.get("ready", "")}}</td>
            <td>{{pod.get("restarts", 0)}}</td>
          </tr>
        % end
      </tbody>
    </table>
  % else:
    <p>No related pods found.</p>
  % end
</section>

