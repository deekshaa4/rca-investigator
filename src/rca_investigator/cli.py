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

    incidents = generate_dataset(args.n, seed=args.seed, hard=args.hard)
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


def cmd_investigate(args: argparse.Namespace) -> int:
    """Investigate one incident and print the report."""
    from pathlib import Path

    from .investigate import investigate, save_report, to_markdown
    from .simulate import load_incident

    meta, metrics, records = load_incident(args.path)
    client = None if args.no_llm else OllamaClient(model=args.model)
    start = time.perf_counter()
    try:
        report = investigate(meta["incident_id"], meta["question"], meta["metric"], metrics,
                             records, client)
    except LLMError as exc:
        print(f"Problem: {exc}")
        return 1
    print(to_markdown(report))
    print(f"(took {time.perf_counter() - start:.0f}s)")
    if args.save:
        out = Path(args.path) / "report.json"
        save_report(report, out)
        (Path(args.path) / "report.md").write_text(to_markdown(report))
        print(f"Saved {out} and report.md")
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    """Investigate every incident in a folder, save the reports and score them."""
    import json
    from pathlib import Path

    from .evaluate import score_report
    from .investigate import investigate, save_report, to_markdown
    from .simulate import load_incident

    folders = sorted(p for p in Path(args.path).iterdir() if (p / "incident.json").exists())
    client = None if args.no_llm else OllamaClient(model=args.model)
    rows = []
    for folder in folders:
        meta, metrics, records = load_incident(folder)
        start = time.perf_counter()
        try:
            report = investigate(meta["incident_id"], meta["question"], meta["metric"],
                                 metrics, records, client)
        except LLMError as exc:
            print(f"  {meta['incident_id']}: failed ({exc})")
            continue
        save_report(report, folder / "report.json")
        (folder / "report.md").write_text(to_markdown(report))
        truth = json.loads((folder / "truth.json").read_text())
        row = score_report(report, truth)
        row["seconds"] = round(time.perf_counter() - start)
        rows.append(row)
        print(f"  {row['incident']} {row['scenario']:<18} verdict {row['verdict']:<12} "
              f"top {row['top_category']:<14} {row['seconds']}s", flush=True)
    return _print_scores(rows, Path(args.path))


def _print_scores(rows: list[dict], folder) -> int:
    """Overall scores, then per scenario and per twist; also saved to scores.csv."""
    import pandas as pd

    from .evaluate import breakdown, summarise

    if not rows:
        print(f"No reports to score in {folder}")
        return 1
    pd.DataFrame(rows).to_csv(folder / "scores.csv", index=False)
    print(f"\nScores for {len(rows)} incidents")
    for name, value in summarise(rows).items():
        print(f"  {name:<40} {value:.0%}")
    for by in ("scenario", "twist"):
        if len({r[by] for r in rows}) > 1:
            print(f"\nBy {by}:")
            print(breakdown(rows, by).to_string())
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Score the reports already saved in a folder (no model needed)."""
    import json
    from pathlib import Path

    from .evaluate import score_report
    from .schema import RCAReport

    folder = Path(args.path)
    rows = []
    for sub in sorted(folder.iterdir()):
        if (sub / "report.json").exists() and (sub / "truth.json").exists():
            report = RCAReport.model_validate_json((sub / "report.json").read_text())
            rows.append(score_report(report, json.loads((sub / "truth.json").read_text())))
    return _print_scores(rows, folder)


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the web page where CuteBot investigates incidents live."""
    from pathlib import Path

    try:
        import uvicorn

        from .web import create_app
    except ImportError:
        print('The web page needs extra packages:  pip install -e ".[web]"')
        return 1
    if not Path(args.data).is_dir():
        print(f"No folder {args.data}. Make some incidents first:  rca simulate")
        return 1
    print(f"Open http://{args.host}:{args.port} in your browser (Ctrl+C to stop).")
    uvicorn.run(create_app(args.data, model=args.model), host=args.host, port=args.port,
                log_level="warning")
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
    simulate.add_argument("--hard", action="store_true",
                          help="add red herrings, competing changes, missing records, more noise")
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

    inv = sub.add_parser("investigate", help="investigate one incident and write the report")
    inv.add_argument("path")
    inv.add_argument("--model", default=DEFAULT_MODEL)
    inv.add_argument("--no-llm", action="store_true", help="engines only, no language model")
    inv.add_argument("--save", action="store_true", help="save report.json and report.md")
    inv.set_defaults(func=cmd_investigate)

    batch = sub.add_parser("batch", help="investigate and score every incident in a folder")
    batch.add_argument("path")
    batch.add_argument("--model", default=DEFAULT_MODEL)
    batch.add_argument("--no-llm", action="store_true")
    batch.set_defaults(func=cmd_batch)

    ev = sub.add_parser("evaluate", help="score saved reports against the known answers")
    ev.add_argument("path")
    ev.set_defaults(func=cmd_evaluate)

    serve = sub.add_parser("serve", help="open the web page with the investigator bot")
    serve.add_argument("--data", default="data/generated", help="folder of incidents")
    serve.add_argument("--model", default=DEFAULT_MODEL)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
