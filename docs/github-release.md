# GitHub release notes / 发布须知

Suggested repository name: `travel-advisor-skill`  
Suggested description: `Travel research, hotel comparison, budget assistance, and itinerary planning Agent Skill with source verification and personalized recommendations.`  
Suggested topics: `agent-skills`, `codex`, `claude-code`, `travel`, `travel-planning`, `decision-support`, `ai-agent`, `python`

## Before publishing

1. Check `SKILL.md`, `README.md`, `README.zh-CN.md`, references, and example inputs.
2. Run `python -m unittest discover -s tests -v` and `python scripts/travel.py --capabilities`.
3. Ensure no secrets, personal itineraries, private booking records, or copyrighted platform dumps have been committed.
4. Confirm that `LICENSE`, `SECURITY.md`, and `CONTRIBUTING.md` suit the project.
5. Verify skill behavior in the intended agent host with real, accessible sources. Offline test passing does not prove live lookup quality.
6. Publish the repository and configure topics in GitHub settings.

## Publication commands (run locally, not required for users)

```bash
cd travel-advisor-skill
git init
git add .
git commit -m "Initial open-source release"
git branch -M main
# Create the repository on GitHub first, then add your actual remote URL:
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

No GitHub repository has been created automatically. The project name is descriptive and is not a trademark clearance.
