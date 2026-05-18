#!/bin/bash
# Atsawin Auto Push Script
# ใช้: ./push.sh "commit message"
# หรือ: ./push.sh  (จะใช้ default message)

cd /root/AI

# Check if there are changes
if git diff --quiet && git diff --staged --quiet; then
    echo "No changes to push."
    exit 0
fi

# Stage all changes
git add -A

# Commit
MSG="${1:-Auto update: $(date '+%Y-%m-%d %H:%M')}"
git commit -m "$MSG"

# Push
git push origin main

echo "✅ Pushed: $MSG"
