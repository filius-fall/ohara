# Ohara vault workflow

This vault is local-first. Markdown note bodies are the user's content and must
not be rewritten, polished, corrected, summarized, or silently moved.

When Pi creates or processes a note:

- Add or repair only YAML frontmatter.
- Infer type from the note's folder using the exact names in Meta/Types.md.
- Reference/ holds pasted source material (LLM output, docs); its notes get
  type: Reference and may keep pasted bodies as-is.
- Trash/ holds processed Fleeting notes; it is excluded from sync, metadata
  checks, and search. Never move user notes there yourself — only on request.
- Choose category and tags from Meta/Categories.md and Meta/Tags.md when the
  note clearly supports them. Leave them empty rather than guessing.
- Keep the exact existing title and created values when present.
- If a title or date is missing, use the filename and file creation time.
- Do not modify spelling, punctuation, links, whitespace, code, or references in
  the body.
- Do not overwrite a note with a Notion version. Conflicts must be reported.

Useful commands from the vault root:

    python scripts/ohara_notes.py metadata --check
    python scripts/ohara_notes.py metadata --apply
    python scripts/ohara_notes.py sync --dry-run
    python scripts/ohara_notes.py sync --apply --push-content

The script uses the local MCP server token at
/home/sreeram/Projects/MCPServers/.env when that file exists. To use another
Notion integration, set NOTION_ENV_FILE to an env file containing NOTION_TOKEN.

The weekly sync is one-way: local Markdown -> the Notion Learning Notes
database. It updates the board properties Type, Categories, and Tags, creates
missing pages, and publishes local body changes only when the Notion page has
not changed since the last safe sync. It stops on two-sided changes.
