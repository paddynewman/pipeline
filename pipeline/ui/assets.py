import urllib.parse

__all__ = [
    "_BRAND_ICON_SVG",
    "_FAVICON_HREF",
    "_CSS",
    "_TIMEAGO_JS",
    "_PARAMS_EDITOR_JS",
    "_STEPS_EDITOR_JS",
    "_CREDENTIALS_EDITOR_JS",
]

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
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
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
.topnav a { color: #8b949e; text-decoration: none; font-size: 13px; padding: 4px 8px; border-radius: 6px; }
.topnav a:hover { color: #f0f6fc; background: rgba(255,255,255,.08); text-decoration: none; }
.topbar-spacer { flex: 1; }
.user-menu { position: relative; display: inline-block; }
.user-menu-btn {
  background: none; border: 1px solid rgba(255,255,255,.2); border-radius: 6px;
  color: #c9d1d9; font-size: 13px; padding: 4px 10px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
}
.user-menu-btn:hover { background: rgba(255,255,255,.08); color: #f0f6fc; }
.user-menu-btn::after { content: ''; display: inline-block; border-top: 4px solid currentColor; border-left: 4px solid transparent; border-right: 4px solid transparent; }
.user-dropdown {
  display: none; position: absolute; right: 0; top: calc(100% + 6px);
  background: #2d333b; border: 1px solid #444c56; border-radius: 8px;
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
.job-header { gap: 40px; }
.job-header-main { flex: 1; min-width: 0; }
.job-header .actions { flex-shrink: 0; align-self: flex-start; }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 14px; border-radius: 6px; font-size: 13px; font-weight: 500;
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
.table-wrap { background: white; border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; }
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
  display: inline-block; padding: 2px 9px; border-radius: 999px;
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
  background: white; border: 1px solid #d0d7de; border-radius: 8px;
  padding: 20px; margin-bottom: 16px;
}

/* Meta grid */
.meta-grid {
  display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 20px;
  background: white; border: 1px solid #d0d7de; border-radius: 8px;
  padding: 16px 20px;
}
.meta-item {}
.meta-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; color: #57606a; }
.meta-value { font-size: 14px; margin-top: 3px; font-weight: 500; }

/* Log */
.log-panel {
  background: #e9ecef; border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden;
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
.log-script-details + .log-wrap { border-top: 1px solid #d0d7de; }
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
  margin: 0; background: #f6f8fa; border: none; border-bottom: none; border-radius: 0;
  padding: 12px; font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', monospace;
  font-size: 12px; line-height: 1.7; color: #24292f; white-space: pre-wrap; overflow-x: auto;
}

/* Forms */
.form-card { background: white; border: 1px solid #d0d7de; border-radius: 8px; padding: 24px; }
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
  width: 100%; padding: 6px 12px; border: 1px solid #d0d7de; border-radius: 6px;
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
.params-editor { border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; margin-top: 6px; }
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
  font-size: 12px; line-height: 1; padding: 5px 7px; border-radius: 6px;
}
.btn-param:hover { background: #e9ecef; }
.btn-param:disabled { opacity: 0.5; cursor: default; }
.btn-rm { background: none; border: none; color: #cf222e; cursor: pointer; font-size: 18px; line-height: 1; padding: 0 2px; }
.btn-rm:hover { opacity: 0.7; }

/* Script sections editor */
.script-sections-editor { border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; margin-top: 6px; }
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
  border-radius: 6px; background: #f6f8fa;
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
.alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; }
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
  display: inline-block; padding: 1px 8px; border-radius: 999px;
  font-size: 11px; font-weight: 500; background: #ddf4ff; color: #0550ae;
  border: 1px solid #b6e3ff;
}
.dashboard-tabs {
  display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;
}
.dashboard-tab {
  appearance: none; border: 1px solid #d0d7de; background: #ffffff; color: #57606a;
  border-radius: 999px; padding: 6px 12px; font-size: 12px; font-weight: 600;
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
.cred-editor { border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden; margin-top: 6px; }
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
  window.timeAgo = timeAgo;
  document.querySelectorAll('[data-time]').forEach(function (el) {
    el.title = el.getAttribute('data-time');
    el.textContent = timeAgo(el.getAttribute('data-time'));
  });
})();
"""

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
