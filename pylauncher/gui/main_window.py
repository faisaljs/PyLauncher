from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
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

from ..config import (
    effective_settings,
    load_config,
    save_config,
    set_version_override,
)
from ..launcher import (
    DEFAULT_GAME_DIR,
    detect_java_major,
    required_java_major,
)
from ..manifest import fetch_manifest, fetch_version
from .java_discovery import discover_java
from .log_panel import LogPanel
from .settings_dialog import SettingsDialog
from .version_list import VersionListWidget
from .worker import Bridge, WorkerPool, run_install, run_launch, run_load_versions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyLauncher")
        self.resize(960, 680)

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
        self._version_data_cache = {}
        self._manifest = None
        self._selected = ("", False)
        self._discovered_java = discover_java()

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

        self.java_combo = QComboBox()
        self.java_combo.setEditable(True)
        self._populate_java_combo(self.cfg.get("java", "java"))
        self.java_combo.currentTextChanged.connect(self._on_java_changed)

        form.addRow("Username:", self.username_edit)
        form.addRow("Memory (MB):", self.memory_edit)
        form.addRow("Java:", self.java_combo)
        play_layout.addLayout(form)

        self.java_banner = QLabel("")
        self.java_banner.setWordWrap(True)
        self.java_banner.setVisible(False)
        self.java_banner.setStyleSheet(
            "QLabel { background-color: #4a1a1a; color: #ffb3b3; "
            "padding: 8px; border-radius: 4px; }"
        )
        play_layout.addWidget(self.java_banner)

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
        toolbar.addAction("Settings").triggered.connect(self._on_settings)
        toolbar.addAction("Reload Versions").triggered.connect(self._load_versions)
        toolbar.addAction("Rescan Java").triggered.connect(self._rescan_java)

    def _populate_java_combo(self, current: str) -> None:
        self.java_combo.blockSignals(True)
        self.java_combo.clear()
        candidates = list(self._discovered_java)
        if current and current not in candidates:
            candidates.insert(0, current)
        if not candidates:
            candidates = [current or "java"]
        for c in candidates:
            self.java_combo.addItem(c)
        idx = self.java_combo.findText(current)
        if idx >= 0:
            self.java_combo.setCurrentIndex(idx)
        else:
            self.java_combo.setEditText(current)
        self.java_combo.blockSignals(False)

    def _rescan_java(self) -> None:
        current = self.java_combo.currentText()
        self._discovered_java = discover_java()
        self._populate_java_combo(current)
        self.log_panel.append(f"[P] Rescanned Java: {len(self._discovered_java)} candidates")

    def _load_versions(self) -> None:
        self.status_label.setText("Loading versions...")
        self.pool.submit(run_load_versions, self.bridge, self.game_dir)

    def _on_versions_loaded(self, rows: list) -> None:
        self.version_list.set_versions(rows)
        self.status_label.setText(f"{len(rows)} versions available.")
        installed_count = sum(1 for _, _, i in rows if i)
        self.log_panel.append(f"[P] Loaded {len(rows)} versions ({installed_count} installed)")

    def _on_version_selected(self, version_id: str, installed: bool) -> None:
        if self._busy:
            return
        self._selected = (version_id, installed)
        self.play_button.setText("PLAY" if installed else "INSTALL")

        eff = effective_settings(self.cfg, version_id)
        self.memory_edit.setText(str(eff["memory_mb"]))

        data = self._load_version_data(version_id)
        chosen = eff["java"]
        if data is not None:
            required = required_java_major(data)
            current_major = detect_java_major(chosen)
            if current_major is None or current_major < required:
                better = self._find_java_for(required)
                if better:
                    chosen = better
                    self.log_panel.append(
                        f"[P] Auto-selected {chosen} for {version_id} (needs Java {required}+)"
                    )

        idx = self.java_combo.findText(chosen)
        if idx >= 0:
            self.java_combo.setCurrentIndex(idx)
        else:
            self.java_combo.setEditText(chosen)

        self.status_label.setText(
            f"{version_id} — {'installed' if installed else 'not installed'}"
        )
        self._update_java_banner(version_id)

    def _find_java_for(self, required_major: int):
        for path in self._discovered_java:
            major = detect_java_major(path)
            if major is not None and major >= required_major:
                return path
        return None

    def _load_version_data(self, version_id: str):
        if version_id in self._version_data_cache:
            return self._version_data_cache[version_id]
        try:
            if self._manifest is None:
                self._manifest = fetch_manifest(self.game_dir)
            data = fetch_version(version_id, self._manifest, self.game_dir)
            self._version_data_cache[version_id] = data
            return data
        except Exception as e:
            self.log_panel.append(f"[P] Could not load version JSON for {version_id}: {e}")
            return None

    def _update_java_banner(self, version_id: str) -> None:
        if not version_id:
            self.java_banner.setVisible(False)
            return
        data = self._load_version_data(version_id)
        if data is None:
            self.java_banner.setVisible(False)
            return

        required = required_java_major(data)
        java_path = self.java_combo.currentText() or "java"
        actual = detect_java_major(java_path)

        if actual is None:
            self.java_banner.setText(
                f"Java not found at '{java_path}'. Pick a valid JDK from the list."
            )
            self.java_banner.setVisible(True)
            return

        if actual < required:
            self.java_banner.setText(
                f"{version_id} requires Java {required}+ but '{java_path}' is Java {actual}. "
                f"No matching JDK found in scanned paths. Install JDK {required} to play this version."
            )
            self.java_banner.setVisible(True)
        else:
            self.java_banner.setVisible(False)

    def _on_java_changed(self, _text: str) -> None:
        version_id, _ = self._selected
        if version_id:
            self._update_java_banner(version_id)

    def _selected_version(self) -> tuple:
        return self._selected

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
        java = self.java_combo.currentText().strip() or "java"

        self._busy = True
        self.play_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        self.cfg["username"] = username
        self.cfg = set_version_override(self.cfg, version_id, java=java, memory_mb=memory)
        save_config(self.cfg)

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
            run_launch, self.bridge, version_id, username, self.game_dir, java, memory,
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
        version_id, installed = self._selected
        self.play_button.setText("PLAY" if installed else "INSTALL")
        self.progress.setVisible(False)

    def _on_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec():
            self.cfg = dlg.result_config()
            save_config(self.cfg)
            self.username_edit.setText(self.cfg.get("username", "Player"))
            self.memory_edit.setText(str(self.cfg.get("memory_mb", 2048)))
            self._populate_java_combo(self.cfg.get("java", "java"))

    def closeEvent(self, event) -> None:
        self.pool.shutdown()
        super().closeEvent(event)