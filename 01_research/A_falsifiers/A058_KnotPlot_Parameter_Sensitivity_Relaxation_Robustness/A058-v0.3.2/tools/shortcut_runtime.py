"""Auditable native KnotPlot launcher: preserve Windows shortcut Start in directory.

The .lnk is metadata, never passed to CreateProcess directly.  Generated per-probe
KnotPlot input/output filenames are absolute, so the application working directory
may be the real KnotPlot data directory without scattering A058 exports there.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import dataclass


def _require_workdir(path: Path, description: str) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise NotADirectoryError(f'{description} is not a directory: {resolved}')
    return resolved


def _relative_shortcut_workdir(exe: Path, shortcut: Path, raw: str) -> tuple[Path, str]:
    """Resolve a relative shortcut Start-in conservatively; never use process cwd."""
    relative = Path(raw)
    # A relative '.' for KnotPlot is interpreted as the target EXE directory,
    # never the folder containing the copied A058 shortcut.
    if relative == Path('.'):
        return _require_workdir(exe.parent, 'KnotPlot executable parent'), 'relative_dot_executable_parent'
    candidate_exe = (exe.parent / relative).resolve(strict=False)
    candidate_link = (shortcut.parent / relative).resolve(strict=False)
    candidates = []
    for base, candidate in (('executable_parent', candidate_exe), ('shortcut_parent', candidate_link)):
        if candidate.is_dir() and candidate not in [v for _, v in candidates]:
            candidates.append((base, candidate))
    if not candidates:
        raise FileNotFoundError(
            f'Shortcut Start-in {raw!r} did not resolve from the EXE or shortcut parent. '
            'Supply --workdir with an absolute KnotPlot working directory.')
    if len(candidates) > 1:
        raise RuntimeError(
            f'Ambiguous relative Start-in {raw!r}: EXE parent yields {candidate_exe}, '
            f'shortcut parent yields {candidate_link}; specify --workdir explicitly.')
    base, directory = candidates[0]
    return _require_workdir(directory, 'Shortcut relative Start-in'), 'relative_start_in_' + base


@dataclass(frozen=True)
class KnotPlotLaunch:
    executable: Path
    workdir: Path
    shortcut: Path | None
    shortcut_args: str = ''
    workdir_source: str = 'executable_parent'

    def command(self):
        if self.shortcut_args:
            # Raw Windows shortcut arguments are deliberately retained verbatim.
            # No shell=True: CreateProcess receives the original executable path.
            return (subprocess.list2cmdline([str(self.executable)]) + ' '
                    + self.shortcut_args + ' -stdin -nographics')
        return [str(self.executable), '-stdin', '-nographics']


def resolve_launcher(value: Path | str, *, platform: str | None = None,
                     workdir_override: Path | str | None = None) -> KnotPlotLaunch:
    platform = sys.platform if platform is None else platform
    entry = Path(value).expanduser().resolve(strict=True)
    explicit = None
    if workdir_override is not None:
        explicit_path = Path(os.path.expandvars(str(workdir_override))).expanduser()
        if not explicit_path.is_absolute():
            raise ValueError('--workdir must be an absolute path')
        explicit = _require_workdir(explicit_path, '--workdir')
    if not entry.is_file():
        raise FileNotFoundError(f'KnotPlot launcher is not a file: {entry}')
    if entry.suffix.casefold() != '.lnk':
        if entry.suffix.casefold() != '.exe':
            raise ValueError(f'Expected Windows EXE or LNK, got {entry.suffix}')
        return KnotPlotLaunch(entry, explicit or entry.parent, None,
                              workdir_source='explicit_cli_override' if explicit is not None else 'executable_parent')
    if platform != 'win32':
        raise RuntimeError('Resolving Windows .lnk needs PowerShell/COM on Windows')

    script = ("$ErrorActionPreference='Stop'; "
              "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); "
              "$sc=(New-Object -ComObject WScript.Shell).CreateShortcut($env:A058_SHORTCUT_PATH); "
              "[pscustomobject]@{target=$sc.TargetPath;workdir=$sc.WorkingDirectory;"
              "arguments=$sc.Arguments}|ConvertTo-Json -Compress")
    env = os.environ.copy()
    env['A058_SHORTCUT_PATH'] = str(entry)
    r = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],
                       env=env, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=20, check=False)
    if r.returncode:
        raise RuntimeError(f'Windows shortcut resolution failed (PowerShell rc={r.returncode}): '
                           + r.stderr.strip()[-600:])
    try:
        data = json.loads(r.stdout.strip())
        exe = Path(os.path.expandvars(data['target'])).expanduser().resolve(strict=True)
        raw_workdir = str(data.get('workdir') or '').strip()
        shortcut_args = str(data.get('arguments') or '').strip()
    except (ValueError, KeyError, TypeError, OSError) as e:
        raise RuntimeError(f'Invalid shortcut metadata: {type(e).__name__}') from e
    if not exe.is_file() or exe.suffix.casefold() != '.exe':
        raise RuntimeError('Shortcut does not resolve to an existing KnotPlot .exe')
    if explicit is not None:
        wd = explicit
        source = 'explicit_cli_override'
    elif raw_workdir:
        start_in = Path(os.path.expandvars(raw_workdir.strip('"'))).expanduser()
        if start_in.is_absolute():
            wd = _require_workdir(start_in, 'Shortcut Start-in')
            source = 'shortcut_start_in_absolute'
        else:
            wd, source = _relative_shortcut_workdir(exe, entry, str(start_in))
    else:
        wd = _require_workdir(exe.parent, 'KnotPlot EXE parent')
        source = 'empty_shortcut_start_in_executable_parent_fallback'
    return KnotPlotLaunch(exe, wd, entry, shortcut_args, source)


def knotplot_path(path:Path)->str:
    p=path.resolve().as_posix()
    if any(c in p for c in '\r\n\0"'):
        raise ValueError('Path not expressible in KnotPlot script')
    # Quoted filenames are supported by some but not all KnotPlot versions.
    # Native runtime command/readback qualification remains mandatory.
    return '"'+p+'"' if any(c.isspace() for c in p) else p


def native_probe_script(script:str, probe_dir:Path)->str:
    """Rebind only three known file operations; original probe.kpc is never edited."""
    required = {
      'load A058_seed.kpf': 'load ' + knotplot_path(probe_dir/'A058_seed.kpf'),
      'data open A058_native_metrics.csv': 'data open ' + knotplot_path(probe_dir/'A058_native_metrics.csv'),
      'save A058_final.txt ascii': 'save ' + knotplot_path(probe_dir/'A058_final.txt') + ' ascii',
    }
    lines=script.splitlines()
    for needle,replacement in required.items():
        hits=[i for i,old in enumerate(lines) if old.strip()==needle]
        if len(hits)!=1:
            raise ValueError(f'Expected exactly one {needle!r}, found {len(hits)}: refusing ambiguous native probe')
        lines[hits[0]]=replacement
    return '\n'.join(lines)+'\n'
