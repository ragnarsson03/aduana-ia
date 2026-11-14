from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


class IndexReferences(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.assets: set[str] = set()
        self.references: set[str] = set(re.findall(r"(?:https?:)?//[^\s\"'<>]+", html))
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name in ("src", "href", "poster"):
            value = values.get(name)
            if value:
                self.references.add(value)
                if tag in {"script", "link", "img", "source", "video"}:
                    self.assets.add(value)
        srcset = values.get("srcset", "")
        for candidate in srcset.split(","):
            if candidate.strip():
                value = candidate.strip().split()[0]
                self.references.add(value)
                self.assets.add(value)

    def external(self, base_url: str) -> list[str]:
        origin = urlsplit(base_url).netloc
        return sorted(
            ref for ref in self.references
            if urlsplit(urljoin(base_url, ref)).scheme in {"http", "https"}
            and urlsplit(urljoin(base_url, ref)).netloc != origin
        )

    def local_assets(self, base_url: str) -> list[str]:
        origin = urlsplit(base_url).netloc
        return sorted(
            urljoin(base_url, ref) for ref in self.assets
            if urlsplit(urljoin(base_url, ref)).netloc == origin
            and not ref.startswith("#")
        )


def assert_asset_type(url: str, content_type: str) -> None:
    suffix = urlsplit(url).path.rsplit(".", 1)[-1].lower()
    media_type = content_type.split(";", 1)[0].lower()
    expected = {
        "js": {"text/javascript", "application/javascript"},
        "css": {"text/css"}, "png": {"image/png"}, "svg": {"image/svg+xml"},
        "jpg": {"image/jpeg"}, "jpeg": {"image/jpeg"}, "webp": {"image/webp"},
        "gif": {"image/gif"}, "ico": {"image/x-icon", "image/vnd.microsoft.icon"},
        "woff": {"font/woff"}, "woff2": {"font/woff2"},
    }
    assert suffix in expected, f"Add a content-type assertion for asset extension: {suffix}"
    assert media_type in expected[suffix], f"Incorrect asset content-type: {media_type} ({suffix})"


def assert_no_cedula(content: bytes, location: str) -> None:
    # A boolean assertion avoids pytest printing either the body or sensitive bytes.
    leaked = any(value in content for value in (b"V-12345678", b"V12345678", b"12345678"))
    assert not leaked, f"Synthetic citizen identifier found in {location}; content redacted"
