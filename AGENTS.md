# AGENTS.md

## Project Notes

1. Use `uv run main.py publish --dry-run` to test changes made to the markdown generator and verify the generated report output locally.
2. Update both `README.md` and `src/README.md` when code changes affect documented behavior, workflows, commands, or output.
3. Use `make test-ci` when you need a local run that matches the pinned CI Python version and test entrypoint as closely as possible.
4. Always run `uv run pytest` (or `make test-ci`) and confirm all tests pass before committing. Never commit code with failing tests.
