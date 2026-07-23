import logging
import shutil
from importlib import resources
from pathlib import Path
from typing import Optional

log = logging.getLogger(f"mkdocs.plugins.{__name__}")


class AssetProvider:
    """Provides the AsyncAPI web component JS bundle and stylesheet."""

    ASSETS_DIR = "assets/mkdocs_asyncapi"
    BUNDLE = "asyncapi-web-component.js"
    CSS = "default.min.css"

    UNPKG_JS = "https://unpkg.com/@asyncapi/web-component@{version}/lib/asyncapi-web-component.js"
    UNPKG_CSS = "https://unpkg.com/@asyncapi/react-component@{version}/styles/default.min.css"

    @classmethod
    def script_path(cls) -> str:
        """Site-relative path to the vendored web component JS."""
        return f"{cls.ASSETS_DIR}/{cls.BUNDLE}"

    @classmethod
    def css_path(cls) -> str:
        """Site-relative path to the vendored stylesheet."""
        return f"{cls.ASSETS_DIR}/{cls.CSS}"

    @classmethod
    def script_url(cls, asset_source: str, version: str) -> str:
        """Site-relative path (bundled) or unpkg URL (cdn) for the web component JS."""
        if asset_source == "cdn":
            return cls.UNPKG_JS.format(version=version)
        return cls.script_path()

    @classmethod
    def css_url(cls, asset_source: str, version: str, override: Optional[str] = None) -> str:
        """Site-relative path (bundled), unpkg URL (cdn), or a user-provided override."""
        if override:
            return override
        if asset_source == "cdn":
            return cls.UNPKG_CSS.format(version=version)
        return cls.css_path()

    @classmethod
    def copy_bundle(cls, site_dir: Path) -> None:
        """Copy the vendored web component JS + CSS into the built site."""
        dest_dir = site_dir / cls.ASSETS_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        for filename in (cls.BUNDLE, cls.CSS):
            src = resources.files("mkdocs_asyncapi").joinpath(f"assets/{filename}")
            if not src.is_file():
                log.error(
                    "mkdocs-asyncapi: Vendored asset missing: %s. "
                    "Reinstall mkdocs-asyncapi or run scripts/vendor-assets.sh.",
                    filename,
                )
                continue
            with resources.as_file(src) as src_path:
                shutil.copy2(src_path, dest_dir / filename)
