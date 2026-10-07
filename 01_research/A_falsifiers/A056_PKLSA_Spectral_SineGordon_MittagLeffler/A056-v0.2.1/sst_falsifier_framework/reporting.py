from __future__ import annotations
from pathlib import Path
import json

def render_json_context(template_path, output_path, replacements):
    text=Path(template_path).read_text(encoding='utf-8')
    for k,v in replacements.items(): text=text.replace('{{'+k+'}}',str(v))
    Path(output_path).write_text(text,encoding='utf-8')
