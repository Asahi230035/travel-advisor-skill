# Contributing to Travel Advisor Skill

Contributions to instructions, evidence policies, low-dependency code, documentation and test cases are welcome.

1. Open an issue describing the concrete travel decision that currently fails or becomes confusing.
2. Keep changes aligned with the core promise: **task-sized answers, no mandatory setup**.
3. If changing `SKILL.md`, update relevant reference docs and add a scenario under `evals/scenarios.md`.
4. If changing Python, include regression tests; run `python -m unittest discover -s tests -v`.
5. Do not add mandatory API keys, proprietary datasets, non-stdlib Python dependencies, scraping bypasses or unverified claims of real-time access.
6. Label all example prices, locations and quoted content as synthetic unless they are documented and licensed source materials.
7. Do not include personal identifiers, booking confirmations, private emails, access tokens, or copyrighted full posts in issues or pull requests.

A good pull request explains the user-facing behavior, the failure it fixes, the test case, and any host-compatibility concerns.
