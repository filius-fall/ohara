#!/usr/bin/env bash
set -euo pipefail

vault_dir="${OHARA_VAULT:-$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
primary_remote="${OHARA_PRIMARY_REMOTE:-origin}"
mirror_remote="${OHARA_MIRROR_REMOTE:-github}"
backup_date="$(TZ="${OHARA_TIMEZONE:-Asia/Kolkata}" date +%F)"

cd "$vault_dir"

if [[ -z "$(git status --porcelain)" ]]; then
    exit 0
fi

git add -A

if git diff --cached --quiet; then
    exit 0
fi

git commit -m "backup-${backup_date}"
git push "$primary_remote" main
git push "$mirror_remote" main
