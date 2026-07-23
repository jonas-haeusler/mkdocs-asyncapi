"""Tests for the AsyncAPI asset provider module."""

from unittest.mock import patch

from mkdocs_asyncapi.assets import AssetProvider


class TestPaths:
    """Tests for the script_path/css_path methods."""

    def test_script_path(self):
        """Test the site-relative script path."""
        assert AssetProvider.script_path() == "assets/mkdocs_asyncapi/asyncapi-web-component.js"

    def test_css_path(self):
        """Test the site-relative stylesheet path."""
        assert AssetProvider.css_path() == "assets/mkdocs_asyncapi/default.min.css"


class TestScriptUrl:
    """Tests for the script_url method."""

    def test_bundled_returns_site_relative_path(self):
        """Test that 'bundled' returns the vendored site-relative path."""
        assert AssetProvider.script_url("bundled", "3.1.4") == AssetProvider.script_path()

    def test_cdn_returns_unpkg_url(self):
        """Test that 'cdn' returns the pinned unpkg URL."""
        url = AssetProvider.script_url("cdn", "3.1.4")
        assert (
            url == "https://unpkg.com/@asyncapi/web-component@3.1.4/lib/asyncapi-web-component.js"
        )

    def test_cdn_uses_configured_version(self):
        """Test that the cdn URL reflects the configured version."""
        assert "9.9.9" in AssetProvider.script_url("cdn", "9.9.9")


class TestCssUrl:
    """Tests for the css_url method."""

    def test_bundled_returns_site_relative_path(self):
        """Test that 'bundled' returns the vendored site-relative path."""
        assert AssetProvider.css_url("bundled", "3.1.4") == AssetProvider.css_path()

    def test_cdn_returns_unpkg_url(self):
        """Test that 'cdn' returns the pinned unpkg URL."""
        url = AssetProvider.css_url("cdn", "3.1.4")
        assert url == "https://unpkg.com/@asyncapi/react-component@3.1.4/styles/default.min.css"

    def test_override_wins_regardless_of_source(self):
        """Test that an explicit override always wins."""
        assert AssetProvider.css_url("bundled", "3.1.4", override="/custom.css") == "/custom.css"
        assert AssetProvider.css_url("cdn", "3.1.4", override="/custom.css") == "/custom.css"


class TestCopyBundle:
    """Tests for the copy_bundle method."""

    def test_copies_vendored_files_into_site(self, tmp_path):
        """Test that both vendored files are copied into the built site."""
        site_dir = tmp_path / "site"
        site_dir.mkdir()

        AssetProvider.copy_bundle(site_dir)

        dest_dir = site_dir / "assets" / "mkdocs_asyncapi"
        assert (dest_dir / "asyncapi-web-component.js").stat().st_size > 0
        assert (dest_dir / "default.min.css").stat().st_size > 0

    @patch("mkdocs_asyncapi.assets.resources.files")
    def test_missing_vendored_asset_does_not_raise(self, mock_files, tmp_path):
        """Test that a missing vendored asset is logged, not raised."""
        empty_package_dir = tmp_path / "empty-package"
        empty_package_dir.mkdir()
        mock_files.return_value = empty_package_dir

        site_dir = tmp_path / "site"
        site_dir.mkdir()

        AssetProvider.copy_bundle(site_dir)

        dest_dir = site_dir / "assets" / "mkdocs_asyncapi"
        assert not (dest_dir / "asyncapi-web-component.js").exists()
        assert not (dest_dir / "default.min.css").exists()
