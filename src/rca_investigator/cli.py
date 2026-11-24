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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
