import html
import textwrap
import urllib.parse


def esc(s):
    return html.escape(str(s) if s is not None else "", quote=True)


def _html(block):
    return textwrap.dedent(block).strip()


_BRAND_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
    '<path d="M28 100L64 64L100 28" fill="none" stroke="#22c55e" stroke-width="8" stroke-linecap="round"/>'
    '<circle cx="28" cy="100" r="18" fill="#166534"/>'
    '<circle cx="64" cy="64" r="18" fill="#16a34a"/>'
    '<circle cx="100" cy="28" r="18" fill="#4ade80"/>'
    "</svg>"
)
_FAVICON_HREF = "data:image/svg+xml," + urllib.parse.quote(_BRAND_ICON_SVG)


_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; border-radius: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  font-size: 14px; line-height: 1.5; background: #f6f8fa; color: #24292f;
}
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }

/* Top bar */
.topbar {
  display: flex; align-items: center; height: 50px; padding: 0 20px;
  background: #24292f; gap: 16px; position: sticky; top: 0; z-index: 100;
}
.brand { font-size: 17px; font-weight: 700; color: #f0f6fc; text-decoration: none; letter-spacing: 1px; }
.brand:hover { text-decoration: none; color: #ffffff; }
.topnav a { color: #8b949e; text-decoration: none; font-size: 13px; padding: 4px 8px; border-radius: 0; }
.topnav a:hover { color: #f0f6fc; background: rgba(255,255,255,.08); text-decoration: none; }
.topbar-spacer { flex: 1; }
.user-menu { position: relative; display: inline-block; }
.user-menu-btn {
  background: none; border: 1px solid rgba(255,255,255,.2); border-radius: 0;
  color: #c9d1d9; font-size: 13px; padding: 4px 10px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
}
.user-menu-btn:hover { background: rgba(255,255,255,.08); color: #f0f6fc; }
.user-menu-btn::after { content: ''; display: inline-block; border-top: 4px solid currentColor; border-left: 4px solid transparent; border-right: 4px solid transparent; }
.user-dropdown {
  display: none; position: absolute; right: 0; top: calc(100% + 6px);
  background: #2d333b; border: 1px solid #444c56; border-radius: 0;
  min-width: 140px; box-shadow: 0 4px 12px rgba(0,0,0,.4); z-index: 200;
}
.user-dropdown a {
  display: block; padding: 8px 14px; color: #c9d1d9; font-size: 13px;
  text-decoration: none;
}
.user-dropdown a:hover { background: rgba(255,255,255,.06); color: #f0f6fc; text-decoration: none; }
.user-menu.open .user-dropdown { display: block; }

/* Container */
.container { width: 100%; margin: 0; padding: 24px 20px; }

/* Breadcrumb */
.breadcrumb { font-size: 13px; color: #57606a; margin-bottom: 18px; }
.breadcrumb a { color: #0969da; }
.breadcrumb a:hover { text-decoration: underline; }

/* Page header */
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h1 { font-size: 20px; font-weight: 600; }
.page-header .actions { display: flex; gap: 8px; }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 14px; border-radius: 0; font-size: 13px; font-weight: 500;
  cursor: pointer; border: 1px solid transparent; text-decoration: none;
  line-height: 20px; white-space: nowrap; vertical-align: middle;
}
.btn:hover { text-decoration: none; }
.btn-sm { padding: 3px 10px; font-size: 12px; }
.btn-primary { background: #0969da; color: white; border-color: rgba(0,0,0,.1); }
.btn-primary:hover { background: #0860ca; color: white; }
.btn-danger { background: #cf222e; color: white; border-color: rgba(0,0,0,.1); }
.btn-danger:hover { background: #c21a27; color: white; }
.btn-warning { background: #bf8700; color: white; border-color: rgba(0,0,0,.1); }
.btn-warning:hover { background: #a57800; color: white; }
.btn-secondary { background: #f6f8fa; color: #24292f; border-color: #d0d7de; }
.btn-secondary:hover { background: #e9ecef; }

/* Table */
.table-wrap { background: white; border: 1px solid #d0d7de; border-radius: 0; overflow: hidden; }
table { width: 100%; border-collapse: collapse; }
th {
  text-align: left; padding: 9px 14px; font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .4px; color: #57606a;
  background: #f6f8fa; border-bottom: 1px solid #d0d7de; white-space: nowrap;
}
td { padding: 10px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: #f6f8fa; }
.col-num { width: 70px; white-space: nowrap; }
.col-weather { width: 88px; }
.col-labels { width: 180px; }
.col-status { width: 120px; }
.col-dur { width: 90px; }
.col-time { width: 140px; }
.col-actions { width: 80px; text-align: right; }

.weather-cell { text-align: center; }

.weather {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 15px; font-weight: 600;
  border: none;
  background: none;
  padding: 0;
}
.weather-icon { font-size: 15px; line-height: 1; }
.weather-sunny,
.weather-partly-cloudy,
.weather-cloudy,
.weather-rainy,
.weather-stormy,
.weather-none {
  background: none;
  color: inherit;
  border: none;
}
.section-title-row {
  display: flex; align-items: center; gap: 8px; margin: 24px 0 12px;
}

/* Badges */
.badge {
  display: inline-block; padding: 2px 9px; border-radius: 0;
  font-size: 11px; font-weight: 600;
}
.badge-success { background: #dafbe1; color: #1a7f37; }
.badge-failure { background: #ffebe9; color: #a40e26; }
.badge-running { background: #ddf4ff; color: #0550ae; }
.badge-aborted { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
.badge-disabled { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; font-size: 13px; font-weight: 500; vertical-align: middle; margin-left: 8px; }

/* Job name in table */
.job-link { font-weight: 500; color: #0969da; font-size: 14px; }
.job-desc { font-size: 12px; color: #57606a; margin-top: 2px; }

/* Card */
.card {
  background: white; border: 1px solid #d0d7de; border-radius: 0;
  padding: 20px; margin-bottom: 16px;
}

/* Meta grid */
.meta-grid {
  display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 20px;
  background: white; border: 1px solid #d0d7de; border-radius: 0;
  padding: 16px 20px;
}
.meta-item {}
.meta-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; color: #57606a; }
.meta-value { font-size: 14px; margin-top: 3px; font-weight: 500; }

/* Log */
.log-panel {
  background: #e9ecef; border: 1px solid #d0d7de; border-radius: 0; overflow: hidden;
}
.log-panel-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 8px 12px; background: #f6f8fa; border-bottom: 1px solid #d0d7de;
}
.log-wrap {
  background: #e9ecef; border: none; border-radius: 0;
  padding: 16px; font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 12px; line-height: 1.7; color: #24292f; white-space: pre-wrap;
  word-break: break-all; max-height: 65vh; overflow-y: auto; min-height: 1.7em;
}
.log-sections { display: flex; flex-direction: column; gap: 16px; }
.log-section-title { font-size: 13px; font-weight: 600; color: #24292f; margin: 0; }
.log-section-heading { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.log-section-subtitle { font-size: 12px; color: #57606a; margin: 0; white-space: nowrap; }
.log-script-details {
  margin: 0; background: transparent; border: none; border-radius: 0;
}
.log-script-summary {
  display: flex; align-items: center; width: 100%; cursor: pointer;
  font-size: 13px; font-weight: 600; color: #24292f; list-style: none;
}
.log-script-summary::-webkit-details-marker { display: none; }
.log-script-summary::after {
  content: ''; display: inline-block; margin-left: auto; width: 0; height: 0;
  border-top: 4px solid transparent; border-bottom: 4px solid transparent;
  border-left: 6px solid #8c959f;
}
.log-script-details[open] .log-script-summary::after {
  transform: rotate(90deg); transform-origin: 65% 50%;
}
.log-script-body {
  border-top: 1px solid #d0d7de;
  background: #f6f8fa;
}
.log-script-meta {
  padding: 10px 12px 0; font-size: 12px; color: #57606a;
}
.log-script-wrap {
  margin: 0; background: #f6f8fa; border: none; border-bottom: 1px solid #d0d7de; border-radius: 0;
  padding: 12px; font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 12px; line-height: 1.7; color: #24292f; white-space: pre-wrap; overflow-x: auto;
}

/* Forms */
.form-card { background: white; border: 1px solid #d0d7de; border-radius: 0; padding: 24px; }
.form-section {
  padding-top: 20px; margin-top: 20px; border-top: 1px solid #d8dee4;
}
.form-section:first-of-type {
  padding-top: 0; margin-top: 0; border-top: none;
}
.form-section-title {
  font-size: 15px; font-weight: 600; color: #24292f; margin-bottom: 4px;
}
.form-section-hint {
  font-size: 12px; color: #57606a; margin-bottom: 16px;
}
.form-group { margin-bottom: 18px; }
label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 5px; color: #24292f; }
.hint { font-weight: normal; color: #57606a; font-size: 12px; margin-left: 4px; }
input[type=text], input[type=password], input[type=number], textarea, select {
  width: 100%; padding: 6px 12px; border: 1px solid #d0d7de; border-radius: 0;
  font-size: 14px; font-family: inherit; background: white; color: #24292f; line-height: 1.5;
}
input[type=text]:focus, input[type=password]:focus, input[type=number]:focus, textarea:focus, select:focus {
  outline: none; border-color: #0969da; box-shadow: 0 0 0 3px rgba(9,105,218,.1);
}
textarea { resize: vertical; }
textarea.code {
  font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace; font-size: 13px;
}
.form-actions { display: flex; gap: 8px; margin-top: 24px; padding-top: 18px; border-top: 1px solid #d0d7de; }

/* Params editor */
.params-editor { border: 1px solid #d0d7de; border-radius: 0; overflow: hidden; margin-top: 6px; }
.params-header {
  display: grid; grid-template-columns: 1fr 2fr 1fr 1.5fr 88px;
  gap: 8px; padding: 7px 10px; background: #f6f8fa;
  border-bottom: 1px solid #d0d7de; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .4px; color: #57606a;
}
.param-row {
  display: grid; grid-template-columns: 1fr 2fr 1fr 1.5fr 88px;
  gap: 8px; padding: 7px 10px; border-bottom: 1px solid #f0f0f0; align-items: center;
}
.param-row:last-child { border-bottom: none; }
.param-row input { margin: 0; font-size: 13px; padding: 4px 8px; }
.params-add { padding: 8px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de; }
.param-actions { display: flex; gap: 4px; justify-content: flex-end; }
.btn-param {
  background: #f6f8fa; border: 1px solid #d0d7de; color: #24292f; cursor: pointer;
  font-size: 12px; line-height: 1; padding: 5px 7px; border-radius: 0;
}
.btn-param:hover { background: #e9ecef; }
.btn-param:disabled { opacity: 0.5; cursor: default; }
.btn-rm { background: none; border: none; color: #cf222e; cursor: pointer; font-size: 18px; line-height: 1; padding: 0 2px; }
.btn-rm:hover { opacity: 0.7; }

/* Script sections editor */
.script-sections-editor { border: 1px solid #d0d7de; border-radius: 0; overflow: hidden; margin-top: 6px; }
.script-section {
  padding: 12px; border-bottom: 1px solid #f0f0f0; background: white;
}
.script-section:last-child { border-bottom: none; }
.script-section-top {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.script-section-name { flex: 1; margin: 0; }
.script-section-execution {
  margin-bottom: 10px; padding: 10px; border: 1px solid #d0d7de;
  border-radius: 0; background: #f6f8fa;
}
.script-section-exec-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px; margin-top: 8px;
}
.script-section-exec-grid label,
.script-section-execution label {
  display: block; margin-bottom: 4px; font-size: 12px; font-weight: 600; color: #57606a;
}
.script-section-execution select,
.script-section-execution input {
  margin: 0;
}
.script-section textarea { margin: 0; min-height: 140px; }
.script-sections-add, .steps-add { padding: 8px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de; }

/* Alert */
.alert { padding: 12px 16px; border-radius: 0; margin-bottom: 16px; font-size: 13px; }
.alert-danger { background: #ffebe9; border: 1px solid #ffcecb; color: #a40e26; }
.alert-warning { background: #fff8c5; border: 1px solid #e3b341; color: #7d4e00; }

/* Empty state */
.empty-state { text-align: center; padding: 60px 20px; color: #57606a; }
.empty-state p { font-size: 15px; }

/* Section title */
.section-title { font-size: 15px; font-weight: 600; margin: 24px 0 12px; }
.section-title-row .section-title { margin: 0; }

/* Labels */
.label-list { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.label-chip {
  display: inline-block; padding: 1px 8px; border-radius: 0;
  font-size: 11px; font-weight: 500; background: #ddf4ff; color: #0550ae;
  border: 1px solid #b6e3ff;
}
.dashboard-tabs {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;
}
.dashboard-tab {
  appearance: none; border: 1px solid #d0d7de; background: #ffffff; color: #57606a;
  border-radius: 0; padding: 6px 12px; font-size: 12px; font-weight: 600;
  cursor: pointer;
}
.dashboard-tab:hover {
  background: #f6f8fa; color: #24292f;
}
.dashboard-tab-active {
  background: #0969da; color: #ffffff; border-color: #0969da;
}

/* Trigger radio */
.trigger-options { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
.trigger-option { display: flex; align-items: center; gap: 8px; font-weight: normal; cursor: pointer; }
.trigger-option input[type=radio] { width: auto; cursor: pointer; }
.trigger-cron-row { margin-top: 8px; }


/* Parameters display in build */
.param-table { width: auto; }
.param-table td { padding: 4px 10px; }
.param-table td:first-child { font-weight: 500; color: #57606a; padding-left: 0; }
.param-table td:last-child { font-family: monospace; font-size: 13px; }

.text-muted { color: #57606a; }
.mr-2 { margin-right: 8px; }
.inline-form { display: inline; }

/* Credentials binding editor */
.cred-editor { border: 1px solid #d0d7de; border-radius: 0; overflow: hidden; margin-top: 6px; }
.cred-header {
  display: grid; grid-template-columns: 2fr 1fr 1fr 60px;
  gap: 8px; padding: 7px 10px; background: #f6f8fa;
  border-bottom: 1px solid #d0d7de; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .4px; color: #57606a;
}
.cred-row {
  display: grid; grid-template-columns: 2fr 1fr 1fr 60px;
  gap: 8px; padding: 7px 10px; border-bottom: 1px solid #f0f0f0; align-items: center;
}
.cred-row:last-child { border-bottom: none; }
.cred-row select, .cred-row input { margin: 0; font-size: 13px; padding: 4px 8px; }
.cred-add { padding: 8px 10px; background: #f6f8fa; border-top: 1px solid #d0d7de; }
"""

_TIMEAGO_JS = """
(function () {
  function timeAgo(iso) {
    if (!iso) return '\u2014';
    var d = new Date(iso.replace('T', ' '));
    var s = Math.floor((Date.now() - d.getTime()) / 1000);
    if (isNaN(s)) return iso;
    if (s < 5) return 'just now';
    if (s < 60) return s + 's ago';
    if (s < 3600) return Math.floor(s / 60) + 'm ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    return Math.floor(s / 86400) + 'd ago';
  }
  document.querySelectorAll('[data-time]').forEach(function (el) {
    el.title = el.getAttribute('data-time');
    el.textContent = timeAgo(el.getAttribute('data-time'));
  });
})();
"""

_BADGE_HTML = {
    "success": '<span class="badge badge-success">\u2713 Success</span>',
    "failure": '<span class="badge badge-failure">\u2717 Failure</span>',
    "running": '<span class="badge badge-running">\u29d7 Running</span>',
    "queued": '<span class="badge badge-aborted">\u23f3 Queued</span>',
    "aborted": '<span class="badge badge-aborted">\u25a0 Aborted</span>',
}

_PARAMS_EDITOR_JS = """
(function () {
  var hidden = document.getElementById('params-json');
  var editor = document.getElementById('params-editor');
  var addBtn = document.getElementById('add-param-btn');
  if (!hidden || !editor || !addBtn) return;

  function renderRows(params) {
    var rows = editor.querySelectorAll('.param-row');
    rows.forEach(function (r) { r.remove(); });
    params.forEach(function (p, i) {
      var row = document.createElement('div');
      row.className = 'param-row';
      var isFirst = i === 0;
      var isLast = i === params.length - 1;
      row.innerHTML =
        '<input type="text" placeholder="NAME" value="' + esc(p.name) + '" data-field="name" data-idx="' + i + '">' +
        '<input type="text" placeholder="Description" value="' + esc(p.description) + '" data-field="description" data-idx="' + i + '">' +
        '<input type="text" placeholder="Default" value="' + esc(p.default) + '" data-field="default" data-idx="' + i + '">' +
        '<input type="text" placeholder="Regex" value="' + esc(p.regex) + '" data-field="regex" data-idx="' + i + '">' +
        '<div class="param-actions">' +
        '<button type="button" class="btn-param btn-up" data-idx="' + i + '" title="Move up"' + (isFirst ? ' disabled' : '') + '>↑</button>' +
        '<button type="button" class="btn-param btn-down" data-idx="' + i + '" title="Move down"' + (isLast ? ' disabled' : '') + '>↓</button>' +
        '<button type="button" class="btn-rm" data-idx="' + i + '" title="Remove">&times;</button>' +
        '</div>';
      editor.insertBefore(row, editor.querySelector('.params-add'));
    });
  }

  function esc(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }

  function getParams() {
    try { return JSON.parse(hidden.value) || []; } catch (e) { return []; }
  }

  function saveParams() {
    var params = [];
    editor.querySelectorAll('.param-row').forEach(function (row) {
      var name = row.querySelector('[data-field="name"]').value.trim();
      var desc = row.querySelector('[data-field="description"]').value.trim();
      var def = row.querySelector('[data-field="default"]').value;
      var regex = row.querySelector('[data-field="regex"]').value.trim();
      if (name) params.push({ name: name, description: desc, default: def, regex: regex });
    });
    hidden.value = JSON.stringify(params);
  }

  function moveParam(index, delta) {
    saveParams();
    var params = getParams();
    var nextIndex = index + delta;
    if (nextIndex < 0 || nextIndex >= params.length) return;
    var current = params[index];
    params[index] = params[nextIndex];
    params[nextIndex] = current;
    hidden.value = JSON.stringify(params);
    renderRows(params);
  }

  renderRows(getParams());

  editor.addEventListener('input', saveParams);
  editor.addEventListener('click', function (e) {
    var button = e.target.closest('button');
    if (!button) return;
    if (button.classList.contains('btn-up')) {
      moveParam(parseInt(button.getAttribute('data-idx'), 10), -1);
      return;
    }
    if (button.classList.contains('btn-down')) {
      moveParam(parseInt(button.getAttribute('data-idx'), 10), 1);
      return;
    }
    if (button.classList.contains('btn-rm')) {
      button.closest('.param-row').remove();
      saveParams();
    }
  });

  addBtn.addEventListener('click', function () {
    var params = getParams();
    params.push({ name: '', description: '', default: '', regex: '' });
    hidden.value = JSON.stringify(params);
    renderRows(params);
  });
})();
"""

_STEPS_EDITOR_JS = """
(function () {
  var hidden = document.getElementById('steps-json');
  var editor = document.getElementById('steps-editor');
  var addBtn = document.getElementById('add-step-btn');
  var availableCreds = window._pipelineAvailableCreds || [];
  if (!hidden || !editor || !addBtn) return;

  function esc(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }

  function escText(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
  }

  function getSections() {
    try { return JSON.parse(hidden.value) || []; } catch (e) { return []; }
  }

  function normalizeStep(section) {
    var image = (section && section.image) || '';
    if (!image && section && section.execution) {
      image = section.execution.image || '';
    }
    return {
      name: (section && section.name) || '',
      script: (section && section.script) || '',
      image: image || '',
      reuse_container: !!(section && section.reuse_container)
    };
  }

  function saveSections() {
    var sections = [];
    var rows = Array.from(editor.querySelectorAll('.script-section'));
    rows.forEach(function (section, i) {
      var name = section.querySelector('[data-field="name"]').value.trim();
      var script = section.querySelector('[data-field="script"]').value;
      var imageEl = section.querySelector('[data-field="docker-image"]');
      var image = imageEl ? imageEl.value.trim() : '';
      var reuseEl = section.querySelector('[data-field="reuse-container"]');
      var reuse = reuseEl ? reuseEl.checked : false;
      if (reuse && i > 0) {
        var prevImage = rows[i - 1].querySelector('[data-field="docker-image"]');
        if (prevImage) image = prevImage.value.trim();
      }
      if (name || script) {
        sections.push({
          name: name || ('Script ' + (sections.length + 1)),
          script: script,
          image: image,
          reuse_container: reuse
        });
      }
    });
    if (!sections.length) sections.push({ name: 'Script 1', script: '', image: '', reuse_container: false });
    hidden.value = JSON.stringify(sections);
  }

  function updateReuseState(row) {
    var reuseEl = row.querySelector('[data-field="reuse-container"]');
    var imageEl = row.querySelector('[data-field="docker-image"]');
    if (!reuseEl || !imageEl) return;
    var reuse = reuseEl.checked;
    if (reuse) {
      var rows = Array.from(editor.querySelectorAll('.script-section'));
      var idx = rows.indexOf(row);
      if (idx > 0) {
        var prevImage = rows[idx - 1].querySelector('[data-field="docker-image"]');
        if (prevImage) imageEl.value = prevImage.value;
      }
      imageEl.disabled = true;
      imageEl.style.opacity = '0.6';
    } else {
      imageEl.disabled = false;
      imageEl.style.opacity = '';
    }
  }

  function syncAllReuseRows() {
    editor.querySelectorAll('.script-section').forEach(function (row) {
      updateReuseState(row);
    });
  }

  function renderSections(sections) {
    var rows = editor.querySelectorAll('.script-section');
    rows.forEach(function (r) { r.remove(); });
    if (!sections.length) sections = [{ name: 'Script 1', script: '', image: '' }];
    sections.forEach(function (section, i) {
      var step = normalizeStep(section);
      var row = document.createElement('div');
      var isFirst = i === 0;
      var isLast = i === sections.length - 1;
      row.className = 'script-section';
      var reuseColumnHtml = isFirst ?
        '<div style="width: 280px; min-width: 280px;"></div>' :
        '<div style="width: 280px; min-width: 280px;">' +
        '<label style="display:flex;align-items:center;gap:6px;margin-bottom:4px;font-size:12px;font-weight:600;color:#57606a">Or reuse the previous container <span title="Uses the container from the previous step, including all filesystem and authentication state." style="display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border:1px solid #8c959f;border-radius:50%;font-size:10px;line-height:1;cursor:help;">i</span></label>' +
        '<div style="height:32px;display:flex;align-items:center;">' +
        '<input type="checkbox" data-field="reuse-container"' + (step.reuse_container ? ' checked' : '') + ' style="cursor:pointer;">' +
        '</div>' +
        '</div>';
      row.innerHTML =
        '<div class="script-section-top" style="display: flex; gap: 16px; align-items: flex-end;">' +
        '<div style="flex: 1; min-width: 300px;">' +
        '<label style="display:block;margin-bottom:4px;font-size:12px;font-weight:600;color:#57606a">Name</label>' +
        '<input type="text" class="script-section-name" placeholder="Section name" value="' + esc(step.name) + '" data-field="name" style="width:100%">' +
        '</div>' +
        '<div style="flex: 1; min-width: 300px;">' +
        '<label style="display:block;margin-bottom:4px;font-size:12px;font-weight:600;color:#57606a">Docker Image</label>' +
        '<input type="text" placeholder="alpine:latest" value="' + esc(step.image) + '" data-field="docker-image" style="width:100%">' +
        '</div>' +
        reuseColumnHtml +
        '<div class="param-actions" style="align-self:center;">' +
        '<button type="button" class="btn-param btn-section-up" data-idx="' + i + '" title="Move up"' + (isFirst ? ' disabled' : '') + '>↑</button>' +
        '<button type="button" class="btn-param btn-section-down" data-idx="' + i + '" title="Move down"' + (isLast ? ' disabled' : '') + '>↓</button>' +
        '<button type="button" class="btn-rm btn-section-rm" data-idx="' + i + '" title="Remove">&times;</button>' +
        '</div>' +
        '</div>' +
        '<textarea class="code" rows="5" placeholder="#!/bin/sh&#10;set -eu&#10;echo Hello" data-field="script" style="margin-top:10px">' + escText(step.script) + '</textarea>';
      editor.insertBefore(row, editor.querySelector('.steps-add'));
      updateReuseState(row);
    });
  }

  function moveSection(index, delta) {
    saveSections();
    var sections = getSections();
    var nextIndex = index + delta;
    if (nextIndex < 0 || nextIndex >= sections.length) return;
    var current = sections[index];
    sections[index] = sections[nextIndex];
    sections[nextIndex] = current;
    hidden.value = JSON.stringify(sections);
    renderSections(sections);
  }

  renderSections(getSections());

  editor.addEventListener('input', function () {
    syncAllReuseRows();
    saveSections();
  });
  editor.addEventListener('change', function (e) {
    var reuse = e.target.closest('[data-field="reuse-container"]');
    if (!reuse) return;
    var row = reuse.closest('.script-section');
    if (row) updateReuseState(row);
    saveSections();
  });
  editor.addEventListener('click', function (e) {
    var button = e.target.closest('button');
    if (!button) return;
    if (button.classList.contains('btn-section-up')) {
      moveSection(parseInt(button.getAttribute('data-idx'), 10), -1);
      return;
    }
    if (button.classList.contains('btn-section-down')) {
      moveSection(parseInt(button.getAttribute('data-idx'), 10), 1);
      return;
    }
    if (button.classList.contains('btn-section-rm')) {
      button.closest('.script-section').remove();
      saveSections();
      renderSections(getSections());
    }
  });

  addBtn.addEventListener('click', function () {
    saveSections();
    var sections = getSections();
    sections.push({ name: 'Script ' + (sections.length + 1), script: '', image: '', reuse_container: false });
    hidden.value = JSON.stringify(sections);
    renderSections(sections);
  });
})();
"""

_CREDENTIALS_EDITOR_JS = """
(function () {
  var hidden = document.getElementById('credentials-json');
  var editor = document.getElementById('cred-editor');
  var addBtn = document.getElementById('add-cred-btn');
  var availableCreds = window._pipelineAvailableCreds || [];
  if (!hidden || !editor || !addBtn) return;

  function esc(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
  }

  function getBindings() {
    try { return JSON.parse(hidden.value) || []; } catch (e) { return []; }
  }

  function renderRows(bindings) {
    editor.querySelectorAll('.cred-row').forEach(function (r) { r.remove(); });
    bindings.forEach(function (b, i) {
      var row = document.createElement('div');
      row.className = 'cred-row';
      var credOptions = availableCreds.map(function (c) {
        return '<option value="' + esc(c) + '"' + (b.credential === c ? ' selected' : '') + '>' + esc(c) + '</option>';
      }).join('');
      row.innerHTML =
        '<select data-field="credential" data-idx="' + i + '">' + credOptions + '</select>' +
        '<input type="text" placeholder="ENV_VAR" value="' + esc(b.env_var) + '" data-field="env_var" data-idx="' + i + '">' +
        '<select data-field="type" data-idx="' + i + '">' +
        '<option value="value"' + (b.type !== 'file' ? ' selected' : '') + '>Value</option>' +
        '<option value="file"' + (b.type === 'file' ? ' selected' : '') + '>File path</option>' +
        '</select>' +
        '<div class="param-actions"><button type="button" class="btn-rm" data-idx="' + i + '" title="Remove">&times;</button></div>';
      editor.insertBefore(row, editor.querySelector('.cred-add'));
    });
  }

  function saveBindings() {
    var bindings = [];
    editor.querySelectorAll('.cred-row').forEach(function (row) {
      var credential = row.querySelector('[data-field="credential"]').value;
      var env_var = row.querySelector('[data-field="env_var"]').value.trim();
      var type = row.querySelector('[data-field="type"]').value;
      if (credential && env_var) bindings.push({ credential: credential, env_var: env_var, type: type });
    });
    hidden.value = JSON.stringify(bindings);
  }

  renderRows(getBindings());

  editor.addEventListener('input', saveBindings);
  editor.addEventListener('change', saveBindings);
  editor.addEventListener('click', function (e) {
    var button = e.target.closest('button');
    if (!button) return;
    if (button.classList.contains('btn-rm')) {
      button.closest('.cred-row').remove();
      saveBindings();
    }
  });

  addBtn.addEventListener('click', function () {
    var bindings = getBindings();
    bindings.push({ credential: availableCreds[0] || '', env_var: '', type: 'value' });
    hidden.value = JSON.stringify(bindings);
    renderRows(bindings);
  });
})();
"""


from pipeline import __version__


def _permissions_for_role(role):
    role = role or "admin"
    return {
        "can_manage_jobs": role == "admin",
        "can_run_builds": role in ("admin", "user"),
        "can_view_workspaces": role in ("admin", "user", "viewer"),
        "can_clear_workspaces": role == "admin",
        "can_manage_credentials": role == "admin",
        "can_manage_settings": role == "admin",
        "can_manage_users": role == "admin",
        "can_change_own_password": role in ("admin", "user", "viewer"),
    }


def _page(title, body, extra_js="", username=None, role=None):
    permissions = _permissions_for_role(role)
    nav_links = ['<a href="/">Dashboard</a>']
    if permissions["can_manage_credentials"]:
        nav_links.append('<a href="/credentials">Credentials</a>')
    if permissions["can_manage_settings"]:
        nav_links.append('<a href="/settings">Settings</a>')
    nav_html = " ".join(nav_links)
    new_job_html = (
        '<a href="/jobs/new" class="btn btn-primary btn-sm">+ New Job</a>'
        if permissions["can_manage_jobs"]
        else ""
    )
    user_links = []
    if username and permissions["can_manage_users"]:
        user_links.append('<a href="/settings/users">Manage users</a>')
    elif username and permissions["can_change_own_password"]:
        user_links.append(
            f'<a href="/settings/users/{esc(username)}/password">Change password</a>'
        )
    user_links.append('<a href="/logout">Log out</a>')
    user_links.append(
        f'<div style="padding:8px 14px 4px 14px;color:#8b949e;font-size:12px;border-top:1px solid #2d333b;margin-top:6px;">Version {__version__}</div>'
    )
    user_html = (
        f"""
<div class="user-menu" id="userMenu">
  <button class="user-menu-btn" onclick="toggleUserMenu(event)">{esc(username)}</button>
  <div class="user-dropdown">
  {''.join(user_links)}
  </div>
</div>
"""
        if username
        else '<a href="/login" style="color:#8b949e;font-size:13px">Log in</a>'
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)} Pipeline</title>
  <link rel="icon" href="{_FAVICON_HREF}" type="image/svg+xml">
  <style>{_CSS}</style>
</head>
<body>
  <header class="topbar">
    <a href="/" class="brand">PIPELINE</a>
    <nav class="topnav">{nav_html}</nav>
    <span class="topbar-spacer"></span>
    {new_job_html}
    {user_html}
  </header>
  <main class="container">
    {body}
  </main>
  <script>
    function toggleUserMenu(e) {{
      e.stopPropagation();
      var m = document.getElementById("userMenu");
      m.classList.toggle("open");
    }}
    document.addEventListener("click", function () {{
      var m = document.getElementById("userMenu");
      if (m) m.classList.remove("open");
    }});
  </script>
  <script>{_TIMEAGO_JS}</script>
  {extra_js}
</body></html>
"""


def _badge(status):
    labels = {
        "success": ("badge-success", "\u2713 Success"),
        "failure": ("badge-failure", "\u2717 Failure"),
        "running": ("badge-running", "\u29d7 Running"),
        "queued": ("badge-aborted", "\u23f3 Queued"),
        "aborted": ("badge-aborted", "\u25a0 Aborted"),
    }
    cls, text = labels.get(status or "", ("badge-aborted", status or "\u2014"))
    return f'<span class="badge {cls}">{text}</span>'


def queue_paused_banner(queue_state):
    message = esc(queue_state.get("pause_message") or "Job queue is paused.")
    queued = int(queue_state.get("queued_count") or 0)
    running = int(queue_state.get("running_count") or 0)
    max_concurrent = int(queue_state.get("max_concurrent_jobs") or 1)
    summary = (
        f"Queue paused. {queued} waiting, {running} running "
        f"(limit: {max_concurrent})."
    )
    return (
        '<div class="alert alert-warning" style="margin-top:0">'
        f'<strong>{message}</strong><div style="margin-top:4px">{esc(summary)}</div>'
        "</div>"
    )


def _weather(weather, compact=False):
    labels = {
        "sunny": ("weather-sunny", "\u2600\ufe0f", "Stable"),
        "partly-cloudy": ("weather-partly-cloudy", "\u26c5", "Mostly stable"),
        "cloudy": ("weather-cloudy", "\u2601\ufe0f", "Mixed"),
        "rainy": ("weather-rainy", "\U0001f327\ufe0f", "Unstable"),
        "stormy": ("weather-stormy", "\u26c8\ufe0f", "Failing"),
    }
    if not weather:
        title = "No completed builds yet."
        content = (
            '<span class="weather-icon">-</span>'
            if compact
            else '<span class="weather-icon">-</span><span class="weather-label">No builds</span>'
        )
        return (
            f'<span class="weather weather-none" title="{esc(title)}">{content}</span>'
        )
    condition = weather.get("condition") or "cloudy"
    cls, icon, label = labels.get(condition, labels["cloudy"])
    successes = int(weather.get("successes", 0))
    total = int(weather.get("total", 0))
    score = int(weather.get("score", 0))
    title = (
        f"{label}: {successes}/{total} recent completed builds succeeded ({score}%)."
    )
    content = f'<span class="weather-icon">{icon}</span>'
    if not compact:
        content += f'<span class="weather-label">{esc(label)}</span>'
    return f'<span class="weather {cls}" title="{esc(title)}">{content}</span>'


def _fmt_duration(secs):
    if secs is None:
        return "\u2014"
    secs = float(secs)
    if secs < 60:
        return f"{secs:.1f}s"
    m = int(secs // 60)
    s = int(secs % 60)
    return f"{m}m {s}s"


def _breadcrumb(*items):
    parts = []
    for label, href in items:
        if href:
            parts.append(f'<a href="{esc(href)}">{esc(label)}</a>')
        else:
            parts.append(f"<span>{esc(label)}</span>")
    return '<nav class="breadcrumb">' + " &rsaquo; ".join(parts) + "</nav>"


# ── Pages ──────────────────────────────────────────────────────────────────────


def login_page(error=None):
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = f"""
<div style="max-width:360px;margin:80px auto">
  <div class="form-card">
    <h1 style="font-size:20px;font-weight:600;margin-bottom:20px">Sign in to Pipeline</h1>
    {error_html}
    <form method="POST" action="/login">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" autocomplete="username" autofocus required>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" autocomplete="current-password" required>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Sign in</button>
      </div>
    </form>
  </div>
</div>
"""
    return _page_bare("Sign in \u2014 Pipeline", body)


def setup_page(error=None):
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = f"""
<div style="max-width:400px;margin:80px auto">
  <div class="form-card">
    <h1 style="font-size:20px;font-weight:600;margin-bottom:6px">Create administrator account</h1>
    <p class="text-muted" style="margin-bottom:20px;font-size:13px">No users exist yet. Create the first account to get started.</p>
    {error_html}
    <form method="POST" action="/setup">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" autocomplete="username" autofocus required pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="administrator">
      </div>
      <div class="form-group">
        <label for="password">Password <span class="hint">(min 8 characters)</span></label>
        <input type="password" id="password" name="password" autocomplete="new-password" required minlength="8">
      </div>
      <div class="form-group">
        <label for="confirm">Confirm password</label>
        <input type="password" id="confirm" name="confirm" autocomplete="new-password" required>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary">Create account</button>
      </div>
    </form>
  </div>
</div>
"""
    return _page_bare("Setup \u2014 Pipeline", body)


def _page_bare(title, body):
    """Minimal page without the authenticated topbar, used for login/setup."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" href="{_FAVICON_HREF}" type="image/svg+xml">
  <style>{_CSS}</style>
</head>
<body>
  <main class="container">{body}</main>
</body>
</html>
"""


def dashboard(jobs, username=None, role=None):
    permissions = _permissions_for_role(role)
    can_manage_jobs = permissions["can_manage_jobs"]
    if not jobs:
        create_html = (
            '<a href="/jobs/new">Create your first job</a>' if can_manage_jobs else ""
        )
        empty_text = f"No jobs yet. {create_html}." if create_html else "No jobs yet."
        body = f"""
      <div class="page-header"><h1>Dashboard</h1></div>
      <div class="empty-state">
        <p>{empty_text}</p>
      </div>
      """
        return _page("Dashboard", body, username=username, role=role)

    all_labels = sorted({label for job in jobs for label in (job.get("labels") or [])})
    rows = []
    for job in jobs:
        lb = job.get("last_build")
        name = job["name"]
        labels = job.get("labels") or []
        label_key = "|" + "|".join(labels) + "|" if labels else ""
        labels_html = (
            (
                '<div class="label-list" style="margin-top:3px">'
                + "".join(
                    f'<span class="label-chip">{esc(label)}</span>' for label in labels
                )
                + "</div>"
            )
            if labels
            else ""
        )
        if lb:
            build_link = f'<a href="/jobs/{esc(name)}/builds/{esc(lb["id"])}"># {esc(lb["id"])}</a>'
            status_html = _badge(lb.get("status"))
            dur = esc(_fmt_duration(lb.get("duration")))
            started = lb.get("started_at") or lb.get("queued_at", "")
            time_html = f'<span data-time="{esc(started)}">{esc(started)}</span>'
        else:
            build_link = '<span class="text-muted">\u2014</span>'
            status_html = '<span class="text-muted">\u2014</span>'
            dur = "\u2014"
            time_html = "\u2014"
        desc = esc(job.get("description", ""))
        desc_html = f'<div class="job-desc">{desc}</div>' if desc else ""
        is_job_enabled = job.get("enabled", True)
        disabled_badge = (
            ' <span class="badge badge-disabled" style="font-size:11px">Disabled</span>'
            if not is_job_enabled
            else ""
        )
        labels_cell_html = labels_html or '<span class="text-muted">\u2014</span>'
        row_style = ' style="opacity:0.6"' if not is_job_enabled else ""
        rows.append(
            f"""
<tr data-labels="{esc(label_key)}"{row_style}>
  <td><a href="/jobs/{esc(name)}" class="job-link">{esc(name)}</a>{disabled_badge}{desc_html}</td>
  <td class="col-labels">{labels_cell_html}</td>
  <td class="col-num">{build_link}</td>
  <td class="col-time">{time_html}</td>
  <td class="col-dur">{dur}</td>
  <td class="col-status">{status_html}</td>
  <td class="col-weather weather-cell">{_weather(job.get("weather"), compact=True)}</td>
</tr>
"""
        )

    tabs = ""
    if all_labels:
        tab_buttons = [
            '<button type="button" class="dashboard-tab dashboard-tab-active" data-label="">All</button>'
        ]
        tab_buttons.extend(
            f'<button type="button" class="dashboard-tab" data-label="{esc(label)}">{esc(label)}</button>'
            for label in all_labels
        )
        tabs = (
            '<div class="dashboard-tabs" aria-label="Job label filters">'
            + "".join(tab_buttons)
            + "</div>"
        )

    table = f"""
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Job</th>
        <th class="col-labels">Labels</th>
        <th class="col-num">Last Build</th>
        <th class="col-time">Last Started</th>
        <th class="col-dur">Last Duration</th>
        <th class="col-status">Last Status</th>
        <th class="col-weather weather-cell">Stability</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>
"""
    body = '<div class="page-header"><h1>Dashboard</h1></div>' + tabs + table
    filter_js = """
      <script>
      (function() {
        var buttons = [].slice.call(document.querySelectorAll(".dashboard-tab"));
        var rows = [].slice.call(document.querySelectorAll("tbody tr[data-labels]"));
        if (!rows.length) {
          return;
        }
        function apply(label) {
          var token = label ? "|" + label + "|" : "";
          rows.forEach(function(row) {
            var labels = row.getAttribute("data-labels") || "";
            row.hidden = !!token && labels.indexOf(token) === -1;
          });
          buttons.forEach(function(button) {
            button.classList.toggle("dashboard-tab-active", (button.getAttribute("data-label") || "") === label);
          });
        }
        buttons.forEach(function(button) {
          button.addEventListener("click", function() {
            apply(button.getAttribute("data-label") || "");
          });
        });
      })();
      </script>
    """
    return _page("Dashboard", body, extra_js=filter_js, username=username, role=role)


def job_detail(job, builds, username=None, role=None):
    permissions = _permissions_for_role(role)
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, None))
    has_params = bool(job.get("parameters"))
    is_enabled = job.get("enabled", True)

    if not is_enabled:
        build_btn = '<button type="button" class="btn btn-primary" disabled title="Job is disabled" style="opacity:0.4;cursor:not-allowed">Build Now</button>'
    elif permissions["can_run_builds"] and has_params:
        build_btn = f'<a href="/jobs/{esc(name)}/build" class="btn btn-primary">Build with Parameters\u2026</a>'
    elif permissions["can_run_builds"]:
        build_btn = (
            f'<form class="inline-form" method="POST" action="/jobs/{esc(name)}/build">'
            '<button type="submit" class="btn btn-primary">Build Now</button>'
            "</form>"
        )
    else:
        build_btn = ""

    workspace_btn = (
        f'<a href="/jobs/{esc(name)}/workspace" class="btn btn-secondary">Workspace</a>'
        if permissions["can_view_workspaces"]
        else ""
    )
    edit_btn = (
        f'<a href="/jobs/{esc(name)}/edit" class="btn btn-secondary">Edit</a>'
        if permissions["can_manage_jobs"]
        else ""
    )
    delete_btn = (
        f'<form class="inline-form" method="POST" action="/jobs/{esc(name)}/delete" onsubmit="return confirm(\'Delete job {esc(name)}?\')">'
        '<button type="submit" class="btn btn-danger">Delete</button>'
        "</form>"
        if permissions["can_manage_jobs"]
        else ""
    )

    desc = esc(job.get("description", ""))
    desc_html = (
        f'<p class="text-muted" style="margin-top:6px">{desc}</p>' if desc else ""
    )
    labels = job.get("labels") or []
    labels_html = (
        (
            '<div class="label-list" style="margin-top:8px">'
            + "".join(
                f'<span class="label-chip">{esc(label)}</span>' for label in labels
            )
            + "</div>"
        )
        if labels
        else ""
    )
    header = f"""
<div class="page-header">
  <div>
    <h1>{esc(name)}{' <span class="badge badge-disabled">Disabled</span>' if not is_enabled else ''}</h1>
    {desc_html}{labels_html}
  </div>
  <div class="actions">
    {build_btn}
    {workspace_btn}
    {edit_btn}
    {delete_btn}
  </div>
</div>
"""

    if not builds:
        builds_html = '<div class="empty-state" style="padding:30px 0"><p>No builds yet.</p></div>'
    else:
        rows = []
        for b in reversed(builds):
            bid = b["id"]
            params = b.get("parameters") or {}
            params_str = (
                ", ".join(f"{k}={v}" for k, v in params.items()) if params else "\u2014"
            )
            started = b.get("started_at") or b.get("queued_at", "")
            tb = b.get("triggered_by") or ""
            if tb == "cron":
                triggered_html = '<span class="text-muted" style="font-size:12px">&#9201; Cron</span>'
            elif tb:
                triggered_html = f'<span style="font-size:12px">{esc(tb)}</span>'
            else:
                triggered_html = '<span class="text-muted">\u2014</span>'
            rows.append(
                f"""
<tr>
  <td class="col-num"><a href="/jobs/{esc(name)}/builds/{esc(bid)}"># {esc(bid)}</a></td>
  <td class="col-time"><span data-time="{esc(started)}">{esc(started)}</span></td>
  <td class="col-dur">{esc(_fmt_duration(b.get("duration")))}</td>
  <td class="col-status">{_badge(b.get("status"))}</td>
  <td style="font-size:12px">{triggered_html}</td>
  <td class="text-muted" style="font-size:12px">{esc(params_str)}</td>
</tr>
"""
            )

        builds_html = f"""
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th class="col-num">#</th>
        <th class="col-time">Started</th>
        <th class="col-dur">Duration</th>
        <th class="col-status">Status</th>
        <th>Triggered by</th>
        <th>Parameters</th>
      </tr>
    </thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>
"""

    body = (
        bc
        + header
        + '<div class="section-title-row">'
        + '<div class="section-title">Build History</div>'
        + _weather(job.get("weather"), compact=True)
        + "</div>"
        + builds_html
    )
    return _page(name, body, username=username, role=role)


def workspace(job, files, username=None, role=None):
    permissions = _permissions_for_role(role)
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, f"/jobs/{name}"), ("Workspace", None))

    if not files:
        files_html = (
            '<div class="empty-state" style="padding:30px 0">'
            "<p>The workspace is empty. Run the job to generate files.</p>"
            "</div>"
        )
    else:

        def _fmt_size(n):
            if n < 1024:
                return f"{n} B"
            if n < 1024 * 1024:
                return f"{n / 1024:.1f} KB"
            return f"{n / 1024 / 1024:.1f} MB"

        rows = "".join(
            f"<tr>"
            f'<td><a href="/jobs/{esc(name)}/workspace/{esc(f["path"])}">{esc(f["path"])}</a></td>'
            f'<td class="text-muted" style="font-size:12px;white-space:nowrap">{esc(_fmt_size(f["size"]))}</td>'
            f'<td class="text-muted col-time"><span data-time="{esc(f["mtime"])}">{esc(f["mtime"])}</span></td>'
            f"</tr>"
            for f in files
        )
        files_html = (
            '<div class="table-wrap"><table>'
            '<thead><tr><th>File</th><th>Size</th><th class="col-time">Modified</th></tr></thead>'
            f"<tbody>{rows}</tbody>"
            "</table></div>"
        )

    clear_btn = (
        f'<form class="inline-form" method="POST" action="/jobs/{esc(name)}/workspace/clear"'
        f" onsubmit=\"return confirm('Clear the workspace for {esc(name)}?')\">"
        f'<button type="submit" class="btn btn-danger">Clear Workspace</button>'
        f"</form>"
        if permissions["can_clear_workspaces"]
        else ""
    )

    header = (
        f'<div class="page-header">'
        f"<h1>Workspace: {esc(name)}</h1>"
        f'<div class="actions">'
        f"{clear_btn}"
        f'<a href="/jobs/{esc(name)}" class="btn btn-secondary">Back to Job</a>'
        f"</div></div>"
    )
    body = bc + header + files_html
    return _page(f"Workspace: {name}", body, username=username, role=role)


def credentials_list(creds, username=None, role=None):
    bc = _breadcrumb(("Dashboard", "/"), ("Credentials", None))
    header = _html(
        """
        <div class="page-header">
          <h1>Credentials</h1>
          <div class="actions">
            <a href="/credentials/new" class="btn btn-primary">+ New Credential</a>
          </div>
        </div>
        """
    )
    if not creds:
        body = _html(
            f"""
            {bc}
            {header}
            <div class="empty-state">
              <p>No credentials yet. <a href="/credentials/new">Add your first credential</a>.</p>
            </div>
            """
        )
        return _page("Credentials", body, username=username, role=role)
    rows_list = []
    for c in creds:
        cname = esc(c["name"])
        cdesc = esc(c.get("description", ""))
        desc_html = f'<div class="job-desc">{cdesc}</div>' if cdesc else ""
        rows_list.append(
            f"<tr>"
            f"<td><strong>{cname}</strong>{desc_html}</td>"
            f'<td style="width:180px;text-align:right">'
            f'<a href="/credentials/{cname}/edit" class="btn btn-secondary btn-sm">Edit</a> '
            f'<form class="inline-form" method="POST" action="/credentials/{cname}/delete"'
            f" onsubmit=\"return confirm('Delete credential {cname}?')\">"
            f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
            f"</form>"
            f"</td></tr>"
        )
    rows = "".join(rows_list)
    table = _html(
        f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Name</th><th style="width:180px"></th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
      """
    )
    body = _html(
        f"""
      {bc}
      {header}
      {table}
      """
    )
    return _page("Credentials", body, username=username, role=role)


def credentials_form(cred=None, error=None, username=None, role=None):
    is_new = cred is None
    title = "New Credential" if is_new else f'Edit: {cred["name"]}'
    bc = _breadcrumb(("Dashboard", "/"), ("Credentials", "/credentials"), (title, None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    name_val = esc(cred["name"]) if cred else ""
    name_input = (
        (
            f'<input type="text" id="name" name="name" value="{name_val}" required'
            f' pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="my-credential">'
        )
        if is_new
        else (
            f'<input type="text" id="name" value="{name_val}" readonly'
            f' style="background:#f6f8fa;cursor:not-allowed">'
            f'<input type="hidden" name="name" value="{name_val}">'
        )
    )
    value_hint = "Enter the secret value" if is_new else "Enter the updated value"
    desc_val = esc(cred.get("description", "")) if cred else ""
    value_val = esc(cred.get("value", "")) if cred else ""
    action = "/credentials/new" if is_new else f'/credentials/{esc(cred["name"])}/edit'
    submit_label = "Create Credential" if is_new else "Save Changes"
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>{esc(title)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="{action}">
            <div class="form-group">
              <label for="name">Name <span class="hint">(letters, numbers, - and _ only)</span></label>
              {name_input}
            </div>
            <div class="form-group">
              <label for="cred-desc">Description <span class="hint">(optional)</span></label>
              <input type="text" id="cred-desc" name="description" value="{desc_val}" placeholder="What is this credential for?">
            </div>
            <div class="form-group">
              <label for="cred-value">Value <span class="hint">{esc(value_hint)}</span></label>
              <textarea id="cred-value" name="value" class="code" rows="6" autocomplete="off" spellcheck="false" placeholder="Paste value or multi-line content (e.g. SSH private key)&#10;-----BEGIN OPENSSH PRIVATE KEY-----&#10;...">{value_val}</textarea>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">{submit_label}</button>
              <a href="/credentials" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(title, body, username=username, role=role)


def job_form(job=None, error=None, available_creds=None, username=None, role=None):
    is_new = job is None
    title = "New Job" if is_new else f'Edit: {job["name"]}'
    bc = _breadcrumb(("Dashboard", "/"), (title, None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""

    name_val = esc(job["name"]) if job else ""
    name_input = (
        (
            f'<input type="text" id="name" name="name" value="{name_val}" required'
            f' pattern="[a-zA-Z0-9][a-zA-Z0-9_-]*" placeholder="my-job">'
        )
        if is_new
        else (
            f'<input type="text" id="name" name="name" value="{name_val}" readonly'
            f' style="background:#f6f8fa;cursor:not-allowed">'
            f'<input type="hidden" name="name" value="{name_val}">'
        )
    )

    desc_val = esc(job.get("description", "")) if job else ""
    raw_mb = job.get("max_builds") if job else None
    max_builds_val = esc(str(raw_mb)) if raw_mb is not None else ""
    enabled_val = True if job is None else bool(job.get("enabled", True))
    disabled_attr = " checked" if not enabled_val else ""
    labels_val = esc(", ".join(job.get("labels") or [])) if job else ""
    trigger = (job.get("trigger") or {}) if job else {}
    trigger_type = trigger.get("type", "manual")
    cron_schedule_val = (
        esc(trigger.get("schedule", "")) if trigger_type == "cron" else ""
    )
    gitpoll_interval_val = (
        esc(str(trigger.get("interval", ""))) if trigger_type == "gitpoll" else ""
    )
    notify_on_failure = (
        True if job is None else bool(job.get("notify_on_failure", True))
    )
    params_json = json_str(job.get("parameters", [])) if job else "[]"
    steps = job.get("steps") if job else None
    if not steps:
        steps = [{"name": "Script 1", "script": "", "image": ""}]
    steps_json = json_str(steps)
    creds_json = json_str(job.get("credentials", []) if job else [])
    available_creds = available_creds or []
    git_cfg = (job.get("git") or {}) if job else {}
    git_url_val = esc(git_cfg.get("url", ""))
    git_branch_val = esc(git_cfg.get("branch", ""))
    git_cred_val = git_cfg.get("credential", "") or ""
    git_shallow = git_cfg.get("shallow", True)
    form_action = "/jobs/new" if is_new else f'/jobs/{esc(job["name"])}/edit'

    git_shallow_attr = " checked" if git_shallow else ""
    notify_on_failure_attr = " checked" if notify_on_failure else ""
    trigger_manual_attr = " checked" if trigger_type not in ("cron", "gitpoll") else ""
    trigger_cron_attr = " checked" if trigger_type == "cron" else ""
    trigger_gitpoll_attr = " checked" if trigger_type == "gitpoll" else ""
    trigger_cron_hidden = " hidden" if trigger_type != "cron" else ""
    trigger_gitpoll_hidden = " hidden" if trigger_type != "gitpoll" else ""
    submit_label = "Create Job" if is_new else "Save Changes"
    cancel_href = "/" if is_new else "/jobs/" + esc(job["name"])

    if available_creds:
        git_credential_field = (
            '<select id="git-credential" name="git_credential" style="max-width:300px">'
            '<option value="">None</option>'
            + "".join(
                f'<option value="{esc(c)}"{" selected" if c == git_cred_val else ""}>{esc(c)}</option>'
                for c in available_creds
            )
            + "</select>"
        )
        credentials_field = _html(
            f"""
            <div class="cred-editor" id="cred-editor">
              <div class="cred-header"><span>Credential</span><span>Env Var Name</span><span>Type</span><span>Actions</span></div>
              <div class="cred-add"><button type="button" id="add-cred-btn" class="btn btn-secondary btn-sm">+ Add</button></div>
            </div>
            <input type="hidden" id="credentials-json" name="credentials_json" value="{esc(creds_json)}">
            """
        )
    else:
        git_credential_field = _html(
            """
            <input type="text" id="git-credential" name="git_credential" value="" style="display:none">
            <p class="text-muted" style="font-size:13px;margin-top:4px">No credentials defined. <a href="/credentials/new">Add a credential</a> to use SSH key auth.</p>
            """
        )
        credentials_field = _html(
            f"""
            <p class="text-muted" style="font-size:13px;margin-top:6px">No credentials defined. <a href="/credentials/new">Add a credential</a> first.</p>
            <input type="hidden" name="credentials_json" value="{esc(creds_json)}">
            """
        )

    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>{esc(title)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="{form_action}">
            <div class="form-section">
              <div class="form-section-title">Basics</div>
              <div class="form-section-hint">Name the job and add the metadata people use to identify it.</div>
              <div class="form-group">
                <label for="name">Name <span class="hint">(letters, numbers, - and _ only)</span></label>
                {name_input}
              </div>
              <div class="form-group">
                <label for="desc">Description <span class="hint">(optional)</span></label>
                <input type="text" id="desc" name="description" value="{desc_val}" placeholder="What does this job do?">
              </div>
              <div class="form-group">
                <label for="job-labels">Labels <span class="hint">(optional, space or comma separated)</span></label>
                <input type="text" id="job-labels" name="labels" value="{labels_val}" placeholder="production qa techops">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="disabled" value="1"{disabled_attr} style="width:auto">
                  Disabled <span class="hint">(check to prevent this job from being built)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Source Code</div>
              <div class="form-section-hint">Optionally check out a Git repository into the workspace before scripts run.</div>
              <div class="form-group">
                <label for="git-url">Repository URL <span class="hint">(leave blank to skip checkout)</span></label>
                <input type="text" id="git-url" name="git_url" value="{git_url_val}" placeholder="git@github.com:user/repo.git">
              </div>
              <div class="form-group">
                <label for="git-branch">Branch <span class="hint">(default: main)</span></label>
                <input type="text" id="git-branch" name="git_branch" value="{git_branch_val}" placeholder="main" style="max-width:220px">
              </div>
              <div class="form-group">
                <label for="git-credential">SSH Key Credential <span class="hint">(optional)</span></label>
                {git_credential_field}
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="git_shallow" value="1"{git_shallow_attr} style="width:auto">
                  Shallow clone <span class="hint">(recommended: fetches only the latest commit)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Scheduling</div>
              <div class="form-section-hint">Control retention and decide whether the job runs manually or on a cron schedule.</div>
              <div class="form-group">
                <label for="job-max-builds">Max build history <span class="hint">(leave blank to use the server default)</span></label>
                <input type="number" id="job-max-builds" name="max_builds" value="{max_builds_val}" min="1" placeholder="e.g. 10" style="max-width:120px">
              </div>
              <div class="form-group">
                <label>Trigger</label>
                <div class="trigger-options">
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="manual"{trigger_manual_attr}> Manual</label>
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="cron"{trigger_cron_attr}> Cron schedule</label>
                  <label class="trigger-option"><input type="radio" name="trigger_type" value="gitpoll"{trigger_gitpoll_attr}> Git poll</label>
                </div>
                <div class="trigger-cron-row" id="trigger-cron-row"{trigger_cron_hidden}>
                  <input type="text" id="cron_schedule" name="cron_schedule" value="{cron_schedule_val}" placeholder="*/5 * * * *" style="max-width:220px;margin-top:6px">
                  <div class="hint" style="margin-top:4px">5 fields: minute hour day month weekday &nbsp;&middot;&nbsp; e.g. <code>0 * * * *</code> = every hour, <code>30 6 * * 1</code> = Mon 06:30</div>
                  <div class="hint" id="cron-next-run" style="margin-top:6px"></div>
                </div>
                <div class="trigger-gitpoll-row" id="trigger-gitpoll-row"{trigger_gitpoll_hidden}>
                  <input type="number" id="gitpoll_interval" name="gitpoll_interval" value="{gitpoll_interval_val}" placeholder="300" min="300" style="max-width:220px;margin-top:6px">
                  <div class="hint" style="margin-top:4px">Polling interval in seconds (default: 300, min: 300)</div>
                </div>
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer;margin-top:10px">
                  <input type="checkbox" name="notify_on_failure" value="1"{notify_on_failure_attr} style="width:auto">
                  Send failure notification emails <span class="hint">(enabled by default; clear to opt out for this job)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Build Inputs</div>
              <div class="form-section-hint">Define user-supplied parameters and any credentials that should be injected into the build environment.</div>
              <div class="form-group">
                <label>Parameters <span class="hint">(passed as environment variables)</span></label>
                <div class="params-editor" id="params-editor">
                  <div class="params-header"><span>Name</span><span>Description</span><span>Default</span><span>Regex</span><span>Actions</span></div>
                  <div class="params-add"><button type="button" id="add-param-btn" class="btn btn-secondary btn-sm">+ Add Parameter</button></div>
                </div>
                <input type="hidden" id="params-json" name="params_json" value="{esc(params_json)}">
              </div>
              <div class="form-group">
                <label>Credentials <span class="hint">(inject secrets into the build environment)</span></label>
                {credentials_field}
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Execution</div>
              <div class="form-section-hint">Add one or more steps. Every step runs inside an ephemeral Docker container.</div>
              <div class="form-group">
                <label>Steps <span class="hint">(run in order)</span></label>
                <div class="script-sections-editor" id="steps-editor">
                  <div class="steps-add"><button type="button" id="add-step-btn" class="btn btn-secondary btn-sm">+ Add Step</button></div>
                </div>
                <input type="hidden" id="steps-json" name="steps_json" value="{esc(steps_json)}">
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">{submit_label}</button>
              <a href="{cancel_href}" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )

    available_creds_js = (
        f"<script>window._pipelineAvailableCreds={json_str(available_creds)};</script>"
    )
    creds_js = (f"<script>{_CREDENTIALS_EDITOR_JS}</script>") if available_creds else ""
    trigger_js = """
  <script>
  (function () {
    var radios = document.querySelectorAll('input[name="trigger_type"]');
    var cronRow = document.getElementById("trigger-cron-row");
    var cronInput = document.getElementById("cron_schedule");
    var preview = document.getElementById("cron-next-run");
    var gitpollRow = document.getElementById("trigger-gitpoll-row");
    var gitpollRadio = document.querySelector('input[name="trigger_type"][value="gitpoll"]');
    var gitUrlInput = document.getElementById("git-url");
    var gitBranchInput = document.getElementById("git-branch");
    var gitCredentialInput = document.getElementById("git-credential");
    var gitShallowInput = document.querySelector('input[name="git_shallow"]');
    var timer = null;

    function hasRepositoryUrl() {
      return !!(gitUrlInput && gitUrlInput.value.trim() !== "");
    }

    function setPreview(text, isError) {
      preview.textContent = text || "";
      preview.style.color = isError ? "#a40e26" : "";
    }

    function fetchPreview() {
      var schedule = cronInput.value.trim();
      if (!schedule) {
        setPreview("Enter a cron schedule to preview the next run.", false);
        return;
      }
      fetch("/cron/preview?schedule=" + encodeURIComponent(schedule), {
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          return r.json().then(function (data) {
            return { ok: r.ok, data: data };
          });
        })
        .then(function (result) {
          if (result.ok) {
            setPreview(result.data.message || "", false);
          } else {
            setPreview(
              result.data.error || "Could not preview the next run.",
              true,
            );
          }
        })
        .catch(function () {
          setPreview("Could not preview the next run.", true);
        });
    }

    function schedulePreview() {
      if (timer) {
        clearTimeout(timer);
      }
      timer = setTimeout(fetchPreview, 150);
    }

    function updateSourceCodeAvailability() {
      var hasGit = hasRepositoryUrl();
      if (gitBranchInput) {
        gitBranchInput.disabled = !hasGit;
      }
      if (gitCredentialInput) {
        gitCredentialInput.disabled = !hasGit;
      }
      if (gitShallowInput) {
        gitShallowInput.disabled = !hasGit;
      }
      [gitBranchInput, gitCredentialInput, gitShallowInput].forEach(function (el) {
        if (!el) {
          return;
        }
        var group = el.closest(".form-group");
        if (group) {
          group.style.opacity = hasGit ? "" : "0.6";
        }
      });
    }

    function updateGitpollAvailability() {
      var hasGit = hasRepositoryUrl();
      if (gitpollRadio) {
        gitpollRadio.disabled = !hasGit;
      }
      var label = gitpollRadio && gitpollRadio.closest("label");
      if (label) {
        label.style.opacity = hasGit ? "" : "0.4";
        label.style.cursor = hasGit ? "" : "not-allowed";
      }
      if (!hasGit && gitpollRadio && gitpollRadio.checked) {
        var manualRadio = document.querySelector('input[name="trigger_type"][value="manual"]');
        if (manualRadio) {
          manualRadio.checked = true;
        }
      }
    }

    function update() {
      updateSourceCodeAvailability();
      updateGitpollAvailability();
      var val = document.querySelector('input[name="trigger_type"]:checked').value;
      cronRow.hidden = val !== "cron";
      gitpollRow.hidden = val !== "gitpoll";
      if (val === "cron") {
        cronInput.required = true;
        schedulePreview();
      } else {
        cronInput.required = false;
        setPreview("", false);
      }
    }

    cronInput.addEventListener("input", schedulePreview);
    if (gitUrlInput) {
      gitUrlInput.addEventListener("input", update);
    }
    radios.forEach(function (r) {
      r.addEventListener("change", update);
    });
    update();
  })();
  </script>
  """
    return _page(
        title,
        body,
        extra_js=f"{available_creds_js}<script>{_PARAMS_EDITOR_JS}</script><script>{_STEPS_EDITOR_JS}</script>{creds_js}{trigger_js}",
        username=username,
        role=role,
    )


def json_str(obj):
    import json

    return json.dumps(obj, ensure_ascii=False)


def _render_log_sections(sections):
    def _compact_details(details):
        details = details or ""
        if details.startswith("Docker image: "):
            details = details[len("Docker image: ") :]
        details = details.replace(" | Host: ", " | ")
        if details.endswith(" | localhost"):
            details = details[: -len(" | localhost")]
        return details

    parts = []
    for index, section in enumerate(sections):
        text = section["text"]
        script = section.get("script", "")
        details = _compact_details(section.get("details", ""))
        heading_html = (
            '<div class="log-section-heading">'
            f'<div class="log-section-title">{esc(section["name"])}</div>'
            "</div>"
        )
        # Only show Docker image details when expanded
        details_html = (
            f'<div class="log-section-subtitle">Docker image: {esc(details)}</div>'
            if details
            else ""
        )
        panel_header_html = f'<div class="log-panel-header">{heading_html}</div>'
        if script:
            panel_top_html = (
                '<details class="log-script-details">'
                '<summary class="log-panel-header log-script-summary">'
                f"{heading_html}"
                "</summary>"
                '<div class="log-script-body">'
                + (
                    f'<div class="log-script-meta">{details_html}</div>'
                    if details_html
                    else ""
                )
                + f'<div class="log-script-wrap">{esc(script)}</div>'
                + "</div>"
                "</details>"
            )
        else:
            panel_top_html = panel_header_html
        log_html = (
            f'<div class="log-wrap" id="log-section-{index}">{esc(text)}</div>'
            if text
            else f'<div id="log-section-{index}"></div>'
        )
        parts.append(
            '<div class="log-section">'
            '<div class="log-panel">'
            f"{panel_top_html}"
            f"{log_html}"
            "</div>"
            "</div>"
        )
    return '<div class="log-sections" id="log-sections">' + "".join(parts) + "</div>"


def build_form(job, error=None, values=None, username=None, role=None):
    name = job["name"]
    bc = _breadcrumb(("Dashboard", "/"), (name, f"/jobs/{name}"), ("Build", None))
    params = job.get("parameters") or []
    values = values or {}
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""

    fields = []
    for p in params:
        raw_name = p.get("name", "")
        pname = esc(raw_name)
        pdesc = esc(p.get("description", ""))
        pdef = esc(values.get(raw_name, p.get("default", "")))
        pregex = p.get("regex", "")
        pregex_esc = esc(pregex)
        label_hint = f' <span class="hint">{pdesc}</span>' if pdesc else ""
        regex_hint = f' <span class="hint">Regex: {pregex_esc}</span>' if pregex else ""
        pattern_attr = f' pattern="{pregex_esc}"' if pregex else ""
        title_attr = f' title="Must match: {pregex_esc}"' if pregex else ""
        fields.append(
            _html(
                f"""
                <div class="form-group">
                  <label for="p_{pname}">{pname}{label_hint}{regex_hint}</label>
                  <input type="text" id="p_{pname}" name="param_{pname}" value="{pdef}"{pattern_attr}{title_attr}>
                </div>
                """
            )
        )

    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Build: {esc(name)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/jobs/{esc(name)}/build">
            {''.join(fields)}
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Run Build</button>
              <a href="/jobs/{esc(name)}" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(f"Build: {name}", body, username=username, role=role)


def _live_log_js(section_log_urls, status_url):
    import json as _json

    urls_js = _json.dumps(section_log_urls)
    su = _json.dumps(status_url)
    return _html(
        f"""
        <script>
        (function() {{
          var sectionUrls = {urls_js};
          var statusUrl = {su};

          function poll() {{
            sectionUrls.forEach(function(url, i) {{
              var el = document.getElementById("log-section-" + i);
              if (!el) return;
              fetch(url + "?_=" + Date.now())
                .then(function(r) {{ return r.text(); }})
                .then(function(t) {{
                  if (t) {{
                    el.classList.add("log-wrap");
                    el.textContent = t;
                    el.scrollTop = el.scrollHeight;
                  }}
                }})
                .catch(function() {{}});
            }});
          }}

          function check(delay) {{
            window.setTimeout(function() {{
              fetch(statusUrl + "?_=" + Date.now())
                .then(function(r) {{ return r.json(); }})
                .then(function(d) {{
                  if (d.status !== "running") {{
                    location.reload();
                    return;
                  }}
                  check(500);
                }})
                .catch(function() {{
                  check(1000);
                }});
            }}, delay || 0);
          }}

          setInterval(poll, 2000);
          poll();
          check();
        }})();
        </script>
        """
    )


def build_detail(job, build, section_logs, username=None, role=None):
    permissions = _permissions_for_role(role)
    name = job["name"]
    bid = build["id"]
    status = build.get("status", "")
    bc = _breadcrumb(
        ("Dashboard", "/"),
        (name, f"/jobs/{name}"),
        (f"Build #{bid}", None),
    )

    params = build.get("parameters") or {}
    params_html = ""
    if params:
        rows = "".join(
            f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in params.items()
        )
        params_html = (
            '<div class="meta-item" style="min-width:200px">'
            '<div class="meta-label">Parameters</div>'
            '<div class="meta-value">'
            f'<table class="param-table"><tbody>{rows}</tbody></table>'
            "</div></div>"
        )

    cancel_btn = ""
    if permissions["can_run_builds"] and status in ("running", "queued"):
        cancel_btn = (
            f'<form class="inline-form" method="POST"'
            f' action="/jobs/{esc(name)}/builds/{esc(bid)}/cancel">'
            '<button type="submit" class="btn btn-warning btn-sm">Cancel Build</button>'
            "</form>"
        )

    started = build.get("started_at", "")
    queued_at = build.get("queued_at", "")
    started_label = "Started"
    started_value = started
    if not started and queued_at:
        started_label = "Queued"
        started_value = queued_at
    finished = build.get("finished_at", "")
    tb = build.get("triggered_by") or ""
    if tb == "cron":
        triggered_html = "&#9201; Cron schedule"
    elif tb:
        triggered_html = esc(tb)
    else:
        triggered_html = "\u2014"
    meta = (
        '<div class="meta-grid">'
        f'<div class="meta-item"><div class="meta-label">Status</div>'
        f'<div class="meta-value">{_badge(status)}</div></div>'
        f'<div class="meta-item"><div class="meta-label">{esc(started_label)}</div>'
        f'<div class="meta-value"><span data-time="{esc(started_value)}">{esc(started_value)}</span></div></div>'
        f'<div class="meta-item"><div class="meta-label">Duration</div>'
        f'<div class="meta-value">{esc(_fmt_duration(build.get("duration")))}</div></div>'
        f'<div class="meta-item"><div class="meta-label">Triggered by</div>'
        f'<div class="meta-value">{triggered_html}</div></div>'
        + (
            f'<div class="meta-item"><div class="meta-label">Finished</div>'
            f'<div class="meta-value"><span data-time="{esc(finished)}">{esc(finished)}</span></div></div>'
            if finished
            else ""
        )
        + params_html
        + "</div>"
    )

    log_section = (
        '<div class="section-title">'
        "Log "
        f'<a href="/jobs/{esc(name)}/builds/{esc(bid)}/log" class="text-muted" style="font-size:12px;font-weight:500;margin-left:8px">View as plain text</a>'
        "</div>" + f"{_render_log_sections(section_logs)}"
    )

    header = (
        f'<div class="page-header">'
        f"<h1>Build #{esc(bid)}: {esc(name)}</h1>"
        f'<div class="actions">{cancel_btn}</div>'
        f"</div>"
    )

    body = bc + header + meta + log_section

    extra_js = ""
    if status == "running":
        section_urls = [
            f"/jobs/{esc(name)}/builds/{esc(bid)}/log/{i + 1}"
            for i in range(len(section_logs))
        ]
        extra_js = _live_log_js(
            section_urls,
            f"/jobs/{esc(name)}/builds/{esc(bid)}/status",
        )

    return _page(
        f"Build #{bid}: {name}",
        body,
        extra_js=extra_js,
        username=username,
        role=role,
    )


def users_list(users, current_user, error=None, username=None, role=None):
    bc = _breadcrumb(("Dashboard", "/"), ("Users", None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    header = _html(
        """
        <div class="page-header">
          <h1>Users</h1>
          <div class="actions">
            <a href="/settings/users/new" class="btn btn-primary">+ New User</a>
          </div>
        </div>
        """
    )
    rows = []
    for user in users:
        if isinstance(user, dict):
            uname = user.get("username", "")
            role_name = user.get("role", "")
            is_disabled = bool(user.get("disabled", False))
        else:
            uname = user
            role_name = ""
            is_disabled = False
        uesc = esc(uname)
        role_name = role_name if role_name in ("admin", "user", "viewer") else "user"
        role_html = esc(role_name.capitalize())
        if is_disabled:
            role_html += ' <span class="badge badge-aborted" style="font-size:10px;vertical-align:middle">Disabled</span>'
        is_self = uname == current_user
        self_badge = (
            ' <span class="label-chip" style="font-size:11px;vertical-align:middle">you</span>'
            if is_self
            else ""
        )
        actions = f'<a href="/settings/users/{uesc}/edit" class="btn btn-secondary btn-sm">Edit User</a> '
        if not is_self:
            actions += (
                f'<form class="inline-form" method="POST" action="/settings/users/{uesc}/delete"'
                f" onsubmit=\"return confirm('Delete user {uesc}?')\">"
                f'<button type="submit" class="btn btn-danger btn-sm">Delete</button>'
                f"</form>"
            )
        rows.append(
            f"<tr>"
            f"<td><strong>{uesc}</strong>{self_badge}</td>"
            f"<td>{role_html}</td>"
            f'<td style="text-align:right">{actions}</td>'
            f"</tr>"
        )
    table = _html(
        f"""
      <div class="table-wrap"><table>
        <thead><tr><th>Username</th><th>Role</th><th></th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
      """
    )
    empty = '<div class="empty-state"><p>No users.</p></div>'
    body = _html(
        f"""
      {bc}
      {header}
      {error_html}
      {table if rows else empty}
      """
    )
    return _page("Users", body, username=username, role=role)


def user_edit_form(
    target_user, user_role="user", disabled=False, error=None, username=None, role=None
):
    bc = _breadcrumb(
        ("Dashboard", "/"),
        ("Users", "/settings/users"),
        (f"Edit user: {target_user}", None),
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    role_value = user_role if user_role in ("admin", "user", "viewer") else "user"
    disabled_attr = " checked" if disabled else ""
    sel_admin = " selected" if role_value == "admin" else ""
    sel_user = " selected" if role_value == "user" else ""
    sel_viewer = " selected" if role_value == "viewer" else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Edit user: {esc(target_user)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/{esc(target_user)}/edit">
            <div class="form-group">
              <label>Username</label>
              <input type="text" value="{esc(target_user)}" readonly style="background:#f6f8fa;cursor:not-allowed">
            </div>
            <div class="form-group">
              <label for="edit-user-role">Role</label>
              <select id="edit-user-role" name="role" required style="max-width:220px">
                <option value="admin"{sel_admin}>Administrator</option>
                <option value="user"{sel_user}>User</option>
                <option value="viewer"{sel_viewer}>Viewer</option>
              </select>
            </div>
            <div class="form-group">
              <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                <input type="checkbox" name="disabled" value="1"{disabled_attr} style="width:auto">
                Disable this user <span class="hint">(prevents login without deleting the account)</span>
              </label>
            </div>
            <div class="form-group">
              <label for="edit-user-password">New password <span class="hint">(optional, leave blank to keep unchanged)</span></label>
              <input type="password" id="edit-user-password" name="password" autocomplete="new-password" minlength="8">
            </div>
            <div class="form-group">
              <label for="edit-user-confirm">Confirm new password</label>
              <input type="password" id="edit-user-confirm" name="confirm" autocomplete="new-password" minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save Changes</button>
              <a href="/settings/users" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(f"Edit user: {target_user}", body, username=username, role=role)


def user_new_form(error=None, username=None, role=None):
    bc = _breadcrumb(
        ("Dashboard", "/"), ("Users", "/settings/users"), ("New User", None)
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>New User</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/new">
            <div class="form-group">
              <label for="new-username">Username</label>
              <input type="text" id="new-username" name="username" autocomplete="off" autofocus required pattern="[a-zA-Z0-9][a-zA-Z0-9._-]{{0,49}}">
            </div>
            <div class="form-group">
              <label for="new-role">Role</label>
              <select id="new-role" name="role" required>
                <option value="user" selected>User</option>
                <option value="viewer">Viewer</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            <div class="form-group">
              <label for="new-password">Password</label>
              <input type="password" id="new-password" name="password" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-group">
              <label for="new-confirm">Confirm password</label>
              <input type="password" id="new-confirm" name="confirm" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Create User</button>
              <a href="/settings/users" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page("New User", body, username=username, role=role)


def user_password_form(target_user, error=None, username=None, role=None):
    bc = _breadcrumb(
        ("Dashboard", "/"),
        ("Users", "/settings/users"),
        (f"Change password: {target_user}", None),
    )
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Change password: {esc(target_user)}</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings/users/{esc(target_user)}/password">
            <div class="form-group">
              <label for="new-password">New password</label>
              <input type="password" id="new-password" name="password" autocomplete="new-password" autofocus required minlength="8">
            </div>
            <div class="form-group">
              <label for="new-confirm">Confirm password</label>
              <input type="password" id="new-confirm" name="confirm" autocomplete="new-password" required minlength="8">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save</button>
              <a href="/" class="btn btn-secondary">Cancel</a>
            </div>
          </form>
        </div>
        """
    )
    return _page(f"Change password: {target_user}", body, username=username, role=role)


def error_404(username=None, role=None):
    body = _html(
        """
        <div class="empty-state">
          <h1 style="font-size:48px;color:#d0d7de">404</h1>
          <p>Page not found. <a href="/">Go to Dashboard</a>.</p>
        </div>
        """
    )
    return _page("Not Found", body, username=username, role=role)


def error_403(username=None, role=None):
    body = _html(
        """
          <div class="empty-state">
            <h1 style="font-size:48px;color:#d0d7de">403</h1>
            <p>You do not have permission to access this page.</p>
          </div>
          """
    )
    return _page("Forbidden", body, username=username, role=role)


def settings(cfg, available_creds=None, error=None, username=None, role=None):
    bc = _breadcrumb(("Dashboard", "/"), ("Settings", None))
    error_html = f'<div class="alert alert-danger">{esc(error)}</div>' if error else ""
    max_builds = esc(str(cfg.get("max_builds", 10)))
    max_concurrent_jobs = esc(str(cfg.get("max_concurrent_jobs", 2)))
    queue_paused = bool(cfg.get("queue_paused", False))
    queue_pause_message = esc(cfg.get("queue_pause_message", "Job queue is paused."))
    default_script_header = esc(cfg.get("default_script_header", ""))
    mount_docker_socket = bool(cfg.get("mount_docker_socket", False))
    email_cfg = cfg.get("email_notifications", {}) or {}
    available_creds = available_creds or []
    recipients = email_cfg.get("recipients", [])
    if isinstance(recipients, list):
        recipients_val = esc("\n".join(recipients))
    else:
        recipients_val = esc(recipients)
    from_address_val = esc(email_cfg.get("from_address", ""))
    smtp_host_val = esc(email_cfg.get("smtp_host", ""))
    smtp_port_val = esc(str(email_cfg.get("smtp_port", 587)))
    smtp_security = email_cfg.get("smtp_security", "starttls")
    smtp_username_val = esc(email_cfg.get("smtp_username", ""))
    smtp_credential_val = email_cfg.get("smtp_credential", "")
    queue_paused_attr = " checked" if queue_paused else ""
    mount_docker_socket_attr = " checked" if mount_docker_socket else ""
    smtp_credential_field = (
        (
            '<select id="notification-smtp-credential" name="notification_smtp_credential" style="max-width:300px">'
            + '<option value="">None</option>'
            + "".join(
                f'<option value="{esc(c)}"{" selected" if c == smtp_credential_val else ""}>{esc(c)}</option>'
                for c in available_creds
            )
            + "</select>"
        )
        if available_creds
        else (
            '<input type="hidden" name="notification_smtp_credential" value="">'
            '<p class="text-muted" style="font-size:13px;margin-top:4px">No credentials defined. <a href="/credentials/new">Add a credential</a> to enable SMTP auth.</p>'
        )
    )
    body = _html(
        f"""
        {bc}
        <div class="page-header"><h1>Settings</h1></div>
        {error_html}
        <div class="form-card">
          <form method="POST" action="/settings">
            <div class="form-section" style="margin-top:0;padding-top:0;border-top:none">
              <div class="form-section-title">Execution Defaults</div>
              <div class="form-group">
                <label for="default-script-header">Default script header <span class="hint">(prepended only when a step script does not define its own shebang)</span></label>
                <textarea id="default-script-header" name="default_script_header" class="code" rows="6" spellcheck="false">{default_script_header}</textarea>
              </div>
              <div class="form-group">
                <label for="max-builds">Max build history <span class="hint">(default for all jobs; jobs can override this)</span></label>
                <input type="number" id="max-builds" name="max_builds" value="{max_builds}" min="1" style="max-width:120px">
              </div>
              <div class="form-group">
                <label for="max-concurrent-jobs">Max concurrent jobs <span class="hint">(server-wide queue limit; default: 2)</span></label>
                <input type="number" id="max-concurrent-jobs" name="max_concurrent_jobs" value="{max_concurrent_jobs}" min="1" style="max-width:120px">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="queue_paused" value="1"{queue_paused_attr} style="width:auto">
                  Pause the job queue <span class="hint">(running jobs continue; queued jobs wait)</span>
                </label>
              </div>
              <div class="form-group">
                <label for="queue-pause-message">Queue pause banner message</label>
                <input type="text" id="queue-pause-message" name="queue_pause_message" value="{queue_pause_message}" placeholder="Job queue is paused.">
              </div>
              <div class="form-group">
                <label style="display:flex;align-items:center;gap:8px;font-weight:normal;cursor:pointer">
                  <input type="checkbox" name="mount_docker_socket" value="1"{mount_docker_socket_attr} style="width:auto">
                  Mount host Docker socket into job containers <span class="hint">(disabled by default; enable to allow job containers to talk to the host Docker daemon)</span>
                </label>
              </div>
            </div>

            <div class="form-section">
              <div class="form-section-title">Failure Notifications</div>
              <div class="form-section-hint">Configure where failed build emails are sent. Jobs notify by default unless they opt out.</div>
              <div class="form-group">
                <label for="notification-recipients">Notification email addresses <span class="hint">(comma or newline separated; leave blank to disable)</span></label>
                <input type="text" id="notification-recipients" name="notification_recipients" value="{recipients_val}" spellcheck="false" placeholder="user1@example.com, user2@example.com">
              </div>
              <div class="form-group">
                <label for="notification-from-address">From address <span class="hint">(optional; defaults to SMTP username or the first recipient)</span></label>
                <input type="text" id="notification-from-address" name="notification_from_address" value="{from_address_val}" placeholder="pipeline@example.com">
              </div>
              <div class="form-group">
                <label for="notification-smtp-host">SMTP host</label>
                <input type="text" id="notification-smtp-host" name="notification_smtp_host" value="{smtp_host_val}" placeholder="smtp.example.com">
              </div>
              <div class="form-group">
                <label for="notification-smtp-port">SMTP port</label>
                <input type="number" id="notification-smtp-port" name="notification_smtp_port" value="{smtp_port_val}" min="1" max="65535" style="max-width:120px">
              </div>
              <div class="form-group">
                <label for="notification-smtp-security">SMTP security</label>
                <select id="notification-smtp-security" name="notification_smtp_security" style="max-width:180px">
                  <option value="none"{" selected" if smtp_security == "none" else ""}>None</option>
                  <option value="starttls"{" selected" if smtp_security == "starttls" else ""}>STARTTLS</option>
                  <option value="ssl"{" selected" if smtp_security == "ssl" else ""}>SSL/TLS</option>
                </select>
              </div>
              <div class="form-group">
                <label for="notification-smtp-username">SMTP username <span class="hint">(optional)</span></label>
                <input type="text" id="notification-smtp-username" name="notification_smtp_username" value="{smtp_username_val}" placeholder="pipeline-user">
              </div>
              <div class="form-group">
                <label for="notification-smtp-credential">SMTP credential <span class="hint">(optional password from Credentials)</span></label>
                {smtp_credential_field}
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Save Settings</button>
            </div>
          </form>
        </div>
        """
    )
    return _page("Settings", body, username=username, role=role)


def error_500(message, username=None, role=None):
    body = _html(
        f"""
        <div class="page-header"><h1>Server Error</h1></div>
        <div class="alert alert-danger"><pre style="white-space:pre-wrap">{esc(str(message))}</pre></div>
        <p><a href="/">Go to Dashboard</a></p>
        """
    )
    return _page("Error", body, username=username, role=role)
