"""Tests for the AsyncAPI plugin module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mkdocs_asyncapi.plugin import AsyncApiPlugin


@pytest.fixture
def plugin():
    """Create a fresh plugin instance with default config."""
    p = AsyncApiPlugin()
    p.config = {
        "config": {},
        "asset_source": "bundled",
        "version": "3.1.4",
        "css_import_path": None,
    }
    return p


def make_page(src_uri, url):
    """Create a fake MkDocs page with the given src_uri/url."""
    page = MagicMock()
    page.file.src_uri = src_uri
    page.url = url
    return page


class TestPluginInit:
    """Tests for plugin initialization."""

    def test_init_defaults(self, plugin):
        """Test that plugin initializes with correct defaults."""
        assert plugin.files is None
        assert plugin.pages_with_component == set()


class TestOnFiles:
    """Tests for the on_files method."""

    def test_stores_files_and_resets_state(self, plugin):
        """Test that on_files stores the Files collection and resets per-build state."""
        plugin.pages_with_component = {"stale.md"}
        files = MagicMock()

        result = plugin.on_files(files, {})

        assert plugin.files is files
        assert plugin.pages_with_component == set()
        assert result is files


class TestOnPageMarkdown:
    """Tests for the on_page_markdown method."""

    def test_replaces_remote_src(self, plugin):
        """Test that a remote src is passed through unchanged."""
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = 'Before\n\n<asyncapi-component src="https://example.com/spec.yml"/>\n\nAfter'
        result = plugin.on_page_markdown(markdown, page)

        assert 'schemaUrl="https://example.com/spec.yml"' in result
        assert "Before" in result and "After" in result

    def test_resolves_local_src_via_files(self, plugin):
        """Test that a local src is resolved via the Files collection."""
        resolved_file = MagicMock()
        resolved_file.url = "spec.yml"
        plugin.files = MagicMock()
        plugin.files.get_file_from_path.return_value = resolved_file

        page = make_page("index.md", "index.html")
        markdown = '<asyncapi-component src="spec.yml"/>'

        with patch("mkdocs_asyncapi.plugin.get_relative_url", return_value="spec.yml") as mock_rel:
            result = plugin.on_page_markdown(markdown, page)

        plugin.files.get_file_from_path.assert_called_once_with("spec.yml")
        mock_rel.assert_any_call("spec.yml", "index.html")
        assert 'schemaUrl="spec.yml"' in result

    def test_local_src_resolved_relative_to_page_directory(self, plugin):
        """Test that a relative src is resolved relative to the page's own directory."""
        resolved_file = MagicMock()
        resolved_file.url = "sub/spec.yml"
        plugin.files = MagicMock()
        plugin.files.get_file_from_path.return_value = resolved_file

        page = make_page("sub/index.md", "sub/index.html")
        markdown = '<asyncapi-component src="spec.yml"/>'

        plugin.on_page_markdown(markdown, page)

        plugin.files.get_file_from_path.assert_called_once_with("sub/spec.yml")

    def test_unresolvable_local_src_falls_back_to_literal(self, plugin):
        """Test that an unresolvable local src falls back to the literal value."""
        plugin.files = MagicMock()
        plugin.files.get_file_from_path.return_value = None

        page = make_page("index.md", "index.html")
        markdown = '<asyncapi-component src="missing.yml"/>'

        result = plugin.on_page_markdown(markdown, page)

        assert 'schemaUrl="missing.yml"' in result

    def test_tracks_pages_with_component(self, plugin):
        """Test that a page using the component is tracked."""
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        plugin.on_page_markdown('<asyncapi-component src="https://x/y.yml"/>', page)

        assert "index.md" in plugin.pages_with_component

    def test_preserves_content_without_component(self, plugin):
        """Test that pages without the tag are left untouched and untracked."""
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")
        markdown = "# Title\n\nSome text."

        result = plugin.on_page_markdown(markdown, page)

        assert result == markdown
        assert "index.md" not in plugin.pages_with_component

    def test_merges_global_and_inline_config(self, plugin):
        """Test that global plugin config and inline config are deep-merged."""
        plugin.config["config"] = {"show": {"sidebar": True}}
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = '<asyncapi-component src="https://x/y.yml" config=\'{"show":{"info":false}}\'/>'
        result = plugin.on_page_markdown(markdown, page)

        assert "&quot;sidebar&quot;: true" in result
        assert "&quot;info&quot;: false" in result

    def test_config_value_containing_gt_is_replaced(self, plugin):
        """Test that a '>' inside inline config JSON doesn't prevent tag replacement."""
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = '<asyncapi-component src="https://x/y.yml" config=\'{"publishLabel":"A > B"}\'/>'
        result = plugin.on_page_markdown(markdown, page)

        assert "schemaUrl=" in result
        assert "index.md" in plugin.pages_with_component

    def test_inline_css_import_path_overrides_global(self, plugin):
        """Test that a per-tag cssImportPath attribute wins over the global config."""
        plugin.config["css_import_path"] = "/global.css"
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = '<asyncapi-component src="https://x/y.yml" cssImportPath="/inline.css"/>'
        result = plugin.on_page_markdown(markdown, page)

        assert 'cssImportPath="/inline.css"' in result

    def test_global_css_import_path_used_without_inline_override(self, plugin):
        """Test that the global css_import_path is used when no inline override is given."""
        plugin.config["css_import_path"] = "/global.css"
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = '<asyncapi-component src="https://x/y.yml"/>'
        result = plugin.on_page_markdown(markdown, page)

        assert 'cssImportPath="/global.css"' in result

    def test_cdn_css_import_path_used_when_cdn_source(self, plugin):
        """Test that the cdn stylesheet URL is used as cssImportPath when asset_source is 'cdn'."""
        plugin.config["asset_source"] = "cdn"
        plugin.files = MagicMock()
        page = make_page("index.md", "index.html")

        markdown = '<asyncapi-component src="https://x/y.yml"/>'
        result = plugin.on_page_markdown(markdown, page)

        assert (
            'cssImportPath="https://unpkg.com/@asyncapi/react-component@3.1.4'
            '/styles/default.min.css"' in result
        )


