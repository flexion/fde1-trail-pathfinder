"""The skill's capability: one dense search over the skills wiki.

    python run.py "<query>" [k]

Prints {"query", "k", "result"} as JSON on stdout; `result` is exactly what search_chunks
returns to the tool loop. WIKI_DIR and EMBED_CACHE are read from the environment as in
suggest.py.

Each search prints `capability_call search_chunks` on stderr. This process is on the far
side of a process boundary, so no counter or trace in the caller sees the search run; the
caller counts these lines instead.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # the challenge dir

from suggest import MAX_K, search_chunks  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) < 2 or not argv[1].strip():
        print('usage: python run.py "<query>" [k]', file=sys.stderr)
        return 2
    query = argv[1]
    try:
        k = max(1, min(int(argv[2]), MAX_K)) if len(argv) > 2 else 4
    except ValueError:
        print(f"k must be an integer, not {argv[2]!r}", file=sys.stderr)
        return 2
    print("capability_call search_chunks", file=sys.stderr, flush=True)
    print(json.dumps({"query": query, "k": k, "result": search_chunks(query, k)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
