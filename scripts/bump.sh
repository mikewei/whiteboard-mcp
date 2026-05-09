#!/usr/bin/env bash

set -euo pipefail

part="${1:-patch}"

# changelog
scripts/cliff.sh

read -p "Confirm changelog? (y/n) " confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted"
    exit 1
fi

scripts/cliff.sh > CHANGELOG.md
git add CHANGELOG.md
git commit -m "chore: update changelog"


# bump version
bump-my-version bump "$part" --dry-run

read -p "Confirm bump? (y/n) " confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted"
    exit 1
fi

bump-my-version bump "$part"

# refresh lockfile
uv lock

# read new version from pyproject.toml
version="$(python - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)
print(data["project"]["version"])
PY
)"

tag="v${version}"

# commit
git diff

read -p "Confirm commit ${tag}? (y/n) " confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted"
    exit 1
fi

git add pyproject.toml CHANGELOG.md uv.lock
git commit -m "release: ${tag}"
git tag -a "${tag}" -m "${tag}"

# all done
echo "Released ${tag}"
