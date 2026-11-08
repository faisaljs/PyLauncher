from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class VersionListWidget(QWidget):
    selection_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self._rows: list = []
        self._filter = "all"
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        filter_row = QHBoxLayout()
        self.filter_box = QComboBox()
        self.filter_box.addItems(["All", "Release", "Snapshot", "Old Beta", "Old Alpha"])
        self.filter_box.currentTextChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.filter_box)
        layout.addLayout(filter_row)

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_current_changed)
        layout.addWidget(self.list)

    def set_versions(self, rows: list) -> None:
        self._rows = rows
        self._repopulate()

    def _on_filter_changed(self, text: str) -> None:
        mapping = {
            "All": "all",
            "Release": "release",
            "Snapshot": "snapshot",
            "Old Beta": "old_beta",
            "Old Alpha": "old_alpha",
        }
        self._filter = mapping.get(text, "all")
        self._repopulate()

    def _repopulate(self) -> None:
        current = self.current_version()[0]
        self.list.blockSignals(True)
        self.list.clear()
        for version_id, vtype, installed in self._rows:
            if self._filter != "all" and vtype != self._filter:
                continue
            label = f"{version_id}"
            if installed:
                label = f"{version_id}  *"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, (version_id, installed))
            self.list.addItem(item)
            if version_id == current:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        if self.list.currentItem() is None and self.list.count() > 0:
            self.list.setCurrentRow(0)

    def _on_current_changed(self, current, _prev) -> None:
        if current is None:
            return
        version_id, installed = current.data(Qt.UserRole)
        self.selection_changed.emit(version_id, installed)

    def current_version(self) -> tuple:
        item = self.list.currentItem()
        if item is None:
            return ("", False)
        return item.data(Qt.UserRole)