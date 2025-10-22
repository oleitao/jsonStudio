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
UI_PATH = os.path.join(MODULE_PATH, 'ui', 'jsonStudio.ui')
TEST_DICT = {}
STYLE_PREF_PATH = os.path.join(MODULE_PATH, 'ui', 'settings.json')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        _loadUi(UI_PATH, self)

        self.ui_tree_view = QJsonView()
        self.ui_tree_view.setStyleSheet('QWidget{font: 10pt "Bahnschrift";}')
        self.ui_grid_layout.addWidget(self.ui_tree_view, 1, 0)

        # schema/state
        self._schema = None
        self._schema_path = None
        # style state
        self._style_path = None
        self._current_builtin_style = 'Default'
        self._style_actions = []

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

        self.ui_filter_edit.textChanged.connect(self._proxyModel.setFilterRegExp)
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

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Load Error', f'Failed to load JSON file:\n{e}')
            return

        # Always present the selected JSON in the Raw View (data)
        try:
            self.ui_view_edit.setReadOnly(False)
        except Exception:
            pass
        text = json.dumps(data, indent=4, sort_keys=True)
        self.ui_view_edit.setPlainText(text)

        # Also set it as the active schema for validation
        self._schema = data
        if hasattr(self, 'ui_schema_status_label'):
            self.ui_schema_status_label.setText(f'Schema: {os.path.basename(path)}')

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
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    show()
