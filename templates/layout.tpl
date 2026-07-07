<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pipeline</title>
    <link rel="stylesheet" href="/static/style.css" />
  </head>
  <body>
    <header class="topbar">
      <div class="topbar-inner">
        <div class="topbar-left">
          <div class="brand-wrap">
            <div class="brand">PIPELINE</div>
          </div>
          % if current_user:
            <nav class="primary-nav primary-nav-left">
              <a href="/">Dashboard</a>
              <a href="/settings">Settings</a>
            </nav>
          % end
        </div>
        % if current_user:
        <nav class="primary-nav primary-nav-right">
          <a href="/applications/new" class="topbar-new-app-button">New Application</a>
          <details class="account-menu">
            <summary class="user-tag">{{current_user}}</summary>
            <div class="account-menu-panel">
              <div class="account-menu-label">Signed in as {{current_user}}</div>
              <div class="account-menu-meta">Pipeline {{app_version}}</div>
              <a class="account-menu-action" href="/accounts">Manage User Accounts</a>
              <a class="account-menu-action" href="/logout">Log Out</a>
            </div>
          </details>
        </nav>
        % end
      </div>
    </header>
    <main class="container">
      % if breadcrumbs:
        <nav class="breadcrumbs" aria-label="Breadcrumb">
          <ol>
            % for index, crumb in enumerate(breadcrumbs):
              <li>
                % if crumb.get("href") and index < len(breadcrumbs) - 1:
                  <a href="{{crumb.get('href')}}">{{crumb.get("label")}}</a>
                % else:
                  <span>{{crumb.get("label")}}</span>
                % end
              </li>
            % end
          </ol>
        </nav>
      % end
      {{!base}}
    </main>
    <script>
      (function () {
        var menus = document.querySelectorAll(".account-menu");

        function closeAll() {
          menus.forEach(function (menu) {
            menu.removeAttribute("open");
          });
        }

        document.addEventListener("click", function (event) {
          menus.forEach(function (menu) {
            if (!menu.hasAttribute("open")) {
              return;
            }
            if (!menu.contains(event.target)) {
              menu.removeAttribute("open");
            }
          });
        });

        document.addEventListener("keydown", function (event) {
          if (event.key === "Escape") {
            closeAll();
          }
        });

        function bindLabelEditors() {
          var editors = document.querySelectorAll("[data-label-editor]");

          editors.forEach(function (editor) {
            var addButton = editor.querySelector("[data-add-label-row]");
            var rowsContainer = editor.querySelector("[data-label-rows]");
            var template = editor.querySelector("template[data-label-row-template]");

            if (!addButton || !rowsContainer || !template) {
              return;
            }

            addButton.addEventListener("click", function () {
              var fragment = template.content.cloneNode(true);
              rowsContainer.appendChild(fragment);
            });

            rowsContainer.addEventListener("click", function (event) {
              var removeButton = event.target.closest("[data-remove-label-row]");
              if (!removeButton) {
                return;
              }
              var row = removeButton.closest("[data-label-row]");
              if (row) {
                row.remove();
              }
            });
          });
        }

        bindLabelEditors();
      })();
    </script>
  </body>
</html>
