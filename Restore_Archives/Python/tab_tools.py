
# gui_tabs/tab_tools.py
import sys, subprocess
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QLineEdit, QFileDialog

TOOLS = [
    ("Master Sweep", "master_sweep.py"),
    ("Compare Ideal vs Fremlin", "example_compare_ideal_vs_fremlin_4_1.py"),
    ("Showcase embedded Ideal AB", "example_showcase_embedded_ideal_ab_by_id.py"),
    ("Generator (CLI) generate_knot_fseries", "generate_knot_fseries.py"),
    ("Canon Pipeline", "Swirl_String_TheoryCanon_Pipeline.py"),
    ("Atom mass invariant SEMF", "SST_ATOM_MASS_INVARIANT_SEMF_canonical_only.py"),
    ("Filament Hopf demo", "sst_native_filament_hopf.py"),
    ("Parse knots", "parse_knots.py"),
]

class TabTools(QWidget):
    def __init__(self):
        super().__init__()
        self.base_dir = Path.cwd()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("Base dir:"))
        self.base_edit = QLineEdit(str(self.base_dir))
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse)
        row.addWidget(self.base_edit)
        row.addWidget(btn)
        layout.addLayout(row)

        for label, fname in TOOLS:
            b = QPushButton(f"Run: {label}")
            b.clicked.connect(lambda _, f=fname: self._run(f))
            layout.addWidget(b)

        layout.addStretch(1)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Choose base directory", self.base_edit.text())
        if d:
            self.base_edit.setText(d)

    def _run(self, fname: str):
        base = Path(self.base_edit.text()).expanduser().resolve()
        py = base / fname
        if not py.exists():
            print(f"[ERR] not found: {py}")
            return
        cmd = [sys.executable, str(py)]
        print(f"[launch] {' '.join(cmd)} (cwd={base})")
        subprocess.Popen(cmd, cwd=str(base))
