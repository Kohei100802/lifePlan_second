#!/bin/bash

# 設定
REPO_PATH="/Users/koheimacmini/Documents/40_Program/20250506_Claude_Code_SecondeChallenge/lifeplan-simulator"
LOG_FILE="$REPO_PATH/github_sync.log"
BRANCH="main"
REMOTE="origin"

# タイムスタンプ関数
timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

# ログ出力関数
log_message() {
  echo "$(timestamp) - $1" >> "$LOG_FILE"
  echo "$(timestamp) - $1"
}

# スクリプト開始のログ出力
log_message "GitHub 同期スクリプトを開始します..."

# リポジトリディレクトリに移動
cd "$REPO_PATH" || {
  log_message "エラー: リポジトリディレクトリに移動できません。"
  exit 1
}

# 現在の状態を確認
git_status=$(git status --porcelain)

# 変更があるかどうかをチェック
if [ -n "$git_status" ]; then
  log_message "変更が検出されました。コミットして同期します..."
  
  # 変更をすべて追加
  git add .
  
  # コミット
  COMMIT_MSG="自動同期: $(timestamp)"
  if git commit -m "$COMMIT_MSG"; then
    log_message "コミット成功: $COMMIT_MSG"
  else
    log_message "警告: コミットに失敗しました。"
  fi
  
  # プッシュ
  if git push origin main; then
    log_message "同期成功: 変更をGitHubにプッシュしました。"
  else
    log_message "エラー: プッシュに失敗しました。"
  fi
else
  log_message "変更はありません。リモートの変更を確認します..."
  
  # リモートの変更を取得
  git fetch origin
  
  # リモートに変更があるか確認
  if git status -uno | grep -q "Your branch is behind"; then
    log_message "リモートに変更があります。プルします..."
    if git pull origin main; then
      log_message "同期成功: リモートの変更を取得しました。"
    else
      log_message "エラー: プルに失敗しました。"
    fi
  else
    log_message "リモートとローカルは同期しています。変更はありません。"
  fi
fi

log_message "GitHub 同期スクリプトを終了します。"
