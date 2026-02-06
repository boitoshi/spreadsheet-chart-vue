# ConoHa WING デプロイガイド

## 1. 前提条件
- ConoHa WINGアカウントの取得
- 独自ドメインの設定（任意）
- Node.js 18+ がローカルにインストール済み

## 2. ビルド手順

### 2.1 環境変数の設定
`.env.production` ファイルを編集し、Cloud RunのURLを設定：

```env
VITE_API_BASE_URL=https://portfolio-backend-xxx-an.a.run.app
```

### 2.2 本番ビルド実行
```bash
npm run build:production
```

ビルドが完了すると `dist/` フォルダに静的ファイルが生成されます。

## 3. ConoHa WING アップロード手順

### 3.1 ファイルマネージャーでアップロード
1. ConoHa WINGコントロールパネルにログイン
2. 「サイト管理」→「ファイルマネージャー」を開く
3. 対象ドメインの `public_html` フォルダを選択
4. `dist/` フォルダの中身を全てアップロード

### 3.2 FTP/SFTPでアップロード
```bash
# FTP設定例
ホスト: あなたのドメイン.com
ユーザー名: ConoHa WINGのユーザー名
パスワード: ConoHa WINGのパスワード
ポート: 21 (FTP) または 22 (SFTP)
```

## 4. 設定ファイル

### 4.1 .htaccess の設定
Vue Router使用時のSPAルーティング対応：

```apache
# Vue Router History Mode 対応
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

# キャッシュ設定
<IfModule mod_expires.c>
  ExpiresActive on
  
  # JavaScript and CSS
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  
  # Images
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType image/jpg "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/svg+xml "access plus 1 year"
  
  # Fonts
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType font/woff "access plus 1 year"
</IfModule>

# セキュリティヘッダー
<IfModule mod_headers.c>
  Header always set X-Frame-Options "SAMEORIGIN"
  Header always set X-Content-Type-Options "nosniff"
  Header always set X-XSS-Protection "1; mode=block"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
```

## 5. 確認手順

### 5.1 動作確認
1. ブラウザでサイトにアクセス
2. 開発者ツールでAPIリクエストを確認
3. 各機能が正常に動作することを確認

### 5.2 問題発生時の対処
- CORSエラー → バックエンドのCORS設定を確認
- 404エラー → .htaccess の設定を確認
- APIエラー → 環境変数の設定を確認

## 6. 更新手順

### 6.1 継続的デプロイ
1. コード変更
2. `npm run build:production`
3. `dist/` フォルダの内容をConoHa WINGにアップロード
4. ブラウザキャッシュをクリア

### 6.2 自動化（オプション）
FTPデプロイ用のスクリプトを作成可能：

```bash
#!/bin/bash
npm run build:production
rsync -avz --delete dist/ user@yourserver.com:/path/to/public_html/
```

## 7. 注意事項

- SSL証明書の設定を確認
- 独自ドメインの場合、DNS設定が必要
- ファイルサイズの上限に注意
- 定期的なバックアップを推奨