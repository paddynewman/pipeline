import os
import re

import yaml
from bottle import template


VARIABLE_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def collect_template_variables(template_text):
    return sorted(set(VARIABLE_PATTERN.findall(template_text)))


def render_templates(template_dir, template_files, context):
    manifests = []
    for filename in template_files:
        path = os.path.join(template_dir, filename)
        with open(path, "r", encoding="utf-8") as handle:
            raw_text = handle.read()

        rendered = template(raw_text, **context)
        parsed = list(yaml.safe_load_all(rendered))
        manifests.extend([item for item in parsed if item])

    return manifests


def render_template_text(template_text, context):
    rendered = template(template_text, **context)
    parsed = list(yaml.safe_load_all(rendered))
    return [item for item in parsed if item]
