#!/usr/bin/env bash
# 01-hello: the smallest useful graph. Chain three steps, run, inspect.
set -euo pipefail
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
export SKILLFLOW_DB="$WORK/hello.db"

skillflow init >/dev/null
skillflow add-node fetch --cmd "echo page > page.txt"
skillflow add-node parse --cmd "wc -c < page.txt > size.txt"
skillflow add-node report --cmd "cat size.txt"
skillflow add-edge fetch parse
skillflow add-edge parse report
skillflow run >/dev/null
skillflow status
