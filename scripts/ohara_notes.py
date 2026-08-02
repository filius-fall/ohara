#!/usr/bin/env python3
"""Local-first metadata helper and one-way Notion backup for the Ohara vault."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_VAULT = Path(os.environ.get("OBSIDIAN_VAULT", "/home/sreeram/Notes"))
DEFAULT_DATABASE_ID = "39b40eaf-68f1-80db-b637-cb197b56ec09"
DEFAULT_NOTION_VERSION = os.environ.get("NOTION_VERSION", "2026-03-11")
API_ROOT = "https://api.notion.com/v1"
TYPE_NAMES = {
    "Fleeting Notes",
    "Literature Notes",
    "Permanent Notes",
    "Course",
    "Blog",
    "Anki",
    "Interview Prep",
}
EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".makemd",
    ".space",
    ".trash",
    "Archive",
    "Meta",
    "templates",
}
EXCLUDED_FILES = {"README.md", "AGENTS.md", "Untitled.md"}


class SyncError(RuntimeError):
    pass


def load_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[key.strip()] = value
    return result


def token_for(vault: Path) -> str:
    token = os.environ.get("NOTION_TOKEN", "").strip()
    env_file = os.environ.get("NOTION_ENV_FILE", "").strip()
    candidates = [Path(env_file)] if env_file else []
    if not env_file:
        candidates.append(Path("/home/sreeram/Projects/MCPServers/.env"))
    candidates.append(vault / ".env")
    if not token:
        for candidate in candidates:
            token = load_env(candidate).get("NOTION_TOKEN", "").strip()
            if token:
                break
    if not token:
        raise SyncError("NOTION_TOKEN is missing from Notes/.env or the environment")
    return token


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].replace("\\" + value[0], value[0])
    return value


def parse_list(value: str) -> list[str]:
    value = value.strip()
    if not value or value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        return [unquote(item) for item in value[1:-1].split(",") if item.strip()]
    return [unquote(value)]


def parse_frontmatter(text: str) -> tuple[dict[str, object], str, bool]:
    if not text.startswith("---\n"):
        return {}, text, False
    closing = text.find("\n---", 4)
    if closing < 0:
        return {}, text, False
    raw = text[4:closing]
    lines = raw.splitlines()
    valid = not raw.strip() or any(
        re.match(r"^(title|type|category|tags|created)\s*:", line)
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    )
    if not valid:
        return {}, text, False
    metadata: dict[str, object] = {}
    list_key: str | None = None
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and list_key:
            current = metadata.setdefault(list_key, [])
            if isinstance(current, list):
                current.append(unquote(item.group(1)))
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9 _-]*)\s*:\s*(.*)$", line)
        if not match:
            list_key = None
            continue
        key, value = match.groups()
        key = key.strip()
        if key == "tags":
            metadata[key] = parse_list(value)
            list_key = key
        else:
            metadata[key] = unquote(value)
            list_key = None
    return metadata, text[closing + 4 :], True


def quote(value: object) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def field_lines(key: str, value: object) -> list[str]:
    if key == "tags":
        tags = value if isinstance(value, list) else parse_list(str(value))
        return ["tags: []"] if not tags else ["tags:"] + [
            f"  - {quote(tag)}" for tag in tags
        ]
    return [f"{key}: {quote(value)}"]


def render_frontmatter(metadata: dict[str, object]) -> str:
    lines = ["---"]
    for key in ("title", "type", "category", "tags", "created"):
        default: object = [] if key == "tags" else ""
        lines.extend(field_lines(key, metadata.get(key, default)))
    return "\n".join(lines + ["---", ""])


def note_paths(vault: Path, include_archive: bool = False) -> list[Path]:
    excluded = set(EXCLUDED_DIRS)
    if include_archive:
        excluded.discard("Archive")
    paths = []
    for path in sorted(vault.rglob("*.md")):
        relative = path.relative_to(vault)
        if path.name in EXCLUDED_FILES:
            continue
        if any(part in excluded or part.startswith(".") for part in relative.parts):
            continue
        paths.append(path)
    return paths


def canonical_values(vault: Path, name: str) -> set[str]:
    path = vault / "Meta" / name
    if not path.is_file():
        return set(TYPE_NAMES) if name == "Types.md" else set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def inferred_type(path: Path, vault: Path) -> str:
    parent = path.relative_to(vault).parent.name
    return parent if parent in TYPE_NAMES else "Fleeting Notes"


def inferred_created(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(
        timespec="minutes"
    )


def metadata_for(path: Path, vault: Path) -> dict[str, object]:
    existing, _body, _valid = parse_frontmatter(
        path.read_text(encoding="utf-8")
    )
    tags = existing.get("tags", [])
    if isinstance(tags, str):
        tags = parse_list(tags)
    if not isinstance(tags, list):
        tags = []
    return {
        "title": str(existing.get("title") or path.stem),
        "type": str(existing.get("type") or inferred_type(path, vault)),
        "category": str(existing.get("category") or ""),
        "tags": [str(tag) for tag in tags],
        "created": str(existing.get("created") or inferred_created(path)),
    }


def metadata_issues(path: Path, vault: Path) -> list[str]:
    metadata, _body, valid = parse_frontmatter(
        path.read_text(encoding="utf-8")
    )
    issues = []
    if not valid:
        issues.append("missing valid frontmatter")
    for key in ("title", "type", "tags", "created"):
        if key not in metadata or metadata[key] is None or metadata[key] == "":
            issues.append("missing " + key)
    if metadata.get("type") and str(metadata["type"]) not in canonical_values(vault, "Types.md"):
        issues.append("unknown type: " + str(metadata["type"]))
    if (
        str(metadata.get("title") or "").strip().lower() == "untitled"
        and path.stem.strip().lower() != "untitled"
    ):
        issues.append("title is Untitled; choose a real title")
    category = str(metadata.get("category") or "")
    if category and category not in canonical_values(vault, "Categories.md"):
        issues.append("unknown category: " + category)
    return issues


def add_missing_metadata(path: Path, vault: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    existing, _body, valid = parse_frontmatter(text)
    missing = [
        key for key in ("title", "type", "category", "tags", "created")
        if key not in existing
    ]
    if not missing:
        return False
    resolved = metadata_for(path, vault)
    if not valid:
        path.write_text(render_frontmatter(resolved) + text, encoding="utf-8")
        return True
    closing = text.find("\n---", 4)
    additions = []
    for key in missing:
        additions.extend(field_lines(key, resolved[key]))
    path.write_text(
        text[:closing] + "\n" + "\n".join(additions) + text[closing:],
        encoding="utf-8",
    )
    return True


def body_for(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    _metadata, body, valid = parse_frontmatter(text)
    return (body if valid else text).strip()


def normalized(content: str) -> str:
    lines = [line.rstrip() for line in content.replace("\r\n", "\n").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines).strip())


def digest(content: str) -> str:
    return hashlib.sha256(normalized(content).encode("utf-8")).hexdigest()


def text_from_rich(items: object) -> str:
    if not isinstance(items, list):
        return ""
    return "".join(
        str(item.get("plain_text") or item.get("text", {}).get("content") or "")
        for item in items
        if isinstance(item, dict)
    )


def title_of(page: dict[str, object]) -> str:
    properties = page.get("properties", {})
    if not isinstance(properties, dict):
        return ""
    value = properties.get("Title") or properties.get("Name") or {}
    return text_from_rich(value.get("title", [])) if isinstance(value, dict) else ""


def summary_of(page: dict[str, object]) -> dict[str, object]:
    properties = page.get("properties", {})
    if not isinstance(properties, dict):
        return {"title": "", "type": "", "category": "", "tags": []}
    type_value = properties.get("Type", {})
    type_value = type_value.get("select") if isinstance(type_value, dict) else None
    category_value = properties.get("Categories", {})
    category_value = (
        category_value.get("multi_select", [])
        if isinstance(category_value, dict)
        else []
    )
    tags_value = properties.get("Tags", {})
    tags_value = (
        tags_value.get("multi_select", [])
        if isinstance(tags_value, dict)
        else []
    )
    return {
        "title": title_of(page),
        "type": type_value.get("name", "") if isinstance(type_value, dict) else "",
        "category": (
            category_value[0].get("name", "")
            if category_value and isinstance(category_value[0], dict)
            else ""
        ),
        "tags": [
            item.get("name", "")
            for item in tags_value
            if isinstance(item, dict) and item.get("name")
        ],
    }


def notion_properties(metadata: dict[str, object]) -> dict[str, object]:
    tags = metadata.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    category = str(metadata.get("category") or "")
    return {
        "Title": {
            "title": [{"type": "text", "text": {"content": str(metadata["title"])}}]
        },
        "Type": {"select": {"name": str(metadata["type"])}},
        "Categories": {
            "multi_select": [{"name": category}] if category else []
        },
        "Tags": {
            "multi_select": [{"name": str(tag)} for tag in tags if str(tag)]
        },
    }


class Notion:
    def __init__(self, token: str, version: str):
        self.token = token
        self.version = version

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        headers = {
            "Authorization": "Bearer " + self.token,
            "Notion-Version": self.version,
            "Content-Type": "application/json",
            "User-Agent": "ohara-notes-sync/1.0",
        }
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        for attempt in range(4):
            request = Request(
                API_ROOT + path,
                data=body,
                headers=headers,
                method=method,
            )
            try:
                with urlopen(request, timeout=45) as response:
                    raw = response.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                if error.code == 429 and attempt < 3:
                    try:
                        delay = min(30.0, max(1.0, float(error.headers.get("Retry-After", "2"))))
                    except ValueError:
                        delay = 2.0
                    time.sleep(delay)
                    continue
                raise SyncError(
                    f"Notion {method} {path} failed ({error.code}): {detail}"
                ) from error
            except URLError as error:
                if attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise SyncError(f"Notion {method} {path} failed: {error}") from error
        raise SyncError("Notion request failed after retries")

    def source(self, database_id: str) -> tuple[str, bool]:
        database = self.request("GET", "/databases/" + database_id)
        sources = database.get("data_sources", [])
        if isinstance(sources, list) and sources and isinstance(sources[0], dict):
            if sources[0].get("id"):
                return str(sources[0]["id"]), True
        return database_id, False

    def pages(self, database_id: str) -> tuple[str, bool, list[dict[str, object]]]:
        source_id, data_source = self.source(database_id)
        endpoint = (
            "/data_sources/" + source_id + "/query"
            if data_source
            else "/databases/" + source_id + "/query"
        )
        pages: list[dict[str, object]] = []
        cursor = None
        while True:
            payload: dict[str, object] = {"page_size": 100}
            if cursor:
                payload["start_cursor"] = cursor
            response = self.request("POST", endpoint, payload)
            results = response.get("results", [])
            if isinstance(results, list):
                pages.extend(item for item in results if isinstance(item, dict))
            cursor = response.get("next_cursor")
            if not cursor:
                return source_id, data_source, pages

    def create(
        self,
        source_id: str,
        data_source: bool,
        properties: dict[str, object],
        body: str,
    ) -> dict[str, object]:
        parent = (
            {"data_source_id": source_id}
            if data_source
            else {"database_id": source_id}
        )
        payload: dict[str, object] = {"parent": parent, "properties": properties}
        if body:
            payload["markdown"] = body
        return self.request("POST", "/pages", payload)

    def update_properties(self, page_id: str, properties: dict[str, object]):
        return self.request("PATCH", "/pages/" + page_id, {"properties": properties})

    def get_page(self, page_id: str):
        return self.request("GET", "/pages/" + page_id)

    def get_markdown(self, page_id: str) -> str:
        response = self.request("GET", "/pages/" + page_id + "/markdown")
        return str(response.get("markdown", ""))

    def replace_markdown(self, page_id: str, body: str):
        return self.request(
            "PATCH",
            "/pages/" + page_id + "/markdown",
            {
                "type": "replace_content",
                "replace_content": {"new_str": body},
            },
        )


def state_path(vault: Path) -> Path:
    return vault / "Meta" / "notion-sync-state.json"


def load_state(vault: Path) -> dict[str, object]:
    path = state_path(vault)
    if not path.is_file():
        return {"version": 1, "files": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SyncError(f"Invalid sync state: {path}: {error}") from error
    if not isinstance(value, dict):
        raise SyncError(f"Invalid sync state object: {path}")
    value.setdefault("version", 1)
    value.setdefault("files", {})
    return value


def save_state(vault: Path, state: dict[str, object]) -> None:
    path = state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sync_command(args: argparse.Namespace) -> int:
    vault = args.vault.resolve()
    paths = note_paths(vault, args.include_archive)
    if not paths:
        print("No Markdown notes found.")
        return 0
    notion = Notion(token_for(vault), args.notion_version)
    source_id, data_source, pages = notion.pages(args.database_id)
    state = load_state(vault)
    entries = state.setdefault("files", {})
    if not isinstance(entries, dict):
        raise SyncError("Sync state files must be an object")
    by_id = {
        str(page["id"]): page for page in pages if isinstance(page.get("id"), str)
    }
    by_title: dict[str, list[dict[str, object]]] = {}
    for page in pages:
        title = title_of(page).strip()
        if title:
            by_title.setdefault(title, []).append(page)
    print(f"Vault notes: {len(paths)}; Notion pages: {len(pages)}")
    writes = 0
    conflicts = 0

    for path in paths:
        relative = str(path.relative_to(vault))
        metadata = metadata_for(path, vault)
        if (
            str(metadata["title"]).strip().lower() == "untitled"
            and path.stem.strip().lower() != "untitled"
        ):
            print("CONFLICT " + relative + ": title is Untitled; skipped")
            conflicts += 1
            continue
        body = body_for(path)
        local_digest = digest(body)
        entry = entries.get(relative, {})
        if not isinstance(entry, dict):
            entry = {}
        page = by_id.get(str(entry.get("page_id", "")))
        if page is None:
            candidates = by_title.get(str(metadata["title"]).strip(), [])
            if len(candidates) == 1:
                page = candidates[0]
            elif len(candidates) > 1:
                print(f"CONFLICT {relative}: duplicate Notion title; skipped")
                conflicts += 1
                continue

        if page is None:
            print("CREATE " + relative)
            if args.apply:
                page = notion.create(
                    source_id,
                    data_source,
                    notion_properties(metadata),
                    body,
                )
                writes += 1
                entries[relative] = {
                    "page_id": str(page["id"]),
                    "local_hash": local_digest,
                    "notion_last_edited_time": page.get("last_edited_time", ""),
                    "content_managed": True,
                }
            continue

        page_id = str(page["id"])
        now_notion = str(page.get("last_edited_time", ""))
        old_hash = str(entry.get("local_hash", ""))
        old_notion = str(entry.get("notion_last_edited_time", ""))
        managed = bool(entry.get("content_managed", False))

        if not old_hash:
            if args.apply:
                matches = digest(notion.get_markdown(page_id)) == local_digest
                managed = matches
                if matches:
                    print("ADOPT " + relative + ": body matches")
                else:
                    print("CONFLICT " + relative + ": existing body preserved")
                    conflicts += 1
            entries[relative] = {
                "page_id": page_id,
                "local_hash": local_digest,
                "notion_last_edited_time": now_notion,
                "content_managed": managed,
            }
        else:
            local_changed = local_digest != old_hash
            notion_changed = bool(old_notion) and now_notion != old_notion
            if notion_changed and args.apply:
                if digest(notion.get_markdown(page_id)) != local_digest:
                    managed = False
                    print("CONFLICT " + relative + ": Notion changed; body preserved")
                    conflicts += 1
                else:
                    managed = True
                    old_notion = now_notion
            if local_changed:
                if managed and not notion_changed:
                    if args.push_content:
                        print("UPDATE BODY " + relative)
                        if args.apply:
                            notion.replace_markdown(page_id, body)
                            refreshed = notion.get_page(page_id)
                            old_notion = str(
                                refreshed.get("last_edited_time", now_notion)
                            )
                            old_hash = local_digest
                            writes += 1
                    else:
                        print("PENDING BODY " + relative + ": use --push-content")
                else:
                    print("CONFLICT " + relative + ": both sides changed; body skipped")
                    conflicts += 1

        current = summary_of(page)
        wanted = {
            "title": str(metadata["title"]),
            "type": str(metadata["type"]),
            "category": str(metadata["category"]),
            "tags": sorted(str(tag) for tag in metadata["tags"]),
        }
        actual = {
            "title": str(current["title"]),
            "type": str(current["type"]),
            "category": str(current["category"]),
            "tags": sorted(str(tag) for tag in current["tags"]),
        }
        if actual != wanted:
            print("UPDATE METADATA " + relative)
            if args.apply:
                updated = notion.update_properties(page_id, notion_properties(metadata))
                old_notion = str(updated.get("last_edited_time", old_notion))
                writes += 1
        entries[relative] = {
            "page_id": page_id,
            "local_hash": old_hash or local_digest,
            "notion_last_edited_time": old_notion or now_notion,
            "content_managed": managed,
        }

    if args.apply:
        save_state(vault, state)
        print("State saved: " + str(state_path(vault)))
    print(f"Finished: {writes} write(s), {conflicts} conflict(s).")
    return 2 if conflicts else 0


def metadata_command(args: argparse.Namespace) -> int:
    vault = args.vault.resolve()
    paths = note_paths(vault, args.include_archive)
    problem_count = 0
    changed = 0
    for path in paths:
        issues = metadata_issues(path, vault)
        if issues:
            problem_count += 1
            print(f"{path.relative_to(vault)}: {', '.join(issues)}")
            if args.apply and add_missing_metadata(path, vault):
                changed += 1
    if args.apply:
        print(f"Metadata files changed: {changed}")
    print(f"Notes checked: {len(paths)}; notes with issues: {problem_count}")
    return 1 if problem_count and not args.apply else 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    root.add_argument("--include-archive", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)
    metadata = commands.add_parser("metadata")
    metadata.add_argument("--check", action="store_true")
    metadata.add_argument("--apply", action="store_true")
    metadata.set_defaults(run=metadata_command)
    sync = commands.add_parser("sync")
    sync.add_argument("--apply", action="store_true")
    sync.add_argument("--push-content", action="store_true")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--database-id", default=DEFAULT_DATABASE_ID)
    sync.add_argument("--notion-version", default=DEFAULT_NOTION_VERSION)
    sync.set_defaults(run=sync_command)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        return int(args.run(args))
    except SyncError as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
