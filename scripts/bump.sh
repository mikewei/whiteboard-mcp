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
if git diff --cached --quiet; then
    echo "No changelog changes to commit, skipping."
else
    git commit -m "chore: update changelog"
fi


# bump version
bump-my-version bump "$part" --dry-run --verbose

read -p "Confirm bump? (y/n) " confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted"
    exit 1
fi

bump-my-version bump "$part"

# refresh lockfile
uv lock

# read new version from pyproject.toml
version=$(grep '^version = ' pyproject.toml | head -1 | sed -E 's/version = "(.*)"/\1/')
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
