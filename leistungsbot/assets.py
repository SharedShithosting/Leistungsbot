# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""The gifs that ship inside the package.

Both call sites used to do this by hand, and both were broken:

    try:
        gif = importlib.resources.as_file(
            importlib.resources.files("resources") / "sneaky.gif",
        ),
    except BaseException:
        gif = Path(__file__).parent / "resources" / "sneaky.gif"

`resources` is a directory inside `leistungsbot`, not a top level module, so
`files("resources")` raised `ModuleNotFoundError` every single time and the
fallback was the only branch that ever ran. Which was lucky, because the
`try` branch has a trailing comma: it builds a one element *tuple* holding an
unentered context manager, and hands that to `InputFile`.

The fallback then resolved `resources/` next to whichever file the code
happened to live in - fine while every handler sat in `Bot.py`, wrong the
moment they moved into `leistungsbot/handlers/`.
"""

from __future__ import annotations

import importlib.resources
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def gif(name: str):
    """! Yields a real filesystem path for the packaged gif `name`

    A context manager because that is what `importlib.resources` promises:
    when the package is installed as a zip the file only exists on disk for
    the duration of the block.
    """
    source = importlib.resources.files("leistungsbot") / "resources" / name
    with importlib.resources.as_file(source) as path:
        yield Path(path)
