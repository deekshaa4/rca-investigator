"""Command-line interface: `rca <command>`."""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .llm import DEFAULT_MODEL, LLMError, OllamaClient
from .schema import export_json_schema


def cmd_check(args: argparse.Namespace) -> int:
    """Check that the local model is installed and answering."""
    client = OllamaClient(model=args.model)
    try:
        if not client.has_model():
            print(f"Ollama is running, but the model '{args.model}' is not installed.")
            print(f"Install it with:  ollama pull {args.model}")
            return 1
        start = time.perf_counter()
        reply = client.chat_json(
            "Reply with a JSON object whose 'status' field is the word ready.",
            json_schema={
                "type": "object",
                "properties": {"status": {"type": "string"}},
                "required": ["status"],
            },
        )
        seconds = time.perf_counter() - start
    except LLMError as exc:
        print(f"Problem: {exc}")
        print("Is Ollama installed and running? See https://ollama.com")
        return 1
    print(f"Model '{args.model}' replied {reply} in {seconds:.1f}s. All good.")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Write the report JSON Schema to a file."""
    export_json_schema(args.output)
    print(f"Wrote {args.output}")
    return 0


def cmd_simulate(args: argparse.Namespace) -> int:
    """Generate synthetic incidents with known causes."""
    from collections import Counter

    from .simulate import generate_dataset, save_incident

    incidents = generate_dataset(args.n, seed=args.seed)
    for incident in incidents:
        save_incident(incident, args.out)
    counts = Counter(i.truth["scenario"] for i in incidents)
    print(f"Wrote {len(incidents)} incidents to {args.out}/")
    for scenario, count in counts.items():
        print(f"  {scenario:<18} {count}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run the numerical engine on one incident, or score it on a folder of incidents."""
    import json
    from pathlib import Path

    import pandas as pd

    from .analyze import analyze_change
    from .simulate import load_incident

    path = Path(args.path)
    if (path / "incident.json").exists():
        meta, metrics, _ = load_incident(path)
        result = analyze_change(metrics, meta["metric"])
        print(meta["question"])
        for finding in result.findings:
            print(f"  - {finding['summary']}")
        return 0

    folders = sorted(p for p in path.iterdir() if (p / "incident.json").exists())
    if not folders:
        print(f"No incidents found in {path}")
        return 1
    rows = []
    for folder in folders:
        meta, metrics, _ = load_incident(folder)
        truth = json.loads((folder / "truth.json").read_text())
        result = analyze_change(metrics, meta["metric"])
        gap = (
            abs(pd.Timestamp(result.change_start) - pd.Timestamp(truth["change_start"]))
            if result.detected else None
        )
        rows.append({
            "incident": meta["incident_id"],
            "scenario": truth["scenario"],
            "segment_ok": result.segment == truth["segment"],
            "minutes_off": None if gap is None else int(gap.total_seconds() // 60),
        })
    table = pd.DataFrame(rows)
    print(table.to_string(index=False))
    seg = table["segment_ok"].mean()
    on_time = (table["minutes_off"].fillna(1e9) <= 15).mean()
    print(f"\nRight segment: {seg:.0%}   Change time within 15 min: {on_time:.0%}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Find the records that explain the change (one incident, or score a folder)."""
    import json
    from pathlib import Path

    from .analyze import analyze_change
    from .records import rank_records
    from .simulate import load_incident

    path = Path(args.path)
    if (path / "incident.json").exists():
        meta, metrics, records = load_incident(path)
        hits = rank_records(records, analyze_change(metrics, meta["metric"]), top_k=args.top)
        print(meta["question"])
        for i, hit in enumerate(hits, start=1):
            rec = hit.record
            print(f"  {i}. [{hit.score:.2f}] {rec['id']} {rec['source']}: {rec['text']}")
            print(f"       {'; '.join(hit.reasons)}")
        return 0

    folders = sorted(p for p in path.iterdir() if (p / "incident.json").exists())
    found, total = 0, 0
    for folder in folders:
        meta, metrics, records = load_incident(folder)
        truth = json.loads((folder / "truth.json").read_text())
        if not truth["cause_record_ids"]:
            continue
        hits = rank_records(records, analyze_change(metrics, meta["metric"]), top_k=args.top)
        ids = [h.record["id"] for h in hits]
        rank = next((ids.index(c) + 1 for c in truth["cause_record_ids"] if c in ids), None)
        total += 1
        found += rank is not None
        print(f"  {meta['incident_id']}  {truth['scenario']:<18} cause rank: {rank or 'missed'}")
    print(f"\nCause record in top {args.top}: {found}/{total}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rca", description="Evidence-first root cause analysis")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check the local model is ready")
    check.add_argument("--model", default=DEFAULT_MODEL)
    check.set_defaults(func=cmd_check)

    schema = sub.add_parser("schema", help="export the report JSON Schema")
    schema.add_argument("--output", default="schemas/rca_report.schema.json")
    schema.set_defaults(func=cmd_schema)

    simulate = sub.add_parser("simulate", help="generate synthetic incidents with known causes")
    simulate.add_argument("--n", type=int, default=20, help="number of incidents")
    simulate.add_argument("--seed", type=int, default=42)
    simulate.add_argument("--out", default="data/generated")
    simulate.set_defaults(func=cmd_simulate)

    analyze = sub.add_parser(
        "analyze", help="find what changed (one incident folder, or score a folder of incidents)"
    )
    analyze.add_argument("path")
    analyze.set_defaults(func=cmd_analyze)

    search = sub.add_parser("search", help="find records that explain the change")
    search.add_argument("path")
    search.add_argument("--top", type=int, default=5)
    search.set_defaults(func=cmd_search)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
