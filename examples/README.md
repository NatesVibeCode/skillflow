# Examples

Runnable scripts; each builds a throwaway graph, runs it, and cleans up.
Requires `skillflow` on PATH (`pip install skill-dag`).

- `01-hello.sh` — the smallest useful graph: chain, run, inspect.
- `02-parallel.sh` — independent branches with `--jobs`, plus `--dry-run`.
- `03-retry.sh` — a failing run, a fix outside the graph, then `--retry`.

Every script is executed by `tests/test_examples.py`, so they cannot rot.
