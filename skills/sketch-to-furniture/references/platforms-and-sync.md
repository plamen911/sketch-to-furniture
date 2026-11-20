# Platforms, Free-plan target and GitHub synchronization

Checked against official documentation on 20 November 2026. These are distribution boundaries, not a claim that this package has been installed or tested on every account.

## Supported execution paths

The Python engine is independent of an OpenAI API key. Its core uses the Python standard library; optional PNG rendering uses Pillow. A host must actually provide Python, files and sufficient execution allowance. The self-contained HTML viewer opens in a browser on desktop or phone after the result files are delivered; a localhost URL is local to the machine that serves it.

[Build skills](https://learn.chatgpt.com/docs/build-skills) distinguishes standalone filesystem skills from skills bundled in plugins. The latter are the route for ChatGPT web, desktop and mobile distribution. This repository can build such a portable package; packaging alone is not installation, publication or an entitlement to tools.

The **ChatGPT Free** requirement is an acceptance target, not yet a verified guarantee. Do not require a paid image-generation API: render actual geometry using the supplied code. If the account cannot execute the generator, return reviewed structured parameters and explain that generation still needs a compatible execution host. Do not claim a prompt can add a tool or bypass usage limits. See [official pricing and limits](https://learn.chatgpt.com/docs/pricing).

## Synchronization means different things

- GitHub is the source of versioned code, instructions, tests and release bundles. CI tests and rebuilds the bundle after each main-branch push, then updates a generated distribution branch without force-pushing. This branch contains the portable plugin and marketplace manifest; it is distinct from an installed client copy.
- A desktop checkout may update using `scripts/sync_repo.py`; it refuses dirty worktrees and only accepts fast-forward updates. It is a one-way updater, not a scheduled service or an automatic push of conversation edits.
- [Workspace GitHub import/sync](https://learn.chatgpt.com/docs/enterprise/plugin-management) requires workspace administration. It is not evidence that the same automatic installed-plugin sync exists for a personal Free account.
- An uploaded ZIP is a snapshot. It does not become a GitHub live connection. Start a new chat with the latest release when that is the available distribution path.
- Never auto-publish customer photos, discussions, prices negotiated privately, or every chat edit to a public repository. Publish maintained code and sanitized examples. Client projects stay under ignored `projects/`.

The portable plugin follows the [official package format](https://developers.openai.com/plugins/build/plugins). Public directory submission and workspace installation remain separate steps. No MCP endpoint, app account or credential is bundled.

## Acceptance matrix

| Path | Current evidence | Remaining verification |
| --- | --- | --- |
| Python on this Mac | Generator and behavioral tests | Real SketchUp import on the user's version |
| Browser viewer | Chrome external/interior view tested | Mobile Safari/Chrome and actual phone delivery |
| ChatGPT Desktop | Used to author and invoke local files | Fresh plugin installation |
| ChatGPT web/mobile | Portable package prepared | Account-level install, Python/Pillow execution and quota behavior |
| ChatGPT Free | No API key required by project code | End-to-end test on the cabinetmaker's actual Free account |
| GitHub CI | Source tests, fresh-package execution, distribution update and Pages deployment passed | Recheck after future changes |
| Installed plugin auto-sync | Workspace route documented | Personal Free route not established |

First verified automated run: https://github.com/plamen911/sketch-to-furniture/actions/runs/44780685324. Public sanitized demo: https://plamen911.github.io/sketch-to-furniture/. Desktop Chrome and a 390 px responsive viewport were checked; a physical phone test remains pending.
