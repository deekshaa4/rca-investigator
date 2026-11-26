# Roadmap

A focused 2-week build, using only free and open tools.

## Week 1: a working investigator (v0.1) ✅

- [x] Project setup, report format (JSON Schema), local model client
- [x] Incident simulator: metrics and text records with known, injected root causes (bad deploy, config change, traffic spike, dependency outage, no clear cause)
- [x] Numerical engine: change-point detection, size of change, segment drill-down
- [x] Text engine: record search and an event timeline around the change
- [x] LLM investigator: evidence pack in, structured cited report out
- [x] Command-line interface: `rca investigate <incident>`

## Week 2: trust and presentation (v1.0) ✅

- [x] Evidence sufficiency check: timing match, agreement between numbers and records, ruled-out alternatives, data gaps
- [x] Harder incidents: noise, red herrings, overlapping changes, missing records
- [x] Evaluation: `rca evaluate` with verdict, segment, category and cause-citation accuracy, invented-evidence rate, and breakdowns by scenario and twist
- [x] Better choice of cause on red herrings and competing changes (fit notes, engine overrule, naming all equally good candidates)
- [x] Chat web page: upload files or paste data, ask questions, CuteBot roams the page showing each stage, then presents the report and answers follow-ups
- [x] Connect to databases and folders (read-only), with automatic table discovery
- [x] Explanations for every reader (data nerd, straight answer, like I'm 5), chart, report download
- [x] Documentation, examples and v1.0 release

## Later

- Fine-tune a small open model (LoRA) on investigation examples and compare with the base model
- More domains (manufacturing quality, business KPIs)
- Public incident datasets
