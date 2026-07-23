"""Tests for the AsyncAPI parser module."""

from mkdocs_asyncapi.parser import AsyncApiParser, ComponentOptions


class TestComponentOptions:
    """Tests for the ComponentOptions dataclass."""

    def test_default_values(self):
        """Test that ComponentOptions has correct default values."""
        opts = ComponentOptions(src="spec.yml")
        assert opts.src == "spec.yml"
        assert opts.config == {}
        assert opts.css_import_path is None
        assert opts.schema_fetch_options is None


class TestPattern:
    """Tests for the regex pattern matching."""

    def test_self_closing_tag(self):
        """Test matching a self-closing <asyncapi-component/> tag."""
        markdown = '<asyncapi-component src="spec.yml"/>'
        match = AsyncApiParser.PATTERN.search(markdown)
        assert match is not None
        assert 'src="spec.yml"' in match.group(1)

    def test_paired_tag(self):
        """Test matching a paired <asyncapi-component></asyncapi-component> tag."""
        markdown = '<asyncapi-component src="spec.yml"></asyncapi-component>'
        match = AsyncApiParser.PATTERN.search(markdown)
        assert match is not None
        assert 'src="spec.yml"' in match.group(1)

    def test_paired_tag_with_whitespace_between(self):
        """Test matching a paired tag with whitespace between open/close."""
        markdown = '<asyncapi-component src="spec.yml">\n</asyncapi-component>'
        match = AsyncApiParser.PATTERN.search(markdown)
        assert match is not None

    def test_no_match_for_other_tags(self):
        """Test that unrelated tags don't match."""
        markdown = '<div class="foo"></div>'
        assert AsyncApiParser.PATTERN.search(markdown) is None

    def test_multiple_tags(self):
        """Test finding multiple tags."""
        markdown = '<asyncapi-component src="a.yml"/>\n\n<asyncapi-component src="b.yml"/>'
        matches = list(AsyncApiParser.PATTERN.finditer(markdown))
        assert len(matches) == 2

    def test_matches_gt_inside_attribute_value(self):
        """Test that a '>' inside a quoted attribute value doesn't terminate the tag early."""
        markdown = '<asyncapi-component src="x" config=\'{"publishLabel":"A > B"}\'/>'
        match = AsyncApiParser.PATTERN.search(markdown)
        assert match is not None
        assert "publishLabel" in match.group(1)


class TestParseAttrs:
    """Tests for the parse_attrs method."""

    def test_double_quoted_attr(self):
        """Test parsing a double-quoted attribute."""
        assert AsyncApiParser.parse_attrs(' src="spec.yml"') == {"src": "spec.yml"}

    def test_single_quoted_attr(self):
        """Test parsing a single-quoted attribute."""
        assert AsyncApiParser.parse_attrs(" src='spec.yml'") == {"src": "spec.yml"}

    def test_multiple_attrs(self):
        """Test parsing multiple attributes."""
        attrs = AsyncApiParser.parse_attrs(' src="spec.yml" config=\'{"show":{"info":false}}\'')
        assert attrs["src"] == "spec.yml"
        assert attrs["config"] == '{"show":{"info":false}}'

    def test_no_attrs(self):
        """Test parsing an empty attribute string."""
        assert AsyncApiParser.parse_attrs("") == {}


