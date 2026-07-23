import json
import logging
import re
from dataclasses import dataclass, field
from html import escape

log = logging.getLogger(f"mkdocs.plugins.{__name__}")


@dataclass
class ComponentOptions:
    """Options parsed from an <asyncapi-component> tag."""

    src: str | None
    config: dict = field(default_factory=dict)
    css_import_path: str | None = None
    schema_fetch_options: str | None = None


class AsyncApiParser:
    """Parser for <asyncapi-component> tags in markdown."""

    # The attribute run allows a quoted value to contain '>' (e.g. inside a config JSON string);
    # only a '>' outside quotes terminates the tag.
    PATTERN = re.compile(
        r"""<asyncapi-component((?:"[^"]*"|'[^']*'|[^>])*?)(?:/>|>\s*</asyncapi-component>)""",
        re.DOTALL,
    )
    ATTR_PATTERN = re.compile(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")

    @classmethod
    def parse_attrs(cls, attr_string: str) -> dict:
        """Extract name="value" / name='value' pairs from a tag's attribute string."""
        return {
            m.group(1): m.group(2) if m.group(2) is not None else m.group(3)
            for m in cls.ATTR_PATTERN.finditer(attr_string)
        }

    @classmethod
    def parse(cls, attr_string: str, global_config: dict) -> ComponentOptions:
        """Parse a tag's attributes, merging its inline config over the global config."""
        attrs = cls.parse_attrs(attr_string)

        inline_config = cls._parse_json_attr("config", attrs.get("config"))
        if inline_config is not None and not isinstance(inline_config, dict):
            log.warning(
                "mkdocs-asyncapi: config attribute must be a JSON object, ignoring: %s",
                attrs.get("config"),
            )
            inline_config = None

        schema_fetch_options = attrs.get("schemaFetchOptions")
        # Keep the original string; we validate only to warn on malformed JSON.
        if (
            schema_fetch_options is not None
            and cls._parse_json_attr("schemaFetchOptions", schema_fetch_options) is None
        ):
            schema_fetch_options = None

        return ComponentOptions(
            src=attrs.get("src"),
            config=cls._deep_merge(global_config, inline_config or {}),
            css_import_path=attrs.get("cssImportPath"),
            schema_fetch_options=schema_fetch_options,
        )

    @staticmethod
    def _parse_json_attr(name: str, raw: str | None):
        """Parse a JSON attribute value; warn and return None if absent or not valid JSON."""
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("mkdocs-asyncapi: Invalid JSON in %s attribute: %s", name, raw)
            return None

    @classmethod
    def _deep_merge(cls, base: dict, override: dict) -> dict:
        """Recursively merge override into base; override wins on conflicting keys."""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def to_html(schema_url: str | None, opts: ComponentOptions, css_import_path: str) -> str:
        """Render the resolved options as an <asyncapi-component> web component tag."""
        if not schema_url:
            log.warning("mkdocs-asyncapi: <asyncapi-component> is missing a 'src' attribute")
            schema_url = ""

        attrs = f'schemaUrl="{escape(schema_url, quote=True)}"'
        attrs += f' cssImportPath="{escape(css_import_path, quote=True)}"'
        if opts.config:
            attrs += f' config="{escape(json.dumps(opts.config), quote=True)}"'
        if opts.schema_fetch_options:
            attrs += f' schemaFetchOptions="{escape(opts.schema_fetch_options, quote=True)}"'
        return f"<asyncapi-component {attrs}></asyncapi-component>"
