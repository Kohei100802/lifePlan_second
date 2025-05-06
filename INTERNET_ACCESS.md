# インターネット公開手順

このドキュメントでは、ローカルで実行しているライフプランシミュレーターをインターネット上に一時的に公開する手順を説明します。これにより、外出先のiPhoneなどのモバイルデバイスからアクセスすることが可能になります。

## 1. ngrokを使用した公開方法

ngrokは、ローカルで実行しているサービスを安全にインターネット上に公開するためのツールです。

### 1.1 ngrokのインストール

#### Homebrewを使用したインストール

```bash
brew install ngrok
```

#### 直接ダウンロードしてインストール

1. [ngrokの公式サイト](https://ngrok.com/download)からダウンロード
2. ダウンロードしたzipファイルを展開
3. 必要に応じてPATHを通す

### 1.2 ngrokアカウントの作成と認証

1. [ngrokの公式サイト](https://ngrok.com/)でアカウントを作成
2. ダッシュボードから認証トークンを取得
3. 以下のコマンドで認証を設定

```bash
ngrok config add-authtoken <あなたの認証トークン>
```

### 1.3 アプリの公開

1. ライフプランシミュレーターを起動 

#### 通常版の場合
```bash
# 別のターミナルで
source venv/bin/activate
python run.py
```

#### 簡易版の場合（データベース不要）
```bash
# 別のターミナルで
python app_simple.py
```

2. ngrokを使用してFlaskアプリを公開

#### 通常版の場合（ポート5000）
```bash
ngrok http 5000
```

#### 簡易版の場合（ポート8080）
```bash
ngrok http 8080
```

3. ngrokが生成したURLを確認 (例: `https://abcd1234.ngrok.io`)

このURLを使って、インターネット上の任意のデバイスからアプリにアクセスできます。

### 1.4 追加のセキュリティ設定（オプション）

ngrokのBasic認証を設定してパスワード保護を追加できます：

```bash
ngrok http 5000 --basic-auth="username:password"
```

## 2. Cloudflare Tunnelを使用した公開方法

Cloudflare Tunnelは、より安全かつ安定したトンネリングサービスを提供します。

### 2.1 Cloudflare Tunnelのインストール

#### Homebrewを使用したインストール

```bash
brew install cloudflared
```

#### 直接ダウンロードしてインストール

1. [Cloudflare Tunnelの公式サイト](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation)からダウンロード
2. インストール手順に従ってセットアップ

### 2.2 Cloudflareアカウントの作成とログイン

1. [Cloudflareの公式サイト](https://dash.cloudflare.com/sign-up)でアカウントを作成
2. 以下のコマンドでCloudflareにログイン

```bash
cloudflared login
```

3. ブラウザが開き、認証を完了します

### 2.3 一時的なトンネルの作成と公開

1. ライフプランシミュレーターを起動

#### 通常版の場合
```bash
# 別のターミナルで
source venv/bin/activate
python run.py
```

#### 簡易版の場合（データベース不要）
```bash
# 別のターミナルで
python app_simple.py
```

2. Cloudflare Tunnelを使用してFlaskアプリを公開

#### 通常版の場合（ポート5000）
```bash
cloudflared tunnel --url http://localhost:5000
```

#### 簡易版の場合（ポート8080）
```bash
cloudflared tunnel --url http://localhost:8080
```

3. 生成されたURLを確認 (例: `https://abcd-efgh-ijkl-mnop.trycloudflare.com`)

このURLを使って、インターネット上の任意のデバイスからアプリにアクセスできます。

### 2.4 永続的なトンネルの設定（オプション）

より恒久的なソリューションが必要な場合は、永続的なトンネルを設定できます：

```bash
# トンネルの作成
cloudflared tunnel create lifeplan-simulator

# トンネルの設定ファイルを作成
cat << EOF > ~/.cloudflared/config.yml
tunnel: <トンネルID>
credentials-file: /Users/<username>/.cloudflared/<トンネルID>.json
ingress:
  - hostname: lifeplan.example.com
    service: http://localhost:5000
  - service: http_status:404
EOF

# トンネルを実行
cloudflared tunnel run lifeplan-simulator
```

## 3. インターネット公開時の注意事項

1. **セキュリティ**:
   - 公開URLは第三者に知られないよう注意してください
   - 可能な限り認証を設定してください
   - 機密情報や実際の個人情報は入力しないでください

2. **一時的な使用**:
   - これらの方法は一時的な公開を目的としています
   - 長期的な公開が必要な場合は、適切なホスティングサービスを検討してください

3. **帯域幅と使用制限**:
   - 無料プランには使用制限があります
   - 多数のユーザーや大量のデータ転送には適していません

4. **接続の安定性**:
   - 公開中はMacをスリープ状態にしないでください
   - インターネット接続が安定していることを確認してください

5. **IPアドレスの変更**:
   - 自宅のIPアドレスが変更された場合、新しいトンネルを作成する必要があります

## 4. 公開URLの共有方法

1. **安全な共有方法**:
   - SMS、Eメール、暗号化されたメッセージアプリを使用
   - 可能であれば、Basic認証のユーザー名とパスワードは別の経路で共有

2. **QRコードの生成**:
   - 以下のコマンドでQRコードを生成し、モバイルデバイスで簡単にアクセス

```bash
# qrencode のインストール
brew install qrencode

# URLのQRコードを生成
qrencode -t ANSI "https://your-ngrok-url.ngrok.io"
```

または、オンラインのQRコード生成サービスを使用することもできます。

## 5. 公開の終了

1. **ngrokの場合**:
   - ターミナルで `Ctrl+C` を押してngrokプロセスを終了

2. **Cloudflare Tunnelの場合**:
   - 一時的なトンネルは `Ctrl+C` を押して終了
   - 永続的なトンネルは `cloudflared tunnel delete <トンネル名>` で削除

## 6. トラブルシューティング

- **接続エラーが発生する場合**:
  - アプリケーションが `0.0.0.0` でリッスンしていることを確認
  - ファイアウォールの設定を確認
  - ポート競合がないことを確認

- **ngrokが "ERR_NGROK_..." エラーを表示する場合**:
  - 認証トークンが正しく設定されているか確認
  - 無料プランの使用制限に達していないか確認

- **Cloudflare Tunnelが接続できない場合**:
  - Cloudflareアカウントへの再ログインを試行
  - `cloudflared update` でCloudflaredを最新バージョンに更新