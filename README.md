<div align="center">
<h1 align="center">Json Editor</h1>

  <p align="center">
    A python script for editing `.json` file based on Qt framework
    <br />
    <a href="https://youtu.be/bTjKKb8CYIM">Demo</a>
  </p>
</div>

## About The Project

<br>

<div align="center">
<img src="https://i.imgur.com/7O7OGlr.jpg" alt="json-editor" width="70%"/>
</div>

`.json` files are heavily dependent in production environment and there are
many benefits of creating a standalone editor instead of editing the text file directly. 
Not everyone is fan of working with a text editor (like artists) and no one
can be confident to avoid syntax error in their edits.
Moreover, a standalone tool supports features like version control,
validation, schema and more.

The goal of this tool initially serves as my [model view programming practice in PyQt](https://github.com/leixingyu/model-view-tutorial),
but then I thought, why not iterate on it and make it user-friendly, portable and minimal? My goal now is to make this
modular and easily embeddable, so to create a standardized way for displaying and editing `.json` file across applications.

## Getting Started

### Prerequisites

- [Qt](https://github.com/mottosso/Qt.py): a module that supports different
python qt bindings

   or alternatively, change the code below to whatever qt binding you have on your machine.
   ```python
   from Qt import QtWidgets, QtCore, QtGui
   from Qt import _loadUi
   ```

### Launch

1. Unzip the **json-editor** package and rename is to something like `jsonViewer`

2. You can either run `main.py` directly or:
    ```python
    from jsonViewer import main
    main.show()
    ```

## Features

### Validation, sort and filtering

- Data validation is a built-in feature that comes with the model/view architecture
as type is preserved during `setData()` and `data()` methods. It then gets translated
into qt element: `str` as `QLineEdit`; `int` as `QSpinBox`; `float` as `QDoubleSpinBox`

- `list` and `dict` type data fully utilized the hierarchical support of `QAbstractItemModel`.

- Sorting and Filtering are enabled with the help of `QSortFilterProxyModel`.

![](https://i.imgur.com/ngslOnZ.gif)  


### Serialization

Serialization and de-serialization in the `QJsonModel` enables functionalities like copy/paste (left) 
and drag/drop (right).

| Copy and Paste | Drag and Drop |
|-----|----|
| ![copy/paste](https://i.imgur.com/UVlgHmQ.gif) | ![drag/drop](https://i.imgur.com/1uHIhOA.gif) |

### Raw View

The tool also has a built-in text editor with syntax highlighting known as the **raw view**.

As shown, the data between the **tree view** and the **raw view** are interchangeable.

![](https://i.imgur.com/o8IH5q9.gif)


## JSON Schema

- Use `Load JSON…` to select a file. The selected JSON is shown in the Raw View and is also set as the active schema.
- Click `Validate` to validate the JSON Schema itself (checked against the appropriate meta‑schema). If you edit the Raw View, the edited content is what gets validated.
- Click `Clear` to reset both panels (tree and Raw View) and clear the loaded schema.
- Requires the `jsonschema` package: `pip install jsonschema`.

## Custom Stylesheet

- The top menu `Style -> Themes` lists styles discovered from `.qss` files in `ui/` (e.g., `ui/dark.qss`, `ui/light.qss`). Add your own `.qss` files there to extend the list.
- Use `Style -> Load .qss…` to apply any stylesheet file manually.
- Use `Style -> Reset` to revert to the default Qt look.
 - Style selection persists: the last selected theme or `.qss` file is saved and re-applied on next launch.

## Roadmap

- [x] Json text view with syntax highlight
- [x] Json schema support
- [x] File drop
- [x] Custom stylesheet
- [ ] Scripting interface for modular support
- [ ] Web deployment (maybe?)

### Reference

[Model View Programming](https://github.com/leixingyu/model-view-tutorial)

[QJsonModel](https://github.com/dridk/QJsonModel)
