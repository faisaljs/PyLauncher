from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..config import load_config, save_config
from ..launcher import DEFAULT_GAME_DIR
from .log_panel import LogPanel
from .settings_dialog import SettingsDialog
from .version_list import VersionListWidget
from .worker import Bridge, WorkerPool, run_install, run_launch, run_load_versions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLauncher")
        self.resize(920, 640)

        self.game_dir = DEFAULT_GAME_DIR
        self.cfg = load_config()
        self.pool = WorkerPool(max_workers=4)
        self.bridge = Bridge()
        self.bridge.progress.connect(self._on_progress)
        self.bridge.log.connect(self._on_log)
        self.bridge.failed.connect(self._on_failed)
        self.bridge.finished.connect(self._on_install_finished)
        self.bridge.game_line.connect(self._on_game_line)
        self.bridge.game_exited.connect(self._on_game_exited)
        self.bridge.versions_loaded.connect(self._on_versions_loaded)

        self._busy = False
        self._build_ui()
        self._load_versions()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        self.version_list = VersionListWidget()
        self.version_list.selection_changed.connect(self._on_version_selected)

        play_panel = QWidget()
        play_layout = QVBoxLayout(play_panel)
        play_layout.setContentsMargins(12, 12, 12, 12)

        form = QFormLayout()
        self.username_edit = QLineEdit(self.cfg.get("username", "Player"))
        self.memory_edit = QLineEdit(str(self.cfg.get("memory_mb", 2048)))
        self.java_edit = QLineEdit(self.cfg.get("java", "java"))
        form.addRow("Username:", self.username_edit)
        form.addRow("Memory (MB):", self.memory_edit)
        form.addRow("Java:", self.java_edit)
        play_layout.addLayout(form)

        self.play_button = QPushButton("PLAY")
        self.play_button.setMinimumHeight(48)
        self.play_button.clicked.connect(self._on_play_clicked)
        play_layout.addWidget(self.play_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%v/%m")
        self.progress.setVisible(False)
        play_layout.addWidget(self.progress)

        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        play_layout.addWidget(self.status_label)

        play_layout.addStretch(1)

        top = QSplitter(Qt.Horizontal)
        top.addWidget(self.version_list)
        top.addWidget(play_panel)
        top.setStretchFactor(0, 1)
        top.setStretchFactor(1, 2)

        self.log_panel = LogPanel()

        main = QSplitter(Qt.Vertical)
        main.addWidget(top)
        main.addWidget(self.log_panel)
        main.setStretchFactor(0, 3)
        main.setStretchFactor(1, 2)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main)

        toolbar = self.addToolBar("Main")
        settings_action = toolbar.addAction("Settings")
        settings_action.triggered.connect(self._on_settings)
        reload_action = toolbar.addAction("Reload Versions")
        reload_action.triggered.connect(self._load_versions)

    def _load_versions(self) -> None:
        self.status_label.setText("Loading versions...")
        self.pool.submit(run_load_versions, self.bridge, self.game_dir)

    def _on_versions_loaded(self, rows: list) -> None:
        self.version_list.set_versions(rows)
        self.status_label.setText(f"{len(rows)} versions available.")
        installed_count = sum(1 for _, _, installed in rows if installed)
        self.log_panel.append(f"[P] Loaded {len(rows)} versions ({installed_count} installed)")

    def _on_version_selected(self, version_id: str, installed: bool) -> None:
        if self._busy:
            return
        self.play_button.setText("PLAY" if installed else "INSTALL")
        self.status_label.setText(
            f"{version_id} — {'installed' if installed else 'not installed'}"
        )

    def _selected_version(self) -> tuple:
        return self.version_list.current_version()

    def _on_play_clicked(self) -> None:
        if self._busy:
            return
        version_id, installed = self._selected_version()
        if not version_id:
            QMessageBox.information(self, "PyLauncher", "Pick a version first.")
            return

        username = self.username_edit.text().strip() or "Player"
        try:
            memory = int(self.memory_edit.text().strip() or "2048")
        except ValueError:
            QMessageBox.warning(self, "PyLauncher", "Memory must be a number.")
            return
        java = self.java_edit.text().strip() or "java"

        self._busy = True
        self.play_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self._save_config(username, memory, java)

        if installed:
            self._start_launch(version_id, username, java, memory)
        else:
            self._start_install(version_id)

    def _start_install(self, version_id: str) -> None:
        self.play_button.setText("INSTALLING...")
        self.log_panel.append(f"[P] Installing {version_id}...")
        self.pool.submit(run_install, self.bridge, version_id, self.game_dir)

    def _start_launch(self, version_id: str, username: str, java: str, memory: int) -> None:
        self.play_button.setText("RUNNING...")
        self.log_panel.append(f"[P] Launching {version_id} as {username}...")
        self.pool.submit(
            run_launch,
            self.bridge, version_id, username, self.game_dir, java, memory,
        )

    def _on_progress(self, stage: str, current: int, total: int) -> None:
        if total <= 0:
            self.progress.setRange(0, 0)
            return
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.status_label.setText(f"{stage} — {current}/{total}")

    def _on_log(self, line: str) -> None:
        self.log_panel.append(f"[P] {line}")

    def _on_failed(self, trace: str) -> None:
        self.log_panel.append(f"[ERROR]\n{trace}")
        self.status_label.setText("Error — see log.")
        self._reset_after_job()
        QMessageBox.critical(self, "PyLauncher", "Job failed. See log for details.")

    def _on_install_finished(self, version_id: str) -> None:
        self.status_label.setText(f"{version_id} installed.")
        self._reset_after_job()
        self._load_versions()

    def _on_game_line(self, line: str) -> None:
        self.log_panel.append(line)
        self.status_label.setText("Game running...")

    def _on_game_exited(self, code: int) -> None:
        self.log_panel.append(f"[P] Game exited ({code}).")
        self.status_label.setText("Ready.")
        self._reset_after_job()

    def _reset_after_job(self) -> None:
        self._busy = False
        self.play_button.setEnabled(True)
        version_id, installed = self._selected_version()
        self.play_button.setText("PLAY" if installed else "INSTALL")
        if self.progress.value() >= self.progress.maximum() or not self._busy:
            self.progress.setVisible(False)

    def _save_config(self, username: str, memory: int, java: str) -> None:
        self.cfg["username"] = username
        self.cfg["memory_mb"] = memory
        self.cfg["java"] = java
        save_config(self.cfg)

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            self.cfg = dlg.result_config()
            save_config(self.cfg)
            self.username_edit.setText(self.cfg.get("username", "Player"))
            self.memory_edit.setText(str(self.cfg.get("memory_mb", 2048)))
            self.java_edit.setText(self.cfg.get("java", "java"))

    def closeEvent(self, event) -> None:
        self.pool.shutdown()
        super().closeEvent(event)