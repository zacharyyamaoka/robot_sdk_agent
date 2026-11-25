"""python -m scorer collect [--directory live|main] [--out inputs.json]   gather inputs from public data
   python -m scorer score <inputs.json>                                   print the scorecard (no network)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .collect import collect
from .score import score


def main(argv: list[str]) -> int:
    if argv[:1] == ["collect"]:
        directory = argv[argv.index("--directory") + 1] if "--directory" in argv else "live"
        inputs = collect(directory)
        text = json.dumps(inputs, indent=1, sort_keys=True) + "\n"
        if "--out" in argv:
            Path(argv[argv.index("--out") + 1]).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    if argv[:1] == ["score"] and len(argv) == 2:
        print(json.dumps(score(json.loads(Path(argv[1]).read_text(encoding="utf-8"))), indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
