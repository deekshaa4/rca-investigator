# RCA Investigator

**An evidence-first AI investigator for root cause analysis.**

Most AI assistants tell you *what* went wrong. RCA Investigator works like an investigator: it finds **what changed**, works out **why it happened**, shows **the evidence** behind every finding, says honestly whether that evidence is **enough to be sure**, and recommends **how to prevent it** from happening again.

> Status: early development (Day 1 of a 2-week build). See the [roadmap](docs/ROADMAP.md).

## What it does

Given numerical data (metrics over time) and text records (logs, tickets, deploy and config change notes), it:

1. **Detects what changed**: when the metric shifted, by how much, and in which segment (service, region, ...).
2. **Investigates why**: links the change to events in the text records and ranks the contributing factors.
3. **Cites evidence**: every claim points to a numbered piece of evidence (`E1`, `E2`, ...). Claims without evidence are rejected.
4. **Judges sufficiency**: returns a verdict of `sufficient`, `partial` or `insufficient`, with reasons and the data that would settle open questions.
5. **Recommends actions**: corrective and preventive actions linked to each contributing factor.

## Design principles

- **Statistics do the maths, the language model does the reasoning.** Numbers are analysed with proper statistical methods, never guessed.
- **No evidence, no claim.** The report format enforces that every cited evidence ID exists.
- **"I don't know yet" is a valid answer.** Insufficient evidence is reported, not hidden.
- **Free and local.** Runs on a laptop with an open model through [Ollama](https://ollama.com). No API keys, no costs, and your data never leaves your machine.

## How it works

```
 metrics.csv ──► Numerical engine ──┐
                 (change points,      │
                  segment drill-down) ├─► Evidence pack ─► LLM investigator ─► Sufficiency check ─► RCA report
 records.jsonl ─► Text engine ───────┘   (numbered IDs)
                 (search, timeline)
```

The report format is defined in [`src/rca_investigator/schema.py`](src/rca_investigator/schema.py) and exported as a JSON Schema in [`schemas/rca_report.schema.json`](schemas/rca_report.schema.json). An example report is in [`examples/example_report.json`](examples/example_report.json).

## Quick start

Requirements: Python 3.10+ and [Ollama](https://ollama.com) (free).

```bash
git clone https://github.com/deekshaa4/rca-investigator.git
cd rca-investigator
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

ollama pull qwen2.5:3b     # small open model, about 2 GB
rca check                  # confirms the model is reachable
pytest                     # runs the tests
```

## Project structure

```
src/rca_investigator/
  schema.py     the RCA report format (with evidence-citation checks)
  llm.py        client for a local model served by Ollama
  cli.py        command-line interface (`rca ...`)
schemas/        JSON Schema of the report
examples/       example report
tests/          tests
docs/           roadmap
```

## License

MIT. See [LICENSE](LICENSE).
