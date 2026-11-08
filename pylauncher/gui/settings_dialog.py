from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .java_discovery import discover_java


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self._cfg = dict(cfg)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.username_edit = QLineEdit(self._cfg.get("username", "Player"))
        form.addRow("Default username:", self.username_edit)

        self.version_edit = QLineEdit(self._cfg.get("default_version", "1.20.4"))
        form.addRow("Default version:", self.version_edit)

        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(512, 32768)
        self.memory_spin.setSingleStep(256)
        self.memory_spin.setValue(int(self._cfg.get("memory_mb", 2048)))
        form.addRow("Default memory (MB):", self.memory_spin)

        java_row = QWidget()
        java_layout = QHBoxLayout(java_row)
        java_layout.setContentsMargins(0, 0, 0, 0)
        self.java_combo = QComboBox()
        self.java_combo.setEditable(True)
        current = self._cfg.get("java", "java")
        candidates = discover_java()
        if current and current not in candidates:
            candidates.insert(0, current)
        if not candidates:
            candidates = [current]
        for c in candidates:
            self.java_combo.addItem(c)
        idx = self.java_combo.findText(current)
        if idx >= 0:
            self.java_combo.setCurrentIndex(idx)
        else:
            self.java_combo.setEditText(current)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse_java)
        java_layout.addWidget(self.java_combo)
        java_layout.addWidget(browse)
        form.addRow("Default Java:", java_row)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Java executable", self.java_combo.currentText() or "/"
        )
        if path:
            idx = self.java_combo.findText(path)
            if idx >= 0:
                self.java_combo.setCurrentIndex(idx)
            else:
                self.java_combo.setEditText(path)

    def result_config(self) -> dict:
        cfg = dict(self._cfg)
        cfg["username"] = self.username_edit.text().strip() or "Player"
        cfg["default_version"] = self.version_edit.text().strip() or "1.20.4"
        cfg["memory_mb"] = self.memory_spin.value()
        cfg["java"] = self.java_combo.currentText().strip() or "java"
        return cfg