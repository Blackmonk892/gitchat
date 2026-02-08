from pathlib import Path
import urllib.parse


def to_uri(path: Path) -> str:

    return Path(path).as_uri()


def from_uri(uri: str) -> str:

    parsed = urllib.parse.urlparse(uri)
    path = urllib.parse.unquote(parsed.path)

    if path.startswith('/') and ':' in path:
        path = path[1:]
    return path
