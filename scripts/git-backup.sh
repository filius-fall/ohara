#!/usr/bin/env bash
set -euo pipefail

vault_dir="${OHARA_VAULT:-$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
offsite_remote="${OHARA_OFFSITE_REMOTE:-github}"
mirror_remote="${OHARA_MIRROR_REMOTE:-}"
backup_date="$(TZ="${OHARA_TIMEZONE:-Asia/Kolkata}" date +%F)"

cd "$vault_dir"

if [[ -n "$(git status --porcelain)" ]]; then
    git add -A

    if ! git diff --cached --quiet; then
        git commit -m "backup-${backup_date}"
    fi
fi

git push "$offsite_remote" main

if [[ -n "$mirror_remote" ]]; then
    git push "$mirror_remote" main
fi
