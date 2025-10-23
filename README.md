<div align="center">
  <h1 align="center">JSON Editor</h1>
  <p align="center">
    A lightweight Qt-based tool for viewing and editing JSON
    <br/>
  </p>
</div>

## Overview

<div align="center">
  <img src="https://i.imgur.com/7O7OGlr.jpg" alt="json-editor" width="70%"/>
  <br/>
</div>

JSON is ubiquitous in production pipelines, but editing raw text can be error‑prone—especially for non‑developers—and a missed comma can break everything. A dedicated editor reduces syntax mistakes and unlocks features that plain text lacks, such as validation, schema awareness, theming, and easier distribution.

This project began as a small [PyQt model/view exercise](https://github.com/leixingyu/model-view-tutorial) and grew into a minimal, portable JSON editor. The long‑term aim is a modular, embeddable component that provides a consistent JSON editing experience across different applications.

## Getting Started

### Prerequisites

- [Qt.py](https://github.com/mottosso/Qt.py), which abstracts over PySide/PyQt bindings.
  If you prefer a specific binding, replace the imports accordingly:

  ```python
  from Qt import QtWidgets, QtCore, QtGui
  from Qt import _loadUi
  ```

### Launch

1. Unzip the package (e.g., to `jsonViewer`).
2. Run `main.py` directly, or import and launch:

   ```python
   from jsonViewer import main
   main.show()
   ```

## Features

### Type‑aware editing, sorting, and filtering

- The model/view design preserves Python types in `setData()`/`data()`, which map to suitable Qt editors: `str` → `QLineEdit`, `int` → `QSpinBox`, `float` → `QDoubleSpinBox`.
- `dict` and `list` structures are represented hierarchically via `QAbstractItemModel`.
- Sorting and filtering are provided by `QSortFilterProxyModel`.

![](https://i.imgur.com/ngslOnZ.gif)

### Serialization

`QJsonModel` supports (de)serialization, enabling copy/paste on the left and drag/drop on the right.

| Copy and Paste | Drag and Drop |
| --- | --- |
| ![copy/paste](https://i.imgur.com/UVlgHmQ.gif) | ![drag/drop](https://i.imgur.com/1uHIhOA.gif) |

### Raw View

Alongside the tree, there’s a text editor with JSON syntax highlighting—the Raw View. Data flows both ways: edit in the tree or in the Raw View and keep them in sync.

![](https://i.imgur.com/o8IH5q9.gif)

## JSON Schema

- Use `File → Load JSON…` to choose a file. The content appears in the Raw View and becomes the active schema.
- Click `Validate` to check that the JSON Schema itself is valid (against the appropriate meta‑schema). If you’ve edited the Raw View, that content is validated.
- Click `Clear` to reset the tree and Raw View, and clear the loaded schema.
- Requires `jsonschema`: `pip install jsonschema`.

## Styles and Theming

- `Style → Themes` lists themes discovered from `.qss` files in `ui/` (e.g., `ui/dark.qss`, `ui/light.qss`). Add your own `.qss` files to extend the list.
- Use `Style → Load .qss…` to apply any stylesheet file manually.
- Use `Style → Reset` to return to the default Qt appearance.
- The chosen style is saved and restored on next launch.

## Roadmap

- [] JSON text view with syntax highlighting
- [x] JSON Schema support
- [] File drag & drop
- [x] Custom stylesheets
- [ ] Scripting interface for modularity
- [ ] Possible web deployment

* [ ] Formatting and linting: configurable prettifier, duplicate key detection, trailing commas; support JSON, JSONC, and JSON5.
* [ ] Schema-based validation: real-time validation via JSON Schema (recent drafts), hover to see errors, quick-fixes, automatic $ref resolution (local/remote).
* [ ] Synchronized multiple views: Text ↔ Tree (collapsible) ↔ Table (for arrays of objects) ↔ Side-by-side diff.
* [ ] Search & transform: JSONPath support and jq integration with live preview.
* [ ] Smart diff/merge: semantic “by key” comparison (not line-based), 3-way merge, moved-node detection.
* [ ] Large file handling: incremental/streaming parsing, partial loading, and virtual scrolling.
* [ ] Autocomplete: schema-based suggestions, snippets, and automatic generation of valid objects.
* [ ] Per-node history: undo/redo scoped to the modified branch.

=== Quality of Life ===

* [ ] Secret/PII detection: highlighting, redaction, and warnings for keys like apiKey/password.
* [ ] Templates & boilerplates: create from schema; catalog (OpenAPI, package.json, tsconfig…).
* [ ] Refactors: rename key globally, extract subtree into $ref, sort keys with rules.
* [ ] Cross-validation: custom rules (e.g., “if type=A then fields must contain X”).
* [ ] Comments: support JSONC/JSON5 and preserve comments on format.
* [ ] Quick actions: duplicate node, move ↑↓, wrap in object/array, convert types (string⇄number⇄boolean).

=== Visualization & Debugging ===

* [ ] Statistics: counts, sizes, type distribution, most frequent keys.
* [ ] Quick charts: bar/pie from arrays of objects (e.g., status by count).
* [ ] Heatmap: highlight nodes recently changed or with errors.
* [ ] Reference explorer: navigate $id/$ref, “peek definition”.

=== Integrations with APIs & Dev Tools ===

* [ ] Mock server: local server that responds according to a JSON/Schema (configurable latency and error rates).
* [ ] Contract tests: compare payloads against schemas (OpenAPI/AsyncAPI/Avro) and generate reports.
* [ ] Built-in CLI: run jq, ajv, yq (for YAML⇄JSON), with “copy as command”.
* [ ] Integrated Git: per-node blame, inline diff, pre-commit hooks (lint/validate).
* [ ] Connectors: S3/GCS, remote URLs, workspaces with auto refresh.

=== Advanced Experiments ===

* [ ] Schema inference: generate JSON Schema from multiple examples (tolerant to variations).
* [ ] Transformation assistant: “explain/generate a jq to transform A→B” (possible AI use).
* [ ] Security validation: size limits, banned keys, PII detector.
* [ ] Localization: key maps for i18n (detect untranslated keys across files).

=== UX/UI ===

* [ ] Global command (⌘K): actions, keys, paths, schemas.
* [ ] Breadcrumbs: show $.orders[12].items[3].price with click-to-jump.
* [ ] Pins: pin favorite nodes at the top.
* [ ] Quick inspection: hover shows samples and metadata (size in bytes, depth).
* [ ] Themes & accessibility: high contrast, configurable mono fonts, RTL-ready.

=== Suggested Architecture ===

* [ ] Desktop (cross-platform): Electron or Tauri + Monaco Editor; validation with ajv; workers for parsing; Rust (Serde/Simdjson) via Tauri for huge files.
* [ ] Web: React + Monaco, ajv + json-source-map (map position→node), Web Workers to keep the UI non-blocking.
* [ ] Optional backend: Node/Rust for heavy comparisons, schema storage, and audits.

=== Sample Roadmap ===

1. MVP (2–3 weeks): Monaco editor, formatting, tree view, AJV validation, open/save, basic JSONPath.
2. Pro version: per-node diff/merge, integrated jq, schema-based autocomplete, templates, Git.
3. Team version: mock server, contract tests, remote connectors, security policies, real-time collaboration (CRDTs).

=== Extras to Shine ===

* [ ] “Explain this error”: translate validation messages into natural language and suggest fixes.
* [ ] Fake data generator: from the schema (faker/json-schema-faker) for testing.
* [ ] Quick “/” commands: /sort keys, /flatten, /dedupe, /to csv.
* [ ] Exports: CSV (with column selection), YAML, NDJSON, Parquet (via wasm/arrow).


### References

- [Model View Programming](https://github.com/leixingyu/model-view-tutorial)
- [QJsonModel](https://github.com/dridk/QJsonModel)
