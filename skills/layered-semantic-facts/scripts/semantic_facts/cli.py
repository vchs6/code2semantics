"""Command-line entrypoint for scanning Python source and querying stored facts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .repository.contract import ContractCodec
from .repository.store import Repository
from .source_scanner import build_fact_batch
from .query_engine import execute_query
from .constructor_plan import plan_constructor_request
from .constructor import execute_constructor_request


def _assets() -> Path:
    return Path(__file__).resolve().parents[2] / "assets"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="semantic-facts")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan-source", aliases=["scan-python"], help="extract syntax inventory from Python and Rust files")
    scan.add_argument("--root", required=True, type=Path, help="source project root")
    scan.add_argument("--db", required=True, type=Path, help="SQLite fact repository")
    scan.add_argument("--output", type=Path, help="optional path to write the validated FactBatch")

    query = commands.add_parser("query", help="execute a caller-supplied public Query JSON")
    query.add_argument("--db", required=True, type=Path)
    query.add_argument("--query-file", required=True, type=Path)

    plan = commands.add_parser("plan", help="map a public ConstructRequest to fixed information needs")
    plan.add_argument("--request-file", required=True, type=Path)

    construct = commands.add_parser("construct", help="execute the supported deterministic constructor")
    construct.add_argument("--request-file", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "plan":
        request_document = json.loads(args.request_file.read_text(encoding="utf-8"))
        result = plan_constructor_request(request_document, _assets())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.command == "construct":
        request_document = json.loads(args.request_file.read_text(encoding="utf-8"))
        result = execute_constructor_request(request_document, _assets())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command in {"scan-source", "scan-python"}:
        codec = ContractCodec(_assets())
        batch = build_fact_batch(args.root, codec)
        digest = hashlib.sha256(
            json.dumps(batch, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        repository = Repository(args.db, _assets())
        try:
            receipt = repository.write(batch, "scan-" + digest)
        finally:
            repository.close()
        print(json.dumps({
            "status": "stored",
            "source_root": str(args.root.resolve()),
            "fact_count": len(batch["facts"]),
            "submission_key": receipt.submission_key,
            "digest": receipt.digest,
            "fact_batch_output": str(args.output) if args.output else None,
        }, ensure_ascii=False))
        return 0

    query_document = json.loads(args.query_file.read_text(encoding="utf-8"))
    repository = Repository(args.db, _assets())
    try:
        result = execute_query(query_document, repository, _assets())
    finally:
        repository.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
