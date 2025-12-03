Title: <concise, factual PR title>

## Short description
- 2–3 sentences summarizing what changed and why (neutral, technical tone).

## Scope of changes (files/areas)
- List the key changes with references to files/directories.
- Keep existing section structure and minimal diffs (per `copilot_update_project_playbook.md`).

## Motivation and context
- Why is the change needed? Does it fix a bug, address technical debt, or improve documentation?
- Reference related design decisions if applicable.

## Tests
- List every test that was run with commands (e.g., `pytest tests/test_etl.py`).
- If tests were skipped, explain why and how that affects regression risk.

## Risks / regression impact
- Describe potential regressions, limitations, or areas needing extra validation.
- Note any environment/configuration requirements (e.g., extra dependencies, data changes).

## Notes for reviewers
- Optional guidance to simplify review (e.g., review order, specific scenarios to verify).

## Pre-merge checklist
- [ ] Changes align with the current repository structure and vision (see `copilot_update_project_playbook.md`).
- [ ] Tests cover primary usage paths, or skipped tests are justified.
- [ ] Risks/regressions are identified and described.
