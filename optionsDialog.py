from Qt import QtWidgets, QtGui, QtCore


class OptionsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(OptionsDialog, self).__init__(parent)
        self.setWindowTitle('Options')
        self.setModal(False)

        # Basic layout and placeholder content
        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel('Preferences and settings will appear here.')
        try:
            font = QtGui.QFont('Bahnschrift', 10)
            label.setFont(font)
        except Exception:
            pass

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)

        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(button_box)

        self.setLayout(layout)
