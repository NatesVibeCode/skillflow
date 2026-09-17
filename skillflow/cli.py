"""Command line interface for skillflow."""

import argparse
import json
import os
import sys

from .dag import Flow, FlowError

DEFAULT_DB = os.environ.get("SKILLFLOW_DB", "skillflow.db")


def _flow(args) -> Flow:
    return Flow(args.db)


def cmd_init(args) -> int:
    try:
        with _flow(args):
            pass
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"initialized {args.db}")
    return 0


def cmd_add_node(args) -> int:
    try:
        with _flow(args) as flow:
            flow.add_node(args.name, args.cmd)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"added node {args.name!r}")
    return 0


def cmd_add_edge(args) -> int:
    try:
        with _flow(args) as flow:
            flow.add_edge(args.from_node, args.to_node)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"added edge {args.from_node!r} -> {args.to_node!r}")
    return 0


def cmd_show(args) -> int:
    try:
        with _flow(args) as flow:
            print(json.dumps({"nodes": flow.nodes(), "edges": flow.edges()}, indent=2))
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_run(args) -> int:
    try:
        with _flow(args) as flow:
            run_id = flow.run()
            result = flow.status(run_id)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["run"]["status"] == "ok" else 1


def cmd_status(args) -> int:
    try:
        with _flow(args) as flow:
            result = flow.status(args.run)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        run = result["run"]
        print(f"run {run['id']}: {run['status']}")
        for node in result["nodes"]:
            print(f"  {node['name']}: {node['status']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillflow", description="A minimal SQLite-backed DAG runner."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the SQLite file")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create the database")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add-node", help="add a node")
    p.add_argument("name")
    p.add_argument("--cmd", default="", help="shell command to run for this node")
    p.set_defaults(func=cmd_add_node)

    p = sub.add_parser("add-edge", help="add a dependency edge (from -> to)")
    p.add_argument("from_node")
    p.add_argument("to_node")
    p.set_defaults(func=cmd_add_edge)

    p = sub.add_parser("show", help="print the DAG as JSON")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("run", help="execute the DAG in topological order")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("status", help="show the latest (or given) run")
    p.add_argument("--run", type=int, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
