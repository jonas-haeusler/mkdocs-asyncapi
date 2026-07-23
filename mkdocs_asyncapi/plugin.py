import logging
import posixpath
from pathlib import Path
from typing import Optional

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.utils import get_relative_url

from .assets import AssetProvider
from .parser import AsyncApiParser

log = logging.getLogger(f"mkdocs.plugins.{__name__}")

# The shadow DOM host establishes no stacking/containing context of its own, so internal
# z-indexed elements and position:fixed controls (e.g. the mobile sidebar toggle) would
# otherwise escape to compete with the surrounding page's header/nav. `contain:layout` fixes
# that, but only takes effect on a block box - the browser default for unknown elements is
# `display:inline`, on which containment is a no-op.
HOST_CONTAINMENT_STYLE = "<style>asyncapi-component{display:block;contain:layout}</style>"


class AsyncApiPlugin(BasePlugin):
    """MkDocs plugin for embedding AsyncAPI specs via the asyncapi-react web component."""

    config_scheme = (
        ("config", config_options.Type(dict, default={})),
        ("asset_source", config_options.Choice(["bundled", "cdn"], default="bundled")),
        # Keep this default in sync with the version pinned in package.json (the vendored bundle).
        ("version", config_options.Type(str, default="3.1.4")),
        ("css_import_path", config_options.Optional(config_options.Type(str))),
    )

    def __init__(self):
        self.files = None
        self.pages_with_component = set()

    def on_files(self, files, config, **kwargs):
        self.files = files
        self.pages_with_component = set()
        return files

    def on_page_markdown(self, markdown: str, page, **kwargs) -> str:
        """Parse <asyncapi-component> tags and replace them with the resolved web component."""
        page_file = page.file.src_uri
        global_config = self.config["config"]

        def replacer(match):
            opts = AsyncApiParser.parse(match.group(1), global_config)
            schema_url = self._resolve_src(opts.src, page)
            css_import_path = self._resolve_css(page, opts.css_import_path)
            self.pages_with_component.add(page_file)
            return AsyncApiParser.to_html(schema_url, opts, css_import_path)

        return AsyncApiParser.PATTERN.sub(replacer, markdown)

    def on_page_content(self, html, page, **kwargs):
        """Inject the web component script only on pages that use it."""
        page_file = page.file.src_uri
        if page_file not in self.pages_with_component:
            return html

        asset_source = self.config["asset_source"]
        script_src = AssetProvider.script_url(asset_source, self.config["version"])
        if asset_source == "bundled":
            script_src = get_relative_url(script_src, page.url)

        return f'{HOST_CONTAINMENT_STYLE}\n<script src="{script_src}" defer></script>\n{html}'

    def on_post_build(self, config, **kwargs):
        """Copy the vendored web component assets into the built site."""
        if self.pages_with_component and self.config["asset_source"] == "bundled":
            AssetProvider.copy_bundle(Path(config["site_dir"]))

    def _resolve_src(self, src: Optional[str], page) -> Optional[str]:
        """Resolve a component's src to a page-relative URL, passing remote URLs through."""
        if not src:
            return src
        if src.startswith("http://") or src.startswith("https://"):
            return src

        page_dir = posixpath.dirname(page.file.src_uri)
        target = posixpath.normpath(posixpath.join(page_dir, src))
        file = self.files.get_file_from_path(target)
        if file is None:
            log.warning(
                "mkdocs-asyncapi: Could not resolve local src '%s' referenced on page '%s'",
                src,
                page.file.src_uri,
            )
            return src
        return get_relative_url(file.url, page.url)

    def _resolve_css(self, page, inline_override: Optional[str]) -> str:
        """Resolve the stylesheet for a page. Precedence: inline > global config > bundled/cdn default."""
        asset_source = self.config["asset_source"]
        override = inline_override or self.config["css_import_path"]
        css = AssetProvider.css_url(asset_source, self.config["version"], override)
        if not override and asset_source == "bundled":
            css = get_relative_url(css, page.url)
        return css
