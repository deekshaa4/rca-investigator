# Contributing

Thanks for your interest! Bug reports, ideas and pull requests are all welcome.

## Set up

```bash
git clone https://github.com/deekshaa4/rca-investigator.git
cd rca-investigator
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q && ruff check .
```

For the language model, install [Ollama](https://ollama.com) and run `ollama pull qwen2.5:3b`. Everything also works without it (`--no-llm`, or untick "AI model" on the web page).

## Ground rules

- **No evidence, no claim.** Anything the report says must be traceable to a numbered piece of evidence.
- **Rules decide, the model explains.** The sufficiency verdict stays rule-based and testable.
- **Read-only and local.** Connected sources must never be written to, and data must not leave the machine.
- **Measure changes.** If a change affects results, run `rca batch data/hard` (create it with `rca simulate --hard --n 50 --out data/hard`) and include the before/after scores from `rca evaluate`.

## Pull requests

1. Open an issue first for anything larger than a small fix.
2. Add or update tests; `pytest -q` and `ruff check .` must pass (CI runs both).
3. Keep pull requests focused, and explain the *why* in the description.

## Good first contributions

- New record sources or column-name synonyms in `ingest.py`
- A connector for another data source in `sources.py`
- More incident types or twists in `simulate.py`
- Accessibility and layout improvements to the web page
