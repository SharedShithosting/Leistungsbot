# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The gifs that ship inside the package.

These used to be resolved relative to the file the code happened to live in,
which broke the moment the handlers moved into `leistungsbot/handlers/`. The
handlers swallow the resulting `FileNotFoundError` into the dev chat, so it
is worth asserting on the lookup directly rather than only through a
workflow.
"""

from __future__ import annotations

import pytest

from leistungsbot import assets

SHIPPED = ["sneaky.gif", "responisibility.gif"]


@pytest.mark.parametrize("name", SHIPPED)
def test_the_gif_is_there(name):
    with assets.gif(name) as path:
        assert path.is_file()
        assert path.stat().st_size > 0


@pytest.mark.parametrize("name", SHIPPED)
def test_the_gif_is_a_real_gif(name):
    with assets.gif(name) as path:
        assert path.read_bytes()[:3] == b"GIF"


def test_a_missing_gif_does_not_silently_pass():
    with pytest.raises(FileNotFoundError), assets.gif("nope.gif") as path:
        path.read_bytes()


def test_every_gif_the_handlers_ask_for_is_shipped():
    """The handlers name their gifs as string literals; keep them honest."""
    import ast
    import pathlib

    # anchored on this file, not the working directory
    package = pathlib.Path(__file__).resolve().parent.parent / "leistungsbot"

    asked = set()
    for source in package.rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "gif"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                asked.add(node.args[0].value)

    assert asked, "no gif() call found - has the helper been renamed?"
    for name in asked:
        with assets.gif(name) as path:
            assert path.is_file(), f"{name} is used but not shipped"
