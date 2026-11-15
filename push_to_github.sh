#!/usr/bin/env bash
# Run from anywhere:  bash /c/Users/USER/PI-AI-MM/paper/push_to_github.sh
# Review each commit with `git show --stat` before the final push if you like.
set -euo pipefail
cd "$(dirname "$0")"

# Optional: set INCLUDE_REVIEW=1 to also publish the simulated reviewer reports.
INCLUDE_REVIEW="${INCLUDE_REVIEW:-1}"

git add .gitignore
git commit -m "chore: ignore LaTeX build products in all manuscript subfolders"

git add figures tables scripts/make_figures.py scripts/make_tables.py CHECKSUMS.sha256
git commit -m "feat: renumber tables, add table 8 and supplementary tables, rebuild figures"

git add scripts/pipeline/revision results/revision
git commit -m "feat: add revision analyses (code and results)"

git add manuscript/main manuscript/revision manuscript/CITATION_CHECK.md manuscript/DRAFT_NOTES.md
git commit -m "docs: add Nature-format manuscript, submission copy and revision notes"

git add manuscript/springer_nature
git commit -m "docs: add Springer Nature template manuscript, supplementary and build scripts"

if [ "$INCLUDE_REVIEW" = "1" ]; then
  git add manuscript/review
  git commit -m "docs: add simulated review rounds"
fi

# Catch-all: anything still uncommitted (including this script) so the remote matches the local folder exactly.
git add -A
git diff --cached --quiet || git commit -m "chore: sync remaining files"

echo; git status -sb; echo
git push origin main
