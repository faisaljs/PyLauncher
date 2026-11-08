from PySide6.QtWidgets import (
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._expanded = True
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        header = QHBoxLayout()
        self.toggle_button = QPushButton("Hide")
        self.toggle_button.setFixedWidth(60)
        self.toggle_button.clicked.connect(self._toggle)
        header.addStretch(1)
        header.addWidget(self.toggle_button)
        layout.addLayout(header)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(5000)
        self.text.setStyleSheet(
            "QPlainTextEdit { background-color: #111; color: #d8d8d8; "
            "font-family: 'Monospace'; font-size: 11px; }"
        )
        layout.addWidget(self.text)

    def append(self, line: str) -> None:
        self.text.appendPlainText(line)
        sb = self.text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self.text.setVisible(self._expanded)
        self.toggle_button.setText("Hide" if self._expanded else "Show")