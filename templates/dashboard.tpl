% rebase("layout.tpl")

<section class="panel">
  <h1>Applications</h1>
</section>

% if not dashboard_items:
  <section class="panel">
    <p>No applications are configured yet.</p>
    <a class="button" href="/applications/new">Create your first application</a>
  </section>
% else:
  <section class="panel">
    <table>
      <thead>
        <tr>
          <th>Application</th>
          <th>Environments</th>
          <th>Description</th>
          <th>Labels</th>
          <th>Label Rules</th>
        </tr>
      </thead>
      <tbody>
        % for item in dashboard_items:
          <tr>
            <td><a href="/applications/{{item['name']}}">{{item["name"]}}</a></td>
            <td>{{item["environments"]}}</td>
            <td>{{item["description"] or "No description"}}</td>
            <td>
              % existing_labels = item.get("labels", [])
              % missing_labels = item.get("missing_required_app_labels", [])
              % if existing_labels or missing_labels:
                <div class="chips">
                  % for label in existing_labels:
                    <span class="chip" title="{{label.get('description', '')}}">{{label.get("name")}}={{label.get("value")}}</span>
                  % end
                  % for required in missing_labels:
                    <span class="chip missing" title="{{required.get('description', '')}}">{{required.get("name")}}</span>
                  % end
                </div>
              % else:
                <span class="muted">none</span>
              % end
            </td>
            <td>
              % label_status = item.get("required_label_status", {})
              % total_missing = label_status.get("total_missing", 0)
              % if total_missing:
                <span class="health-pill unhealthy" title="{{label_status.get('app_missing', 0)}} missing application labels, {{label_status.get('namespace_missing', 0)}} missing namespace labels">{{total_missing}} missing</span>
              % else:
                <span class="health-pill healthy">Complete</span>
              % end
            </td>
          </tr>
        % end
      </tbody>
    </table>
  </section>
% end
