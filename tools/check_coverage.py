#!/usr/bin/env python3
# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Per file coverage gate.

`coverage report --fail-under` is a single number for the whole project, so
one well tested module can hide a module with no tests at all - which is
exactly how `BotScheduler` shipped a job pointing at a method that did not
exist while the total sat at a respectable 70-something percent.

This asks the same question of every file instead.

Usage:

    coverage run -m pytest
    coverage json -o reports/coverage/coverage.json
    python tools/check_coverage.py reports/coverage/coverage.json

Files listed in EXEMPT are allowed to be below the bar for the reason given,
but not to get worse: each carries the number it was at when it was added.
When one reaches MINIMUM the check fails and tells you to delete its entry,
so the list shrinks rather than being forgotten - the same bargain as the
`xfail(strict=True)` markers on the open bugs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MINIMUM = 75.0

EXEMPT: dict[str, tuple[float, str]] = {
    "leistungsbot/google_place.py": (
        36.0,
        "talks to the live google places api; google_place_test skips "
        "without a key, so ci never executes most of it",
    ),
    "leistungsbot/leistungs_config.py": (
        53.8,
        "reads the config into a module level singleton at import time; "
        "exercising set_args would mutate it for every other test",
    ),
}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    report = json.loads(Path(argv[1]).read_text())
    files = report["files"]

    failures: list[str] = []
    graduated: list[str] = []

    for name in sorted(files):
        # rounded to what `coverage report` prints, so a file shown as 54%
        # is not failed for being 53.96% against a floor of 54
        percent = round(files[name]["summary"]["percent_covered"], 1)
        floor, reason = EXEMPT.get(name, (MINIMUM, ""))

        if name in EXEMPT:
            if percent >= MINIMUM:
                graduated.append(
                    f"  {name} is at {percent:.0f}% and no longer needs its "
                    f"exemption - delete it from tools/check_coverage.py",
                )
            elif percent < floor:
                failures.append(
                    f"  {name} dropped to {percent:.0f}%, its exemption "
                    f"allows no less than {floor:.0f}%",
                )
        elif percent < MINIMUM:
            failures.append(
                f"  {name} is at {percent:.0f}%, needs {MINIMUM:.0f}%",
            )

    total = report["totals"]["percent_covered"]
    print(f"per file coverage gate: {MINIMUM:.0f}%, total is {total:.0f}%")

    if failures:
        print("\nbelow the bar:")
        print("\n".join(failures))
    if graduated:
        print("\nready to graduate:")
        print("\n".join(graduated))
    if not failures and not graduated:
        print("every file clears it")

    return 1 if (failures or graduated) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
