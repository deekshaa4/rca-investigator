# Roadmap

A focused 2-week build, using only free and open tools.

## Week 1: a working investigator (v0.1)

- [x] Project setup, report format (JSON Schema), local model client
- [x] Incident simulator: metrics and text records with known, injected root causes (bad deploy, config change, traffic spike, dependency outage, no clear cause)
- [ ] Numerical engine: change-point detection, size of change, segment drill-down
- [ ] Text engine: record search and an event timeline around the change
- [ ] LLM investigator: evidence pack in, structured cited report out
- [ ] Command-line interface: `rca investigate <incident>`

## Week 2: trust and presentation (v1.0)

- [ ] Evidence sufficiency check: timing match, agreement between numbers and records, ruled-out alternatives, data gaps
- [ ] Harder incidents: noise, red herrings, overlapping changes, missing records
- [ ] Evaluation: top-1 / top-3 cause accuracy, citation accuracy, invented-evidence rate, correct "insufficient" verdicts
- [ ] Web interface with an animated investigator bot that shows each step live and presents the report
- [ ] Documentation, examples and v1.0 release

## Later

- Fine-tune a small open model (LoRA) on investigation examples and compare with the base model
- More domains (manufacturing quality, business KPIs)
- Public incident datasets
