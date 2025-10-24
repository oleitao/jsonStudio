"""
Main window to launch JsonViewer
"""


import ast
import json
import os
import sys

from Qt import QtWidgets, QtCore, QtGui
from Qt import _loadUi

from qjsonnode import QJsonNode
from qjsonview import QJsonView
from qjsonmodel import QJsonModel
from codeEditor.highlighter.jsonHighlight import JsonHighlighter
from findDialog import FindDialog
from optionsDialog import OptionsDialog
from textEditDialog import TextEditDialog
import platform
try:
    from Qt import QtPrintSupport
except Exception:  # pragma: no cover
    QtPrintSupport = None

try:
    import jsonschema
    from jsonschema import ValidationError
    from jsonschema.exceptions import SchemaError
    from jsonschema.validators import validator_for
except Exception:  # pragma: no cover
    jsonschema = None
    class ValidationError(Exception):
        pass
    class SchemaError(Exception):
        pass
    def validator_for(schema):
        raise SchemaError('jsonschema not available')

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(MODULE_PATH, 'ui', 'JsonStudio.ui')
TEST_DICT = {}
STYLE_PREF_PATH = os.path.join(MODULE_PATH, 'ui', 'settings.json')
ICON_PATH = os.path.join(MODULE_PATH, 'snap', 'gui', 'logo.png')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        _loadUi(UI_PATH, self)
        # Set window icon if available
        try:
            if os.path.exists(ICON_PATH):
                self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        except Exception:
            pass

        self.ui_tree_view = QJsonView()
        self.ui_tree_view.setStyleSheet('QWidget{font: 10pt "Bahnschrift";}')
        self.ui_grid_layout.addWidget(self.ui_tree_view, 1, 0)
        try:
            self.ui_tree_view.fileDropped.connect(self._load_json_from_path)
        except Exception:
            pass

        # schema/state
        self._schema = None
        self._schema_path = None
        # style state
        self._style_path = None
        self._current_builtin_style = 'Default'
        self._style_actions = []
        # dialogs
        self._options_dialog = None

        root = QJsonNode.load(TEST_DICT)
        self._model = QJsonModel(root, self)

        # proxy model
        self._proxyModel = QtCore.QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self._model)
        self._proxyModel.setDynamicSortFilter(False)
        self._proxyModel.setSortRole(QJsonModel.sortRole)
        self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._proxyModel.setFilterRole(QJsonModel.filterRole)
        self._proxyModel.setFilterKeyColumn(0)

        self.ui_tree_view.setModel(self._proxyModel)

        self.ui_out_btn.clicked.connect(self.updateBrowser)
        self.ui_update_btn.clicked.connect(self.updateModel)
        # schema related
        if hasattr(self, 'ui_validate_btn'):
            self.ui_validate_btn.clicked.connect(self.validateJson)
        if hasattr(self, 'ui_back_to_data_btn'):
            self.ui_back_to_data_btn.clicked.connect(self.backToData)
        if hasattr(self, 'ui_load_json_btn'):
            self.ui_load_json_btn.clicked.connect(self.loadJsonToRaw)
        if hasattr(self, 'ui_clear_btn'):
            self.ui_clear_btn.clicked.connect(self.clearAll)
        if hasattr(self, 'ui_load_style_btn'):
            self.ui_load_style_btn.clicked.connect(self.loadStyle)
        if hasattr(self, 'ui_reset_style_btn'):
            self.ui_reset_style_btn.clicked.connect(self.resetStyle)
        if hasattr(self, 'ui_schema_status_label'):
            self.ui_schema_status_label.setText('No schema loaded')
        if hasattr(self, 'ui_style_status_label'):
            self.ui_style_status_label.setText('Style: Default')

        # Json Viewer (start empty)
        JsonHighlighter(self.ui_view_edit.document())
        try:
            self.ui_view_edit.setPlaceholderText('Paste or type JSON here…')
        except Exception:
            pass
        try:
            self.ui_view_edit.setAcceptDrops(True)
            self.ui_view_edit.installEventFilter(self)
            # Also filter the viewport for drag events (Qt sometimes delivers here)
            if hasattr(self.ui_view_edit, 'viewport'):
                self.ui_view_edit.viewport().installEventFilter(self)
        except Exception:
            pass
        # Build top menu bar for styles
        self._initMenus()
        # Load previously selected style if available
        self._load_saved_style()

    def updateModel(self):
        text = self.ui_view_edit.toPlainText()
        jsonDict = ast.literal_eval(text)
        root = QJsonNode.load(jsonDict)

        self._model = QJsonModel(root)
        self._proxyModel.setSourceModel(self._model)

    def updateBrowser(self):
        self.ui_view_edit.clear()
        output = self.ui_tree_view.asDict(None)
        jsonDict = json.dumps(output, indent=4, sort_keys=True)
        self.ui_view_edit.setPlainText(str(jsonDict))

    def pprint(self):
        output = self.ui_tree_view.asDict(self.ui_tree_view.getSelectedIndices())
        jsonDict = json.dumps(output, indent=4, sort_keys=True)

        print(jsonDict)

    # JSON Schema support
    def loadSchema(self):
        """Open a file dialog and load a JSON Schema file."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select JSON Schema',
            os.path.expanduser('~'),
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Schema Error', f'Failed to load schema:\n{e}')
            return

        self._schema = schema
        if hasattr(self, 'ui_schema_status_label'):
            self.ui_schema_status_label.setText(f'Loaded: {os.path.basename(path)}')

    def backToData(self):
        """Show current tree data in Raw View (right pane)."""
        self.updateBrowser()

    def loadJsonToRaw(self):
        """Open a JSON file, show it in Raw View, and set it as the schema for Validate."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select JSON File',
            os.path.expanduser('~'),
            'JSON Files (*.json);;All Files (*)'
        )
        if not path:
            return
        self._load_json_from_path(path)

    def _load_json_from_path(self, path):
        """Load JSON from a filesystem path into both editors (Raw + UI)."""
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Load Error', f'Failed to load JSON file:\n{e}')
            return


        try:
            self.ui_view_edit.setReadOnly(False)
        except Exception:
            pass
        try:
            text = json.dumps(data, indent=4, sort_keys=True)
        except Exception:
            text = str(data)
        self.ui_view_edit.setPlainText(text)

        try:
            root = QJsonNode.load(data)
            self._model = QJsonModel(root, self)
            self._proxyModel.setSourceModel(self._model)
            self.ui_tree_view.setModel(self._proxyModel)
        except Exception:
            pass

        self._schema = data
        if hasattr(self, 'ui_schema_status_label'):
            try:
                self.ui_schema_status_label.setText(f'Schema: {os.path.basename(path)}')
            except Exception:
                pass

    def _get_current_json(self):
        """Parse current text view as JSON; fallback to tree if empty."""
        text = self.ui_view_edit.toPlainText().strip()
        if text:
            try:
                return json.loads(text)
            except Exception as e:
                raise ValueError(f'Invalid JSON in Raw View: {e}')
        # fallback to model
        return self.ui_tree_view.asDict(None)

    def eventFilter(self, obj, event):
        try:
            edit = getattr(self, 'ui_view_edit', None)
            if obj is edit or (edit is not None and obj is getattr(edit, 'viewport', lambda: None)()):
                if event.type() == QtCore.QEvent.DragEnter:
                    md = event.mimeData()
                    if md and md.hasUrls():
                        event.acceptProposedAction()
                        return True
                elif event.type() == QtCore.QEvent.DragMove:
                    md = event.mimeData()
                    if md and md.hasUrls():
                        event.acceptProposedAction()
                        return True
                elif event.type() == QtCore.QEvent.Drop:
                    md = event.mimeData()
                    if md and md.hasUrls():
                        for url in md.urls():
                            if url.isLocalFile():
                                self._load_json_from_path(url.toLocalFile())
                                break
                        event.acceptProposedAction()
                        return True
        except Exception:
            pass
        return super(MainWindow, self).eventFilter(obj, event)

    def validateJson(self):
        """Validate that the JSON (prefer Raw View) is a valid JSON Schema."""
        if jsonschema is None:
            QtWidgets.QMessageBox.warning(
                self,
                'Dependency Missing',
                'jsonschema is not installed. Install with:\n\n  pip install jsonschema'
            )
            return

        # Prefer validating the schema as shown/edited in the Raw View
        schema_candidate = None
        text = self.ui_view_edit.toPlainText().strip()
        if text:
            try:
                schema_candidate = json.loads(text)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, 'Parse Error', f'Cannot parse Raw View as JSON:\n{e}')
                return
        else:
            schema_candidate = self._schema

        if not isinstance(schema_candidate, dict):
            QtWidgets.QMessageBox.information(self, 'No Schema', 'Load or paste a JSON Schema to validate.')
            return

        try:
            cls = validator_for(schema_candidate)
            cls.check_schema(schema_candidate)
        except SchemaError as e:
            QtWidgets.QMessageBox.critical(self, 'Invalid JSON Schema', str(e))
            return

        QtWidgets.QMessageBox.information(self, 'Schema Validation', 'JSON Schema is valid.')

    def clearAll(self):
        """Clear Raw View, filter, tree model, and loaded schema."""
        # clear text panel
        try:
            self.ui_view_edit.setReadOnly(False)
        except Exception:
            pass
        self.ui_view_edit.clear()
        # clear filter
        try:
            self.ui_filter_edit.clear()
        except Exception:
            pass
        # clear model/tree
        try:
            self._model.clear()
            self._proxyModel.setSourceModel(self._model)
        except Exception:
            pass
        # clear schema state
        self._schema = None
        try:
            self._schema_path = None
        except Exception:
            pass
        if hasattr(self, 'ui_schema_status_label'):
            self.ui_schema_status_label.setText('No schema loaded')

    # Stylesheet support and menubar
    def _initMenus(self):
        try:
            menubar = self.menuBar()
        except Exception:
            menubar = None
        if not menubar:
            return
        # Show menubar inside window (helpful on macOS)
        try:
            menubar.setNativeMenuBar(False)
        except Exception:
            pass

        # File menu
        file_menu = menubar.addMenu('File')

        new_action = QtWidgets.QAction('New File...', self)
        try:
            new_action.setShortcut(QtGui.QKeySequence.New)
        except Exception:
            pass
        new_action.triggered.connect(self.newFile)
        file_menu.addAction(new_action)

        open_action = QtWidgets.QAction('Open...', self)
        try:
            open_action.setShortcut(QtGui.QKeySequence.Open)
        except Exception:
            pass
        open_action.triggered.connect(self.loadJsonToRaw)
        file_menu.addAction(open_action)

        options_action = QtWidgets.QAction('Options', self)
        try:
            options_action.setShortcut(QtGui.QKeySequence.Preferences)
        except Exception:
            pass
        options_action.triggered.connect(self.showOptions)
        file_menu.addAction(options_action)

        print_action = QtWidgets.QAction('Print...', self)
        try:
            print_action.setShortcut(QtGui.QKeySequence.Print)
        except Exception:
            pass
        print_action.triggered.connect(self.printCurrent)
        file_menu.addAction(print_action)

        exit_action = QtWidgets.QAction('Exit', self)
        try:
            exit_action.setShortcut(QtGui.QKeySequence.Quit)
        except Exception:
            pass
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        style_menu = menubar.addMenu('Style')
        themes_menu = style_menu.addMenu('Themes')

        # Build actions from .qss files in ui folder
        self._style_actions = []
        # Default action
        default_action = QtWidgets.QAction('Default', self)
        default_action.setCheckable(True)
        default_action.setChecked(True)
        default_action.triggered.connect(self.resetStyle)
        themes_menu.addAction(default_action)
        self._style_actions.append(default_action)

        for name, path in self._styles_in_ui().items():
            action = QtWidgets.QAction(name, self)
            action.setCheckable(True)
            action.setChecked(False)
            action.triggered.connect(lambda checked, p=path, n=name: self.applyStyleFile(p, n))
            themes_menu.addAction(action)
            self._style_actions.append(action)

        style_menu.addSeparator()
        load_qss_action = QtWidgets.QAction('Load .qss…', self)
        load_qss_action.triggered.connect(self.loadStyle)
        style_menu.addAction(load_qss_action)

        reset_style_action = QtWidgets.QAction('Reset', self)
        reset_style_action.triggered.connect(self.resetStyle)
        style_menu.addAction(reset_style_action)

        # Edit menu (after Style)
        edit_menu = menubar.addMenu('Edit')

        redo_action = QtWidgets.QAction('Redo', self)
        try:
            redo_action.setShortcut(QtGui.QKeySequence.Redo)
        except Exception:
            pass
        redo_action.triggered.connect(self.editRedo)
        edit_menu.addAction(redo_action)

        undo_action = QtWidgets.QAction('Undo', self)
        try:
            undo_action.setShortcut(QtGui.QKeySequence.Undo)
        except Exception:
            pass
        undo_action.triggered.connect(self.editUndo)
        edit_menu.addAction(undo_action)

        edit_menu.addSeparator()

        cut_action = QtWidgets.QAction('Cut', self)
        try:
            cut_action.setShortcut(QtGui.QKeySequence.Cut)
        except Exception:
            pass
        cut_action.triggered.connect(self.editCut)
        edit_menu.addAction(cut_action)

        copy_action = QtWidgets.QAction('Copy', self)
        try:
            copy_action.setShortcut(QtGui.QKeySequence.Copy)
        except Exception:
            pass
        copy_action.triggered.connect(self.editCopy)
        edit_menu.addAction(copy_action)

        paste_action = QtWidgets.QAction('Paste', self)
        try:
            paste_action.setShortcut(QtGui.QKeySequence.Paste)
        except Exception:
            pass
        paste_action.triggered.connect(self.editPaste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        find_action = QtWidgets.QAction('Find', self)
        try:
            find_action.setShortcut(QtGui.QKeySequence.Find)
        except Exception:
            pass
        find_action.triggered.connect(self.editFind)
        edit_menu.addAction(find_action)

        replace_action = QtWidgets.QAction('Replace', self)
        try:
            replace_action.setShortcut(QtGui.QKeySequence.Replace)
        except Exception:
            pass
        replace_action.triggered.connect(self.editReplace)
        edit_menu.addAction(replace_action)

        edit_menu.addSeparator()

        toggle_line_comment_action = QtWidgets.QAction('Toggle Line Comment', self)
        try:
            toggle_line_comment_action.setShortcut(QtGui.QKeySequence('Ctrl+/'))
        except Exception:
            pass
        toggle_line_comment_action.triggered.connect(self.toggleLineComment)
        edit_menu.addAction(toggle_line_comment_action)

        toggle_block_comment_action = QtWidgets.QAction('Toggle Block Comment', self)
        toggle_block_comment_action.triggered.connect(self.toggleBlockComment)
        edit_menu.addAction(toggle_block_comment_action)

        # View menu (after Edit)
        view_menu = menubar.addMenu('View')

        hide_code_action = QtWidgets.QAction('Hide Json Code Editor', self)
        hide_code_action.triggered.connect(self.hideJsonCodeEditor)
        view_menu.addAction(hide_code_action)

        hide_ui_action = QtWidgets.QAction('Hide Json UI Editor', self)
        hide_ui_action.triggered.connect(self.hideJsonUiEditor)
        view_menu.addAction(hide_ui_action)

        show_both_action = QtWidgets.QAction('Show Json Code/UI Editors', self)
        show_both_action.triggered.connect(self.showJsonEditors)
        view_menu.addAction(show_both_action)

        # Help menu (after View)
        help_menu = menubar.addMenu('Help')

        about_action = QtWidgets.QAction('About JsonStudio', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)

        version_notes_action = QtWidgets.QAction('Version Notes', self)
        version_notes_action.triggered.connect(self.showVersionNotes)
        help_menu.addAction(version_notes_action)

        report_action = QtWidgets.QAction('Create Problem Report', self)
        report_action.triggered.connect(self.createProblemReport)
        help_menu.addAction(report_action)

        site_action = QtWidgets.QAction('JsonStudio Site', self)
        site_action.triggered.connect(self.openSite)
        help_menu.addAction(site_action)

    def applyStyleFile(self, path, display_name=None):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                qss = f.read()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Style Error', f'Failed to load stylesheet:\n{e}')
            return
        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet(qss)
        self._style_path = path
        self._current_builtin_style = None
        # Update checks
        for act in self._style_actions:
            try:
                act.setChecked(act.text() == (display_name or os.path.basename(path)))
            except Exception:
                pass
        self._update_style_status_label(display_name or os.path.basename(path))
        self._save_style_selection({'kind': 'qss', 'path': path})

    def loadStyle(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Select Stylesheet',
            os.path.expanduser('~'),
            'Qt Stylesheets (*.qss);;All Files (*)'
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                qss = f.read()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Style Error', f'Failed to load stylesheet:\n{e}')
            return
        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet(qss)
        self._style_path = path
        self._current_builtin_style = None
        for act in self._style_actions:
            try:
                act.setChecked(False)
            except Exception:
                pass
        self._update_style_status_label(os.path.basename(path))
        self._save_style_selection({'kind': 'qss', 'path': path})

    def resetStyle(self):
        app = QtWidgets.QApplication.instance()
        if app:
            app.setStyleSheet('')
        self._style_path = None
        self._current_builtin_style = 'Default'
        for act in self._style_actions:
            try:
                act.setChecked(act.text() == 'Default')
            except Exception:
                pass
        self._update_style_status_label('Default')
        self._save_style_selection({'kind': 'default'})

    def showOptions(self):
        if self._options_dialog is None:
            try:
                self._options_dialog = OptionsDialog(self)
            except Exception:
                self._options_dialog = None
        if self._options_dialog is not None:
            try:
                self._options_dialog.show()
                self._options_dialog.raise_()
                self._options_dialog.activateWindow()
            except Exception:
                pass

    def newFile(self):
        """Start a new (empty) JSON document by clearing views and schema."""
        self.clearAll()

    def printCurrent(self):
        """Print Raw View contents; if empty, print current tree as JSON."""
        if QtPrintSupport is None:
            QtWidgets.QMessageBox.warning(self, 'Print Not Available', 'QtPrintSupport is not available in this environment.')
            return
        printer = QtPrintSupport.QPrinter()
        dialog = QtPrintSupport.QPrintDialog(printer, self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        text = self.ui_view_edit.toPlainText().strip()
        if not text:
            try:
                data = self.ui_tree_view.asDict(None)
                text = json.dumps(data, indent=4, sort_keys=True)
            except Exception:
                text = ''
        doc = QtGui.QTextDocument(text)
        try:
            doc.print_(printer)
        except Exception:
            QtWidgets.QMessageBox.critical(self, 'Print Error', 'Failed to print the document.')

    # Edit actions implementations
    def _text_edit(self):
        return getattr(self, 'ui_view_edit', None)

    def editUndo(self):
        w = self._text_edit()
        if w is not None:
            try:
                w.undo()
            except Exception:
                pass

    def editRedo(self):
        w = self._text_edit()
        if w is not None:
            try:
                w.redo()
            except Exception:
                pass

    def editCut(self):
        w = self._text_edit()
        if w is not None:
            try:
                w.cut()
            except Exception:
                pass

    def editCopy(self):
        w = self._text_edit()
        if w is not None:
            try:
                w.copy()
            except Exception:
                pass

    def editPaste(self):
        w = self._text_edit()
        if w is not None:
            try:
                w.paste()
            except Exception:
                pass

    def editFind(self):
        w = self._text_edit()
        if w is None:
            return
        dlg = FindDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        vals = dlg.values()

        whole = vals.get('whole_word', False)
        case = vals.get('match_case', False)
        use_regex = vals.get('use_regex', False)

        # Build flags for plain-text find
        flags = QtGui.QTextDocument.FindFlags()
        try:
            if case:
                flags |= QtGui.QTextDocument.FindCaseSensitively
            if whole:
                flags |= QtGui.QTextDocument.FindWholeWords
        except Exception:
            pass

        found = False
        if use_regex:
            pattern = vals.get('regex') or ''
            if not pattern:
                return
            # Attempt QRegExp first (widely supported), optionally wrap with word boundaries
            try:
                patt = pattern
                if whole:
                    if not patt.startswith(r"\b"):
                        patt = r"\b" + patt
                    if not patt.endswith(r"\b"):
                        patt = patt + r"\b"
                rx = QtCore.QRegExp(patt)
                rx.setCaseSensitivity(QtCore.Qt.CaseSensitive if case else QtCore.Qt.CaseInsensitive)
                # Some bindings accept flags with regex; try with and without
                try:
                    found = bool(w.find(rx, flags))
                except Exception:
                    found = bool(w.find(rx))
            except Exception:
                found = False
        else:
            text = vals.get('text') or ''
            if not text:
                return
            try:
                found = bool(w.find(text, flags))
            except Exception:
                try:
                    found = bool(w.find(text))
                except Exception:
                    found = False

        if not found:
            try:
                QtWidgets.QMessageBox.information(self, 'Find', 'No matches found.')
            except Exception:
                pass

    def editReplace(self):
        w = self._text_edit()
        if w is None:
            return
        find_text, ok = QtWidgets.QInputDialog.getText(self, 'Replace', 'Find:')
        if not ok:
            return
        replace_text, ok2 = QtWidgets.QInputDialog.getText(self, 'Replace', 'Replace with:')
        if not ok2:
            return
        try:
            content = w.toPlainText()
            content = content.replace(find_text, replace_text)
            w.setPlainText(content)
        except Exception:
            pass

    def toggleLineComment(self):
        w = self._text_edit()
        if w is None:
            return
        cursor = w.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        tc = QtGui.QTextCursor(w.document())
        tc.setPosition(start)
        # Iterate lines
        block = w.document().findBlock(start)
        last_block = w.document().findBlock(end)
        # Determine if we should comment or uncomment (if all lines start with //)
        all_commented = True
        scan_block = block
        while True:
            text = scan_block.text().lstrip()
            if not text.startswith('//'):
                all_commented = False
            if scan_block == last_block:
                break
            scan_block = scan_block.next()

        w.blockSignals(True)
        w.document().undoStack().beginMacro('Toggle Line Comment') if hasattr(w.document(), 'undoStack') else None
        b = block
        while True:
            line_text = b.text()
            leading_ws_len = len(line_text) - len(line_text.lstrip(' \t'))
            leading = line_text[:leading_ws_len]
            rest = line_text[leading_ws_len:]
            if all_commented:
                if rest.startswith('//'):
                    new_line = leading + rest[2:]
                else:
                    new_line = line_text
            else:
                new_line = leading + '//' + rest
            # replace the block text
            c = QtGui.QTextCursor(b)
            c.select(QtGui.QTextCursor.LineUnderCursor)
            c.removeSelectedText()
            c.insertText(new_line)
            if b == last_block:
                break
            b = b.next()
        if hasattr(w.document(), 'undoStack'):
            try:
                w.document().undoStack().endMacro()
            except Exception:
                pass
        w.blockSignals(False)

    def toggleBlockComment(self):
        w = self._text_edit()
        if w is None:
            return
        cursor = w.textCursor()
        if not cursor.hasSelection():
            return
        sel_start = cursor.selectionStart()
        sel_end = cursor.selectionEnd()
        doc = w.document()
        tc = QtGui.QTextCursor(doc)
        tc.setPosition(sel_start)
        tc.setPosition(sel_end, QtGui.QTextCursor.KeepAnchor)
        selected_text = tc.selectedText()
        # QTextCursor.selectedText replaces newlines with \u2029; convert back
        selected_text = selected_text.replace('\u2029', '\n')
        if selected_text.startswith('/*') and selected_text.endswith('*/'):
            new_text = selected_text[2:-2]
        else:
            new_text = '/*' + selected_text + '*/'
        tc.insertText(new_text)

    # View actions implementations
    def _setCopyButtonsVisible(self, visible):
        try:
            if hasattr(self, 'ui_out_btn') and self.ui_out_btn is not None:
                self.ui_out_btn.setVisible(visible)
        except Exception:
            pass
        try:
            if hasattr(self, 'ui_update_btn') and self.ui_update_btn is not None:
                self.ui_update_btn.setVisible(visible)
        except Exception:
            pass

    def hideJsonCodeEditor(self):
        try:
            if hasattr(self, 'ui_view_edit') and self.ui_view_edit is not None:
                self.ui_view_edit.hide()
        except Exception:
            pass
        # Ensure UI (tree) editor stays visible
        try:
            if hasattr(self, 'ui_tree_view') and self.ui_tree_view is not None:
                self.ui_tree_view.show()
        except Exception:
            pass
        # Hide copy buttons as requested
        self._setCopyButtonsVisible(False)

    def hideJsonUiEditor(self):
        try:
            if hasattr(self, 'ui_tree_view') and self.ui_tree_view is not None:
                self.ui_tree_view.hide()
        except Exception:
            pass
        # Ensure Code editor stays visible
        try:
            if hasattr(self, 'ui_view_edit') and self.ui_view_edit is not None:
                self.ui_view_edit.show()
        except Exception:
            pass
        # Hide copy buttons as requested
        self._setCopyButtonsVisible(False)

    def showJsonEditors(self):
        try:
            if hasattr(self, 'ui_view_edit') and self.ui_view_edit is not None:
                self.ui_view_edit.show()
        except Exception:
            pass
        try:
            if hasattr(self, 'ui_tree_view') and self.ui_tree_view is not None:
                self.ui_tree_view.show()
        except Exception:
            pass
        # Show buttons again when both editors are shown
        self._setCopyButtonsVisible(True)

    # Help menu handlers
    def showAbout(self):
        text = (
            'JsonStudio\n\n'
            'A Qt-based JSON viewer/editor.\n'
            f'Python: {sys.version.split("\\n")[0]}\n'
            f'Qt: {QtCore.qVersion()}\n'
        )
        try:
            QtWidgets.QMessageBox.information(self, 'About JsonStudio', text)
        except Exception:
            pass

    def showVersionNotes(self):
        notes = (
            'Version Notes\n\n'
            '- JSON Schema validation support (requires jsonschema).\n'
            '- Themes via .qss files and persistent selection.\n'
            '- Raw View with syntax highlighting.\n'
            '- Menus for File/Edit/View/Help.'
        )
        try:
            QtWidgets.QMessageBox.information(self, 'Version Notes', notes)
        except Exception:
            pass

    def createProblemReport(self):
        try:
            info = [
                'Problem Report (copy below)',
                '',
                f'App: JsonStudio',
                f'Python: {sys.version.split("\\n")[0]}',
                f'Qt: {QtCore.qVersion()}',
                f'OS: {platform.platform()}',
                f'Arch: {platform.machine()}',
                '',
                'Describe the issue here:'
            ]
            text = '\n'.join(info)
            # Copy to clipboard
            try:
                QtWidgets.QApplication.clipboard().setText(text)
            except Exception:
                pass
            # Show editable dialog for user to add details
            dlg = TextEditDialog(text=text, title='Create Problem Report')
            try:
                dlg.ui_textEdit.selectAll()
            except Exception:
                pass
            dlg.show()
        except Exception:
            QtWidgets.QMessageBox.information(self, 'Create Problem Report', 'Unable to assemble problem report.')

    def openSite(self):
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/oleitao'))
        except Exception:
            pass

    def _styles_in_ui(self):
        styles = {}
        ui_dir = os.path.join(MODULE_PATH, 'ui')
        try:
            for fname in os.listdir(ui_dir):
                if fname.lower().endswith('.qss'):
                    name = os.path.splitext(fname)[0].replace('_', ' ').title()
                    styles[name] = os.path.join(ui_dir, fname)
        except Exception:
            pass
        return styles

    def _update_style_status_label(self, name):
        if hasattr(self, 'ui_style_status_label'):
            try:
                self.ui_style_status_label.setText(f'Style: {name}')
            except Exception:
                pass

    # Persist/restore selected style
    def _save_style_selection(self, data):
        try:
            with open(STYLE_PREF_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_saved_style(self):
        try:
            with open(STYLE_PREF_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return

        kind = data.get('kind')
        if kind == 'default':
            # Ensure checks reflect default
            self.resetStyle()
            return
        if kind == 'qss':
            path = data.get('path')
            if not path:
                return
            if not os.path.isabs(path):
                # Support older relative paths (if any)
                path = os.path.join(MODULE_PATH, path)
            if not os.path.exists(path):
                return
            # Determine display name and check corresponding action if inside ui dir
            ui_dir = os.path.join(MODULE_PATH, 'ui')
            display_name = None
            try:
                if os.path.commonpath([os.path.abspath(path), os.path.abspath(ui_dir)]) == os.path.abspath(ui_dir):
                    display_name = os.path.splitext(os.path.basename(path))[0].replace('_', ' ').title()
            except Exception:
                pass
            self.applyStyleFile(path, display_name)


def show():
    global window
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DontUseNativeMenuBar, True)
    except Exception:
        pass
    app = QtWidgets.QApplication(sys.argv)
    # Set application icon (taskbar/dock)
    try:
        if os.path.exists(ICON_PATH):
            app.setWindowIcon(QtGui.QIcon(ICON_PATH))
    except Exception:
        pass
    window = MainWindow()
    try:
        if window.menuBar():
            window.menuBar().setVisible(True)
    except Exception:
        pass
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    show()
