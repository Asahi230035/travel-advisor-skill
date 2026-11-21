# GitHub Release Guide / 发布须知 (v2.0.0)

## Repository Metadata

- **Suggested repository name:** `travel-advisor-skill`
- **Suggested description:** `Evidence-first, real-time travel planning and decision Agent Skill — domain playbooks, strict freshness/authenticity checks, decision formats, and zero-setup stdlib helpers.`
- **Suggested topics:** `agent-skills`, `codex`, `claude-code`, `antigravity`, `travel`, `travel-planning`, `decision-support`, `ai-agent`, `python`

## Pre-Release Checklist

1. Confirm `SKILL.md`, `README.md`, `README.zh-CN.md`, `CHANGELOG.md`, `references/`, `examples/`, and `docs/` are all aligned on `2.0.0`.
2. Run the full test suite and CLI smoke checks:
   ```bash
   python3 -m unittest discover -s tests -v
   python3 scripts/travel.py --capabilities
   ```
3. Confirm `.gitignore` and `.github/workflows/ci.yml` are present and no `__pycache__/`, `.DS_Store`, secrets, or personal travel records are included.
4. Review `LICENSE` and `SECURITY.md`.
5. Run behavioral spot-checks from [evals/scenarios.md](../evals/scenarios.md) in your target agent host with live tools enabled.

## Git Push & Tag Commands

### Option A: Pushing to an existing GitHub repo (e.g. `travel-advisor-skill`)

```bash
cd travel-advisor-skill-main
git init
git add .
git commit -m "feat!: release Travel Advisor Skill v2.0.0"
git branch -M main
git remote add origin https://github.com/Asahi230035/travel-advisor-skill.git
# If pushing onto an existing history, pull/rebase or sync with your cloned repo first.
git push -u origin main
git tag -a v2.0.0 -m "v2.0.0: Real-time freshness guarantees, domain playbooks, decision formats & exporters"
git push origin v2.0.0
```

### Option B: Updating an already cloned local repository

Copy the contents of `travel-advisor-skill-main/` into your existing git clone (removing retired v1 files), then:

```bash
git status
git add -A
git commit -m "feat!: release Travel Advisor Skill v2.0.0"
git tag -a v2.0.0 -m "v2.0.0: Real-time freshness guarantees, domain playbooks, decision formats & exporters"
git push origin main --tags
```

## GitHub Release Notes Template (`v2.0.0`)

```markdown
## Travel Advisor Skill v2.0.0

A major architecture and domain-craft upgrade turning Travel Advisor into an **evidence-first, real-time travel planning copilot** — still zero-setup, API-key-free, and Python stdlib-only.

### Highlights
- **Real-time freshness & authenticity guarantees**: bans model-memory fallbacks for volatile travel facts; adds dual-date freshness checks (`retrieved_at` + `published_at`), future-timestamp rejection, and a snippet-only gate in `travel_core/evidence.py`; standardizes four-state provenance badges (`✅ / ≈ / ⚠️ / ❓`).
- **4 new/upgraded domain playbooks (progressive disclosure)**: itinerary routing & pacing (calendar/Monday closures, Plan B, booking countdowns), stays & door-to-door transport (hub radius, hotel switching, rail vs air, transit pass break-even), balanced budgets & flip conditions, and traveler profiles (kids, seniors, group split-and-rejoin, cross-border readiness).
- **Unified, practical CLI (`scripts/travel.py`)**: supports `--stdin`, `--lang auto|zh|en`, multi-currency FX & hidden surcharge normalization (`compare`), 3-tier budgets & `pass_check`, plus pure-stdlib `.ics` calendar and XSS-safe single-file offline HTML exporters (`export_ics`, `export_html`).
- **24-scenario behavioral eval suite + 27 automated tests** with GitHub Actions CI across Python 3.10–3.12.

### Breaking changes from v1.x
- Retired redundant standalone scripts (`scope_guard.py`, `clarification_priority.py`, `rank_stability.py`, `score_plans.py`, `allocate_budget.py`) in favor of the unified `scripts/travel.py` entry point.
- Reorganized `references/` into 7 focused core + domain playbooks.
```
