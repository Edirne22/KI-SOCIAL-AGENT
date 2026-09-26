#!/usr/bin/env bash
set -euo pipefail

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

git add -A -- memory/ assets/images/
if [ -f content/MOTOGP_ROSTER_NEXT.md ]; then git add -- content/MOTOGP_ROSTER_NEXT.md; fi
if git diff --cached --quiet; then
  echo "Keine Agency-Änderungen zu speichern"
  exit 0
fi
git commit -m "Auto: Racing V8.5 state and audit"
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "FEHLER: Arbeitsbaum nach Persistenz nicht sauber"
  git status --short
  exit 1
fi

for attempt in 1 2 3; do
  echo "Persistenz-Versuch ${attempt}/3"
  git fetch origin main
  if git rebase -X theirs origin/main; then
    if git push origin HEAD:main; then
      echo "Racing-Persistenz erfolgreich"
      exit 0
    fi
  else
    git rebase --abort || true
  fi
  sleep $((attempt * 2))
done

echo "FEHLER: Racing-Persistenz nach 3 konfliktrobusten Versuchen fehlgeschlagen"
exit 1
