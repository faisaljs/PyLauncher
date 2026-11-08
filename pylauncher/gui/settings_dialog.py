from PySide6.QtWidgets import (
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


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
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
        form.addRow("Memory (MB):", self.memory_spin)

        java_row = QWidget()
        java_layout = QHBoxLayout(java_row)
        java_layout.setContentsMargins(0, 0, 0, 0)
        self.java_edit = QLineEdit(self._cfg.get("java", "java"))
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse_java)
        java_layout.addWidget(self.java_edit)
        java_layout.addWidget(browse)
        form.addRow("Java executable:", java_row)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_java(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Java executable", self.java_edit.text() or "/"
        )
        if path:
            self.java_edit.setText(path)

    def result_config(self) -> dict:
        cfg = dict(self._cfg)
        cfg["username"] = self.username_edit.text().strip() or "Player"
        cfg["default_version"] = self.version_edit.text().strip() or "1.20.4"
        cfg["memory_mb"] = self.memory_spin.value()
        cfg["java"] = self.java_edit.text().strip() or "java"
        return cfg