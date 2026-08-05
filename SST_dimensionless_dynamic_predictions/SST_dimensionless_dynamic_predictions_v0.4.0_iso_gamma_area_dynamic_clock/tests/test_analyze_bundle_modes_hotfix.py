from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_analyzer_skips_old_schema_and_accepts_explicit_inputs(tmp_path: Path) -> None:
    old = tmp_path / 'old' / 'campaign_summary.csv'
    _write_csv(old, ['label', 'relative_equilibrium_residual'], [{'label': 'ring', 'relative_equilibrium_residual': 0.0}])

    fields = [
        'ladder_gate', 'label', 'resolution', 'epsilon', 'kernel', 'bundle_mode',
        'radius_ratio_to_hole', 'tube_count', 'circulation_per_tube', 'total_circulation',
        'clock_omega', 'valid_geometry', 'intrinsic_residual', 'residual_reduction_fraction',
        'background_velocity_rms'
    ]
    physical = tmp_path / 'physical' / 'campaign_summary.csv'
    numerical = tmp_path / 'numerical' / 'campaign_summary.csv'
    base = {
        'ladder_gate': 'B6', 'label': 'trefoil', 'resolution': 96, 'epsilon': 0.05,
        'kernel': 'rosenhead', 'radius_ratio_to_hole': 1.0, 'clock_omega': 1.0,
        'valid_geometry': True, 'intrinsic_residual': 0.2,
        'residual_reduction_fraction': 0.0, 'background_velocity_rms': 1.0,
    }
    _write_csv(physical, fields, [{**base, 'bundle_mode': 'physical_tubes', 'tube_count': 4, 'circulation_per_tube': 0.25, 'total_circulation': 1.0}])
    _write_csv(numerical, fields, [
        {**base, 'bundle_mode': 'numerical_discretization', 'tube_count': 4, 'circulation_per_tube': 0.25, 'total_circulation': 1.0},
        {**base, 'bundle_mode': 'continuum', 'tube_count': 0, 'circulation_per_tube': 0.0, 'total_circulation': 1.0},
    ])

    root = Path(__file__).resolve().parents[1]
    output = tmp_path / 'analysis'
    cmd = [
        sys.executable, str(root / 'tools' / 'analyze_bundle_modes.py'),
        '--physical-input', str(physical.parent),
        '--numerical-input', str(numerical.parent),
        '--input', str(tmp_path / 'old'),
        '--output', str(output),
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads((output / 'bundle_mode_analysis.json').read_text(encoding='utf-8'))
    assert payload['physical_rows'] == 1
    assert payload['numerical_discretization_rows'] == 1
    assert payload['continuum_rows'] == 1
    assert payload['skipped_summary_file_count'] == 1
