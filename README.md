# Ohara — Zettelkasten Vault

Personal Obsidian vault. Synced to [GitHub](https://github.com/filius-fall/ohara) and a self-hosted Gitea on `indra` (Tailscale).

## Structure

```
Notes/
├── Fleeting Notes/      daily captures, quick ideas (Obsidian "daily notes" land here)
├── Literature Notes/    notes taken from sources (books, articles, videos)
├── Permanent Notes/     refined, atomic, evergreen ideas
├── Archive/             old / superseded content (pre-2024 notes live here)
├── attachments/         images, PDFs, etc.
├── templates/           one template per Type (body-only; frontmatter is baked by `n`)
├── .zk-types            canonical Type picklist (one per line)
├── .zk-categories       canonical Category picklist (one per line)
├── .obsidian/           vault config (synced; machine-local bits gitignored)
└── .gitignore
```

## Frontmatter schema (every note)

```yaml
---
title: "Note Title"
type: literature             # from .zk-types
category: philosophy         # from .zk-categories (optional)
created: 2026-07-27T10:17:22+05:30
tags:
  - reading
  - whatever-you-want
---
```

Tags are free-form. Type and Category come from the canonical files to prevent typos.

## Workflow (terminal-first, Helix)

```bash
n "Title"                       # create: pick Type, Category, Tags via fzf
n -T permanent -C philosophy "Title"
n -t idea,wisdom "Title"        # --tag (singular; --tags lists existing)
n -l                             # list / jump to notes (fzf + glow)
n -s pattern                     # search notes (fzf + ripgrep)
n --tags                         # list all existing tags in vault
n --types / --categories         # show canonical picklists
n --push                         # git add + commit + push (github + gitea)
n --pull                         # git pull from gitea (Tailscale-fast)
```

Editor override: `EDITOR=helix n "Title"` (default is `hx`).
Vault override: `OBSIDIAN_VAULT=/path n "Title"`.

## Sync model

- **Single push, two destinations** — `git push origin main` hits GitHub (public mirror) and Gitea on indra (private fast sync over Tailscale) via configured `pushurl`s.
- **Other devices** — `git clone ssh://indra@indra.tail21eced.ts.net:2222/filiusfall/Ohara.git` or pull via `n --pull`.
- **Notion** — open the note, copy, paste into Notion (paste-as-markdown converts frontmatter to a code block; acceptable for archival).

## Remotes

```
origin  git@github.com:filius-fall/ohara.git                            (fetch)
origin  git@github.com:filius-fall/ohara.git                            (push)
origin  ssh://indra@indra.tail21eced.ts.net:2222/filiusfall/Ohara.git   (push)
gitea   ssh://indra@indra.tail21eced.ts.net:2222/filiusfall/Ohara.git   (fetch + push)
```
