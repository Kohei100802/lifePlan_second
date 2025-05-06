# ライフプランシミュレーター

Mac上で動作し、インターネット上のスマートフォンからもアクセス可能なライフプランシミュレーションWebアプリです。

## 1. 必要環境

- macOS (Intel/Apple Silicon両対応)
- Python 3.9以上
- pip (Pythonパッケージマネージャー)
- Homebrew (推奨)

## 2. セットアップ手順

### 2.1 Homebrewのインストール (未インストールの場合)

Homebrewがインストールされていない場合は、下記コマンドでインストールします。

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2.2 Pythonのインストール (未インストールの場合)

Homebrewを使用してPythonをインストールします。

```bash
brew install python
```

インストール後、Pythonのバージョンを確認します。

```bash
python3 --version
```

Python 3.9以上であることを確認してください。

### 2.3 プロジェクトのセットアップ

1. Python仮想環境を作成し、有効化します

```bash
# プロジェクトフォルダに移動
cd lifeplan-simulator

# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate
```

2. 必要なPythonパッケージをインストールします

```bash
pip install -r requirements.txt
```

### 2.4 データベースの初期化

以下のコマンドでデータベースを初期化します。

```bash
python admin_tools.py init-db
```

### 2.5 管理者ユーザーの作成 (オプション)

以下のコマンドで管理者ユーザーを作成できます。

```bash
python admin_tools.py create-admin --username admin --email admin@example.com --password yourpassword
```

## 3. アプリの起動と停止

### 3.1 アプリケーションの起動

#### 通常版

1. 仮想環境が有効化されていることを確認します

```bash
# 仮想環境が有効になっていない場合
source venv/bin/activate
```

2. Flaskアプリケーションを起動します

```bash
python run.py
```

これにより、アプリケーションは `http://0.0.0.0:5000/` で起動します。
ローカルからは `http://localhost:5000/` でアクセスできます。

#### 簡易版（データベース不要）

データベース接続に問題がある場合は、インメモリデータ構造を使用した簡易版アプリケーションを使用できます。

```bash
python app_simple.py
```

簡易版アプリケーションは `http://0.0.0.0:8080/` で起動します。
ローカルからは `http://localhost:8080/` でアクセスできます。

### 3.2 アプリケーションの停止

ターミナルで `Ctrl+C` を押すと、アプリケーションは停止します。

## 4. ブラウザでのアクセス方法

- ローカルPCからは `http://localhost:5000/` でアクセスできます。
- 同じWi-Fi/LANネットワーク内の他の端末からは、MacのIPアドレスを使用してアクセスできます。
  (例: `http://192.168.1.123:5000/`)

```bash
# MacのIPアドレスを確認するコマンド
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## 5. アプリケーションの使い方

1. ブラウザからアプリケーションにアクセスします
2. 「アカウント登録」からユーザー登録を行います
3. ログイン後、「新規作成」ボタンからライフプランを作成します
4. 基本情報、収入情報、支出情報を入力して保存します
5. ライフイベント（結婚、出産など）を追加できます
6. シミュレーション結果を閲覧し、CSVやJSONでエクスポートできます

## 6. インターネット公開方法

インターネットへの公開方法については、`INTERNET_ACCESS.md`ファイルをご参照ください。

## 7. トラブルシューティング

- **ポート競合エラーが表示される場合**:
  `run.py` ファイルを編集して、ポート番号を変更します（例：5000 → 5001）

- **データベースエラーが表示される場合**:
  `python admin_tools.py init-db` コマンドを実行してデータベースを再初期化します

- **パッケージ関連のエラーが表示される場合**:
  `pip install --upgrade -r requirements.txt` を実行して依存パッケージを再インストールします

## 8. 注意事項

- このアプリケーションはローカル環境での使用を目的としています。
- インターネットへの公開は、ngrokやCloudflare Tunnelを使用した一時的な公開のみを想定しています。
- 実際の投資判断には、専門家のアドバイスを受けてください。