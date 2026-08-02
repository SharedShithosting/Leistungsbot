# These version placeholders will be replaced later during substitution.
#
# poetry-dynamic-versioning rewrites the two assignments below at build time
# from the git tag, so keep them on one line and in this exact shape --
# the substitution is a regex anchored on `^__version__` / `^__version_tuple__`.
from __future__ import annotations

__version__ = "0.0.0"
__version_tuple__ = (0, 0, 0)


def _from_metadata() -> tuple[str, tuple[int | str, ...]] | None:
    """! Version of the installed distribution, if there is one

    Covers the plain checkout case: substitution only runs on a build, so a
    `poetry install`ed working copy would otherwise report 0.0.0 forever.
    Poetry writes the dynamic version into the distribution metadata, so it
    is the same string substitution would have produced.
    """
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version

    try:
        found = version("leistungsbot")
    except PackageNotFoundError:
        return None
    if not found or found == "0.0.0":
        return None
    return found, _as_tuple(found)


def _as_tuple(text: str) -> tuple[int | str, ...]:
    """! Splits a PEP 440 string into the parts of __version_tuple__

    The leading numeric release segments become ints and whatever follows
    stays as one trailing string, which is the shape
    poetry-dynamic-versioning writes when it substitutes this file.
    """
    public, plus, local = text.partition("+")
    parts: list[int | str] = []
    rest = public
    while rest:
        segment, sep, remainder = rest.partition(".")
        if not segment.isdigit():
            break
        parts.append(int(segment))
        rest = remainder if sep else ""
    trailing = rest + plus + local
    if trailing:
        parts.append(trailing)
    return tuple(parts)


if __version__ == "0.0.0":
    _fallback = _from_metadata()
    if _fallback is not None:
        __version__, __version_tuple__ = _fallback
    del _fallback
