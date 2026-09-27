# VANDAL CS 1.6 Anti-Cheat

Official public website and download page for **VANDAL**, a defensive Counter-Strike 1.6 anti-cheat project.

- Website: GitHub Pages deployment from this repository
- Platform: Windows 10/11 x64
- Focus: process/module/memory/handle observations, clean baseline, evidence correlation, and human review

> Engineering preview. Production Authenticode signing and broad field validation are still pending.

## Development

Run the static site checks (internal links, sitemap, JSON-LD, SHA-256 and build consistency) before pushing:

```sh
python3 scripts/check_site.py
```

The same check runs in CI on every pull request; `main` is deployed to GitHub Pages only after it passes.
