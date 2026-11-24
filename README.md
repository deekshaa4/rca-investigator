# RCA Investigator

**An evidence-first AI investigator for root cause analysis.**

Most AI assistants tell you *what* went wrong. RCA Investigator works like an investigator: it finds **what changed**, works out **why it happened**, shows **the evidence** behind every finding, says honestly whether that evidence is **enough to be sure**, and recommends **how to prevent it** from happening again.

> Status: early development (Day 5 of a 2-week build). See the [roadmap](docs/ROADMAP.md).

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
rca simulate --n 20        # generates 20 incidents with known causes in data/generated/
rca analyze data/generated # finds what changed in each incident and scores it
rca search data/generated  # finds the records that explain each change and scores it
rca investigate data/generated/INC-001 --save   # full investigation report with the local model
pytest                     # runs the tests
```

## Test incidents

To measure whether the investigator finds the *right* cause, it needs incidents where the truth is known. `rca simulate` generates software-service incidents (4 services x 3 regions, 48 hours of 5-minute metrics, plus deploy notes, config changes, alerts, tickets and logs) with one of five injected scenarios:

| Scenario | What happens | Expected verdict |
|---|---|---|
| `bad_deploy` | A release breaks one service in one region | sufficient |
| `config_change` | A config change slows one service everywhere | sufficient |
| `traffic_spike` | A campaign triples traffic in one region | sufficient |
| `dependency_outage` | An upstream dependency fails | sufficient |
| `no_clear_cause` | Errors rise with no record explaining why | **insufficient** |

Each incident folder holds `incident.json` (the question), `metrics.csv`, `records.jsonl` and `truth.json` (the real cause, hidden from the investigator and used only for scoring).

## Finding what changed

The numerical engine (`analyze.py`) uses simple, explainable statistics rather than a language model:

1. In every service/region segment it finds the most likely change point (the split that best separates the series into two levels).
2. It keeps segments whose change is significant (t statistic and before/after ratio) and happened at about the same time as the strongest one.
3. The pattern of affected segments says where the problem lives: one service, one region, or one service in one region.
4. It compares related metrics at the same moment, e.g. whether traffic also rose, which supports or rules out explanations.

Current results on 20 generated incidents: **right segment 100%**, **change time within 15 minutes 95%**.

## Finding the records that explain it

The text engine (`records.py`) ranks deploy notes, config changes, alerts, tickets and logs by four explainable signals, and lists the reasons for every score:

- **Text**: TF-IDF similarity to a query built from the detected change (metric words, affected service/region, traffic words if traffic rose).
- **Time**: causes come shortly before a change, symptoms shortly after; a record that names the change time (e.g. "goes live at 10:25") counts as on time.
- **Segment**: records about the affected service/region count more.
- **Source**: change events (deploys, config changes) outrank log lines, which are usually symptoms.

Current results on the 16 explainable incidents: **true cause ranked first in 16/16**.

## The investigator

`investigate.py` keeps the language model's job small, so a 3B model running on a laptop is enough:

1. Python gathers the facts (numerical and text engines) and numbers them as evidence `E1`, `E2`, ...
2. The model reasons only over that evidence: contributing factors with a "5 Whys" chain, ruled-out alternatives, corrective and preventive actions. Its reply is constrained to a JSON schema.
3. Guardrails check the reply: invented evidence IDs are removed, factors without evidence are dropped, factors resting only on records *after* the change (symptoms) are dropped, and the report must pass schema validation.
4. When the evidence is insufficient, factors are shown as **possible leads (not confirmed)** with low confidence, together with the data that would settle the question.

Example reports from `qwen2.5:3b`: [bad deploy](examples/reports/bad_deploy.md), [traffic spike](examples/reports/traffic_spike.md).

## Project structure

```
src/rca_investigator/
  schema.py     the RCA report format (with evidence-citation checks)
  llm.py        client for a local model served by Ollama
  simulate.py   synthetic incidents with known, injected root causes
  analyze.py    numerical engine: change point, size of change, affected segment
  records.py    text engine: ranked records with reasons, event timeline
  investigate.py  evidence pack, model prompt, guardrails, Markdown report
  cli.py        command-line interface (`rca ...`)
schemas/        JSON Schema of the report
examples/       example report
tests/          tests
docs/           roadmap
```

## License

MIT. See [LICENSE](LICENSE).
