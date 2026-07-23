# mkdocs-asyncapi

MkDocs plugin for embedding [AsyncAPI](https://www.asyncapi.com/) specs via the official
[asyncapi-react](https://github.com/asyncapi/asyncapi-react) web component.

## Quick Start

1. Install the `mkdocs-asyncapi` plugin via `pip`:
  ```shell
  pip install mkdocs-asyncapi
  ```
2. Add the plugin to your `mkdocs.yml`:
  ```yaml
  plugins:
    - search
    - asyncapi
  ```
3. Start embedding specs in your markdown:
  ```markdown
  <asyncapi-component src="path/to/spec.yml"/>
  ```

## Documentation

For detailed instructions, configuration options and a demo, please read the
**[documentation](https://jonas-haeusler.github.io/mkdocs-asyncapi/)**.

## Development

### Local setup

Run `./local-preview` in your terminal to build and run a MkDocs server with the plugin installed,
serving on <http://127.0.0.1:8000/>.

The vendored web component assets under `mkdocs_asyncapi/assets/` are refreshed via
`./scripts/vendor-assets.sh` (requires Node.js/npm) when bumping the pinned version in `package.json`.

## Releasing

Manually trigger the `release` workflow via GitHub Actions, which will auto-bump the plugin version
and perform the release process. PyPI publishing is set up via
[trusted publishing](https://docs.pypi.org/trusted-publishers/).

## License

mkdocs-asyncapi is licensed under the [MIT License](LICENSE).
