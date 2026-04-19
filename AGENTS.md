# AGENTS.md

## Project Notes

1. Use `uv run main.py publish --dry-run` to test changes made to the markdown generator and verify the generated report output locally.
2. Follow these rules for documentation separation of concerns:
   - `docs/SUMMARY.md`: Report details, output formats, and generated layout rules.
   - `README.md`: User guide, high-level project setup, and CLI command usage.
   - `src/README.md`: Technical details, implementation architecture, and database schemas.
3. Use `make test-ci` when you need a local run that matches the pinned CI Python version and test entrypoint as closely as possible.
4. Always run `make test-ci` after code changes made to confirm all tests pass before committing. Never commit code with failing tests.