class TestOnPageContent:
    """Tests for the on_page_content method."""

    def test_injects_script_for_page_with_component(self, plugin):
        """Test that a script tag is injected for pages using the component."""
        plugin.pages_with_component = {"index.md"}
        page = make_page("index.md", "index.html")

        result = plugin.on_page_content("<h1>Title</h1>", page)

        assert "<script" in result
        assert "asyncapi-web-component.js" in result
        assert "<h1>Title</h1>" in result

    def test_injects_containment_style_for_page_with_component(self, plugin):
        """Test that the stacking-containment style is injected alongside the script."""
        plugin.pages_with_component = {"index.md"}
        page = make_page("index.md", "index.html")

        result = plugin.on_page_content("<h1>Title</h1>", page)

        assert "asyncapi-component{display:block;contain:layout}" in result

    def test_no_script_for_page_without_component(self, plugin):
        """Test that no script is injected for pages that don't use the component."""
        plugin.pages_with_component = set()
        page = make_page("other.md", "other.html")

        html = "<h1>Title</h1>"
        result = plugin.on_page_content(html, page)

        assert result == html

    def test_injects_cdn_url_when_configured(self, plugin):
        """Test that the CDN URL is injected when asset_source is 'cdn'."""
        plugin.config["asset_source"] = "cdn"
        plugin.pages_with_component = {"index.md"}
        page = make_page("index.md", "index.html")

        result = plugin.on_page_content("<h1>Title</h1>", page)

        assert "https://unpkg.com/@asyncapi/web-component@3.1.4" in result


class TestOnPostBuild:
    """Tests for the on_post_build method."""

    @patch("mkdocs_asyncapi.plugin.AssetProvider.copy_bundle")
    def test_copies_bundle_when_used_and_bundled(self, mock_copy, plugin):
        """Test that the bundle is copied when a page used the component and asset_source is bundled."""
        plugin.pages_with_component = {"index.md"}

        plugin.on_post_build({"site_dir": "/site"})

        mock_copy.assert_called_once_with(Path("/site"))

    @patch("mkdocs_asyncapi.plugin.AssetProvider.copy_bundle")
    def test_skips_copy_when_no_pages_use_component(self, mock_copy, plugin):
        """Test that the copy is skipped when no page uses the component."""
        plugin.pages_with_component = set()

        plugin.on_post_build({"site_dir": "/site"})

        mock_copy.assert_not_called()

    @patch("mkdocs_asyncapi.plugin.AssetProvider.copy_bundle")
    def test_skips_copy_when_cdn(self, mock_copy, plugin):
        """Test that the copy is skipped when asset_source is 'cdn'."""
        plugin.config["asset_source"] = "cdn"
        plugin.pages_with_component = {"index.md"}

        plugin.on_post_build({"site_dir": "/site"})

        mock_copy.assert_not_called()
