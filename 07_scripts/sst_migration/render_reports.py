"""Render immutable preflight results, never run or recalculate science."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def render(state):
    queue = json.loads((state / 'queue.json').read_text())
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    for job in queue['jobs']:
        if not job.get('result'):
            continue
        source = state / job['result']
        data = json.loads(source.read_text())
        target = source.with_name(job['id'] + '_PREFLIGHT_REPORT.pdf')
        if target.exists():
            raise FileExistsError(target)
        story = []
        def text(value, style='Normal'):
            story.append(Paragraph(escape(str(value)), styles[style]))
            story.append(Spacer(1, 3 * mm))
        text(job['id'] + ' - Migration pilot preflight', 'Title')
        text('BLOCKED | No scientific execution', 'Heading2')
        text('UTC: ' + data['created'])
        text('Source: ' + data['source_version'] + '; proposed sibling: ' + data['proposed_version'])
        text('The proposed sibling has NOT been created. Existing versions and results were not modified.')
        text('Architecture and adapter', 'Heading2')
        text(data['architecture'])
        text(data['adapter_requirements'])
        text('Independent gates', 'Heading2')
        text('Migration: BLOCKED. Execution: NOT_RUN. Scientific certification: NOT_RUN.')
        text('Blocking conditions', 'Heading2')
        for item in data['blockers']:
            text(item.replace('_', ' '))
        audit = data['source_audit']
        for item in audit['framework']['failures']:
            text('Framework manifest mismatch: ' + item['path'])
        pk = audit['pklsa']
        text('Dataset evidence', 'Heading2')
        text(f"Active view: {pk['active_count']} topologies. Historical statuses: {pk['historical_statuses']}. Source-index hashes: {pk['source_hash_status']}.")
        text('Selection is not science requalification. Geometry payload hashes and per-falsifier physical admissibility remain unverified. E010 v0.3.5 physical dynamics: NOT_RUN.')
        text('Evidence and next action', 'Heading2')
        text('Run: ' + data['run_id'])
        text('Result SHA-256: ' + hashlib.sha256(source.read_bytes()).hexdigest())
        text('Resolve canonical source drift without rewriting manifests to hide differences; reconcile registry; review the per-family adapter and dataset admission contract before creating a new version.')
        def footer(canvas, doc):
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(18 * mm, 12 * mm, 'SST-Workbench | preflight evidence | page ' + str(doc.page))
        # Exclusive destination creation prevents accidental report replacement.
        with target.open('xb') as stream:
            SimpleDocTemplate(stream, pagesize=(210 * mm, 297 * mm), leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=20*mm).build(story, onFirstPage=footer, onLaterPages=footer)
        print(target)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, required=True)
    render(p.parse_args().state)