class TestParse:
    """Tests for the parse method."""

    def test_parses_src(self):
        """Test that src is extracted."""
        opts = AsyncApiParser.parse(' src="spec.yml"', {})
        assert opts.src == "spec.yml"

    def test_no_inline_config_uses_global(self):
        """Test that global config is used when no inline config is given."""
        opts = AsyncApiParser.parse(' src="spec.yml"', {"show": {"sidebar": True}})
        assert opts.config == {"show": {"sidebar": True}}

    def test_inline_config_merges_over_global(self):
        """Test that inline config is deep-merged over global config."""
        opts = AsyncApiParser.parse(
            ' src="spec.yml" config=\'{"show":{"info":false}}\'',
            {"show": {"sidebar": True}},
        )
        assert opts.config == {"show": {"sidebar": True, "info": False}}

    def test_inline_config_overrides_conflicting_key(self):
        """Test that inline config wins on a conflicting key."""
        opts = AsyncApiParser.parse(
            ' src="spec.yml" config=\'{"show":{"sidebar":false}}\'',
            {"show": {"sidebar": True}},
        )
        assert opts.config == {"show": {"sidebar": False}}

    def test_invalid_json_config_ignored(self):
        """Test that invalid JSON in config is ignored, falling back to global config."""
        opts = AsyncApiParser.parse(" src=\"spec.yml\" config='not json'", {"a": 1})
        assert opts.config == {"a": 1}

    def test_non_object_config_ignored(self):
        """Test that a config that is valid JSON but not an object is ignored (no crash)."""
        opts = AsyncApiParser.parse(" src=\"spec.yml\" config='[1,2,3]'", {"a": 1})
        assert opts.config == {"a": 1}

    def test_invalid_json_schema_fetch_options_dropped(self):
        """Test that invalid JSON in schemaFetchOptions is dropped rather than passed through."""
        opts = AsyncApiParser.parse(" src=\"spec.yml\" schemaFetchOptions='not json'", {})
        assert opts.schema_fetch_options is None

    def test_css_import_path_and_fetch_options(self):
        """Test that cssImportPath and schemaFetchOptions are extracted."""
        opts = AsyncApiParser.parse(
            ' src="spec.yml" cssImportPath="/custom.css" schemaFetchOptions=\'{"mode":"cors"}\'',
            {},
        )
        assert opts.css_import_path == "/custom.css"
        assert opts.schema_fetch_options == '{"mode":"cors"}'


class TestDeepMerge:
    """Tests for the _deep_merge method."""

    def test_override_wins_on_scalar(self):
        """Test that override wins on a plain scalar conflict."""
        assert AsyncApiParser._deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_dicts_merge(self):
        """Test that nested dicts are merged key-by-key."""
        result = AsyncApiParser._deep_merge({"show": {"a": 1, "b": 2}}, {"show": {"b": 3}})
        assert result == {"show": {"a": 1, "b": 3}}

    def test_base_untouched(self):
        """Test that the base dict is not mutated."""
        base = {"show": {"a": 1}}
        AsyncApiParser._deep_merge(base, {"show": {"a": 2}})
        assert base == {"show": {"a": 1}}


class TestToHtml:
    """Tests for the to_html method."""

    def test_basic_output(self):
        """Test basic output with no config."""
        opts = ComponentOptions(src="spec.yml")
        html = AsyncApiParser.to_html("spec.yml", opts, "default.min.css")
        assert html == (
            '<asyncapi-component schemaUrl="spec.yml" cssImportPath="default.min.css">'
            "</asyncapi-component>"
        )

    def test_includes_config_when_present(self):
        """Test that a non-empty config is emitted as an attribute."""
        opts = ComponentOptions(src="spec.yml", config={"show": {"info": False}})
        html = AsyncApiParser.to_html("spec.yml", opts, "default.min.css")
        assert "config=" in html
        assert "&quot;show&quot;" in html

    def test_omits_config_when_empty(self):
        """Test that an empty config is omitted."""
        opts = ComponentOptions(src="spec.yml", config={})
        html = AsyncApiParser.to_html("spec.yml", opts, "default.min.css")
        assert "config=" not in html

    def test_includes_schema_fetch_options(self):
        """Test that schemaFetchOptions is emitted when present."""
        opts = ComponentOptions(src="spec.yml", schema_fetch_options='{"mode":"cors"}')
        html = AsyncApiParser.to_html("spec.yml", opts, "default.min.css")
        assert "schemaFetchOptions=" in html

    def test_escapes_schema_url(self):
        """Test that the schema URL is HTML-escaped to prevent injection."""
        opts = ComponentOptions(src="x")
        html = AsyncApiParser.to_html('spec"><script>alert(1)</script>', opts, "default.min.css")
        assert "<script>" not in html
        assert "&quot;" in html

    def test_missing_schema_url_emits_empty(self):
        """Test that a missing src warns and emits an empty schemaUrl instead of failing."""
        opts = ComponentOptions(src=None)
        html = AsyncApiParser.to_html(None, opts, "default.min.css")
        assert 'schemaUrl=""' in html
