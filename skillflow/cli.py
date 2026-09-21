"""Command line interface for skillflow."""

import argparse
import json
import os
import sys

from . import __version__
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
        env = json.loads(args.env) if args.env else None
    except ValueError:
        print("error: --env must be a JSON object", file=sys.stderr)
        return 2
    try:
        with _flow(args) as flow:
            flow.add_node(args.name, args.cmd, timeout_s=args.timeout,
                          env=env, cwd=args.cwd)
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


def cmd_remove_node(args) -> int:
    try:
        with _flow(args) as flow:
            removed = flow.remove_node(args.name, args.force)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"removed node {args.name!r} "
          f"({removed['edges']} edges, {removed['results']} results)")
    return 0


def cmd_remove_edge(args) -> int:
    try:
        with _flow(args) as flow:
            flow.remove_edge(args.from_node, args.to_node)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"removed edge {args.from_node!r} -> {args.to_node!r}")
    return 0


def cmd_runs(args) -> int:
    try:
        with _flow(args) as flow:
            print(json.dumps({"runs": flow.runs()}, indent=2, default=str))
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_diff(args) -> int:
    try:
        with _flow(args) as flow:
            print(json.dumps(flow.diff(args.a, args.b), indent=2,
                             default=str))
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
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
            if args.dry_run:
                print(json.dumps({"plan": flow.plan()}, indent=2))
                return 0
            if args.retry:
                run_id = flow.retry(args.jobs)
            else:
                run_id = flow.run(args.jobs, args.from_node)
            result = flow.status(run_id)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["run"]["status"] == "ok" else 1


def cmd_demo(args) -> int:
    import tempfile
    tmp = tempfile.mkdtemp(prefix="skillflow-demo-")
    db = os.path.join(tmp, "demo.db")
    print(f"demo graph in {tmp}")
    try:
        with Flow(db) as flow:
            flow.add_node("fetch", "echo page > page.txt", cwd=tmp)
            flow.add_node("check", "echo checks > checks.txt", cwd=tmp)
            flow.add_node("report", "cat page.txt checks.txt", cwd=tmp)
            flow.add_edge("fetch", "report")
            flow.add_edge("check", "report")
            run_id = flow.run(jobs=2)
            result = flow.status(run_id)
    except FlowError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    run = result["run"]
    print(f"run {run['id']}: {run['status']}")
    for node in result["nodes"]:
        print(f"  {node['name']}: {node['status']}")
    print(f"inspect with: skillflow --db {db} status --json")
    return 0 if run["status"] == "ok" else 1


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
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create the database")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("add-node", help="add a node")
    p.add_argument("name")
    p.add_argument("--cmd", default="", help="shell command to run for this node")
    p.add_argument("--timeout", type=float, default=None,
                   help="kill the command after this many seconds")
    p.add_argument("--env", default=None,
                   help="extra environment as a JSON object")
    p.add_argument("--cwd", default=None,
                   help="working directory for this node's command")
    p.set_defaults(func=cmd_add_node)

    p = sub.add_parser("add-edge", help="add a dependency edge (from -> to)")
    p.add_argument("from_node")
    p.add_argument("to_node")
    p.set_defaults(func=cmd_add_edge)

    p = sub.add_parser("show", help="print the DAG as JSON")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("remove-node", help="delete a node and its edges")
    p.add_argument("name")
    p.add_argument("--force", action="store_true",
                   help="also delete recorded results")
    p.set_defaults(func=cmd_remove_node)

    p = sub.add_parser("remove-edge", help="delete one edge")
    p.add_argument("from_node")
    p.add_argument("to_node")
    p.set_defaults(func=cmd_remove_edge)

    p = sub.add_parser("runs", help="list recorded runs")
    p.set_defaults(func=cmd_runs)

    p = sub.add_parser("diff", help="compare two runs by id")
    p.add_argument("a", type=int)
    p.add_argument("b", type=int)
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("run", help="execute the DAG in topological order")
    p.add_argument("--dry-run", action="store_true",
                   help="print execution levels without running")
    p.add_argument("--jobs", type=int, default=1,
                   help="run nodes in one level concurrently (default 1)")
    p.add_argument("--from", dest="from_node", default=None,
                   help="run this node and everything downstream only")
    p.add_argument("--retry", action="store_true",
                   help="re-run from the latest run's first failure")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("demo", help="run a self-contained demo graph")
    p.set_defaults(func=cmd_demo)

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
