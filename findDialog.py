from Qt import QtWidgets, QtCore, QtGui


class FindDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(FindDialog, self).__init__(parent)
        self.setWindowTitle('Find')
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        # Text to find
        self.find_edit = QtWidgets.QLineEdit()
        try:
            self.find_edit.setPlaceholderText('Text to find…')
        except Exception:
            pass

        # Options
        self.whole_word_cb = QtWidgets.QCheckBox('Match Whole Word')
        self.match_case_cb = QtWidgets.QCheckBox('Match Case')
        self.use_regex_cb = QtWidgets.QCheckBox('Use Regular Expression')

        self.regex_edit = QtWidgets.QLineEdit()
        self.regex_edit.setEnabled(False)
        try:
            self.regex_edit.setPlaceholderText('Regular expression…')
        except Exception:
            pass

        # Enable/disable regex field
        self.use_regex_cb.toggled.connect(self.regex_edit.setEnabled)
        self.use_regex_cb.toggled.connect(lambda on: self.find_edit.setEnabled(not on))

        # Assemble form
        form.addRow('Find what:', self.find_edit)
        form.addRow(self.whole_word_cb)
        form.addRow(self.match_case_cb)
        form.addRow(self.use_regex_cb)
        form.addRow('Regex:', self.regex_edit)

        layout.addLayout(form)

        # Buttons
        # Standard buttons: use Ok as "Find" for compatibility across Qt versions
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        try:
            ok_btn = buttons.button(QtWidgets.QDialogButtonBox.Ok)
            if ok_btn is not None:
                ok_btn.setText('Find')
        except Exception:
            pass
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return {
            'text': self.find_edit.text(),
            'whole_word': self.whole_word_cb.isChecked(),
            'match_case': self.match_case_cb.isChecked(),
            'use_regex': self.use_regex_cb.isChecked(),
            'regex': self.regex_edit.text(),
        }
