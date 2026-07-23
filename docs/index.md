# AsyncAPI for MkDocs

[MkDocs](https://www.mkdocs.org/) plugin for embedding [AsyncAPI](https://www.asyncapi.com/) specs,
rendered via the official [asyncapi-react web component](https://github.com/asyncapi/asyncapi-react).

## Installation

1. Install the plugin via `pip`:
  ```shell
  pip install mkdocs-asyncapi
  ```
2. Add the plugin to your `mkdocs.yml`:
```yaml
plugins:
  - search
  - asyncapi
```

## Configuration

### asset_source

Controls where the web component JS/CSS are loaded from. Possible values:

- `bundled` (default): assets vendored into the plugin package, copied into the built site. Works
  fully offline.
- `cdn`: loads from [unpkg.com](https://unpkg.com), pinned to [version](#version).

```yaml
plugins:
  - search
  - asyncapi:
      asset_source: cdn
```

### version

The `asyncapi-react`/`web-component` version to use for `cdn` URLs (default: `3.1.4`). Has no effect
when `asset_source` is `bundled` — the vendored assets are always used in that case.

### config

Sets the default [AsyncAPI React configuration](https://github.com/asyncapi/asyncapi-react/blob/master/docs/configuration/config-modification.md)
applied to every component on the site. All official config properties are supported (`show`,
`expand`, `sidebar`, `parserOptions`, `schemaID`, the operation `*Label` options, `extensions`, ...).

```yaml
plugins:
  - search
  - asyncapi:
      config:
        show:
          sidebar: true
```

Individual components can override the global config (see [Options](#options) below).

### css_import_path

Overrides the stylesheet loaded by every component, instead of the vendored (or CDN) default. Use
this when you want a custom-themed stylesheet — e.g. matching your site's brand colors — built from
a copy of [`default.css`](https://github.com/asyncapi/asyncapi-react/blob/master/library/styles/default.css).
The value is used verbatim (unlike `src`, it is **not** resolved relative to the current page), so
point it at a fully-qualified URL or a site-root-absolute path:

```yaml
plugins:
  - search
  - asyncapi:
      css_import_path: https://example.com/asyncapi-custom.css
```

A per-component `cssImportPath="..."` attribute overrides this for a single component (see
[Options](#options)).

## Usage

Use the `<asyncapi-component>` tag and reference a spec via `src`:

--8<-- "usage.md"

`src` can be either:

- a **local** file included in the docs build, resolved relative to the current page (MkDocs copies
  it into the site like any other static file)
- a **remote** `http(s)://` URL, fetched by the browser at view time:

--8<-- "remote-usage.md"

### Options

- `src` (required) — path or URL to the AsyncAPI spec.
- `config='{...}'` — per-component config, deep-merged over the global [config](#config) (the
  component's own value wins on conflicts).
- `schemaFetchOptions='{...}'` — optional `RequestInit` JSON passed to the fetch call for `src`.
- `cssImportPath="..."` — per-component stylesheet override, wins over the global
  [css_import_path](#css_import_path).

## Examples

### Inline config override

--8<-- "config-usage.md"

See the [sample page](sample/index.md) for these rendered live.
