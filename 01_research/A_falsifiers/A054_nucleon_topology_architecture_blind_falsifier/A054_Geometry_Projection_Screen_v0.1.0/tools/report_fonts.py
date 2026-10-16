"""Portable ReportLab font selection; no font binary is redistributed."""
from __future__ import annotations
import os
import platform
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def font_candidates(platform_name: str | None = None, windows_dir: str | None = None):
    system = platform_name or platform.system()
    windows = Path(windows_dir or os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    package_fonts = Path(reportlab.__file__).resolve().parent / 'fonts'
    paths=[]
    env_normal=os.environ.get('SST_REPORT_FONT_REGULAR')
    env_bold=os.environ.get('SST_REPORT_FONT_BOLD')
    if env_normal and env_bold:
        paths.append((Path(env_normal),Path(env_bold),'user-defined'))
    if system == 'Windows':
        paths.extend([
            (windows/'segoeui.ttf',windows/'segoeuib.ttf','Windows Segoe UI'),
            (windows/'arial.ttf',windows/'arialbd.ttf','Windows Arial'),
            (windows/'DejaVuSans.ttf',windows/'DejaVuSans-Bold.ttf','Windows DejaVu'),
        ])
    elif system == 'Darwin':
        paths.extend([
            (Path('/Library/Fonts/Arial.ttf'),Path('/Library/Fonts/Arial Bold.ttf'),'macOS Arial'),
            (Path('/System/Library/Fonts/Supplemental/Arial.ttf'),Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf'),'macOS Arial Supplemental'),
        ])
    else:
        for folder in ('/usr/share/fonts/truetype/dejavu', '/usr/local/share/fonts', '/usr/share/fonts'):
            f=Path(folder)
            paths.append((f/'DejaVuSans.ttf',f/'DejaVuSans-Bold.ttf','Linux DejaVu'))
    # Bitstream Vera belongs to ReportLab's own installation on Windows/Linux/macOS.
    paths.append((package_fonts/'Vera.ttf',package_fonts/'VeraBd.ttf','ReportLab Bitstream Vera'))
    return paths

def register_portable_fonts(platform_name: str | None = None, windows_dir: str | None = None):
    attempted=[]
    for regular,bold,label in font_candidates(platform_name,windows_dir):
        if not regular.is_file() or not bold.is_file():
            attempted.append(f'{label}: missing')
            continue
        try:
            pdfmetrics.registerFont(TTFont('DV',str(regular)))
            pdfmetrics.registerFont(TTFont('DVB',str(bold)))
            pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
            return {'provider':label,'regular':str(regular),'bold':str(bold)}
        except Exception as exc:
            attempted.append(f'{label}: {type(exc).__name__}')
    raise RuntimeError('No usable TrueType font found. Tried: '+', '.join(attempted))
