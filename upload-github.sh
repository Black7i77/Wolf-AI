#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v gh >/dev/null || { echo 'GitHub CLI is required for uploading: sudo apt install gh'; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'First sign into your GitHub account using: gh auth login'; exit 1; }
WOLF_OWNER="$(gh api user --jq .login)"
WOLF_REPO="${1:-Wolf-AI}"
[[ "$WOLF_REPO" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo 'Use a repository name with letters, digits, periods, hyphens or underscores.'; exit 1; }
[[ ! -d .git ]] || { echo 'A Git repository is already present. Stopping to preserve it.'; exit 1; }
if gh repo view "$WOLF_OWNER/$WOLF_REPO" >/dev/null 2>&1; then
  echo 'That repository already exists. Choose another name: bash upload-github.sh Wolf-AI-Website'
  exit 1
fi
git init -b main
git add .
git -c user.name='Wolf AI contributors' -c user.email='wolf-ai@users.noreply.github.com' commit -m 'Add MIT-licensed Wolf AI website and Cloudflare public demo'
gh repo create "$WOLF_OWNER/$WOLF_REPO" --public --source=. --remote=origin --push --description 'Local Ollama chat website with coding tools and a Cloudflare demo launcher'
gh repo view "$WOLF_OWNER/$WOLF_REPO" --json url --jq .url > .wolf-github-url
echo 'GitHub source published. Restart the public demo to show its source link:'
cat .wolf-github-url
