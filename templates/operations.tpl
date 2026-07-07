% rebase("layout.tpl")

<section class="panel">
  <h1>Operations</h1>
  <p class="muted">Inspect and manage workloads even if they were not deployed by Pipeline.</p>
  % if message:
    <p class="success">{{message}}</p>
  % end

  <form class="form inline-form" action="/operations" method="get">
    <label>
      Namespace
      <input name="namespace" value="{{namespace}}" />
    </label>
    <label>
      Application (optional)
      <input name="application" value="{{app_name}}" placeholder="pipeline app label" />
    </label>
    <button class="button" type="submit">Refresh</button>
  </form>

  % if error:
    <p class="error-text">{{error}}</p>
  % end
</section>

<section class="panel">
  <h2>Workloads</h2>
  % if not workloads:
    <p>No workloads found in namespace {{namespace}}.</p>
  % else:
    <table>
      <thead>
        <tr>
          <th>Kind</th>
          <th>Name</th>
          <th>Ready</th>
          <th>Replicas</th>
          <th>Scale</th>
        </tr>
      </thead>
      <tbody>
        % for item in workloads:
          <tr>
            <td>{{item.get("kind")}}</td>
            <td>{{item.get("name")}}</td>
            <td>{{item.get("ready")}}</td>
            <td>{{item.get("replicas")}}</td>
            <td>
              <form class="inline" action="/operations/scale" method="post">
                <input type="hidden" name="namespace" value="{{namespace}}" />
                <input type="hidden" name="kind" value="{{item.get('kind')}}" />
                <input type="hidden" name="name" value="{{item.get('name')}}" />
                <input type="number" name="replicas" min="0" value="{{item.get('replicas') or 0}}" />
                <button class="button subtle" type="submit">Apply</button>
              </form>
            </td>
          </tr>
        % end
      </tbody>
    </table>
  % end
</section>
