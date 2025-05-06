#!/bin/bash

# カレントディレクトリをリポジトリのルートに設定
cd /Users/koheimacmini/Documents/40_Program/20250506_Claude_Code_SecondeChallenge/lifeplan-simulator

# 現在の日時を取得
DATETIME=$(date '+%Y-%m-%d %H:%M:%S')

# 変更があるか確認
if [[ -z $(git status -s) ]]; then
  echo "$DATETIME: 変更はありません。"
  exit 0
fi

# 変更をステージングしてコミット
git add .
git commit -m "自動バックアップ: $DATETIME"

# GitHubにプッシュ
git push origin main

echo "$DATETIME: 変更を自動コミットしてGitHubにプッシュしました。"