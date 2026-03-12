---
name: dober-post-to-notion
description: リライト済みのDoberポストをNotionデータベースにReadyステータスで登録する。「リライトポストをNotionに入れて」「ドラフトをNotionに登録して」「ポストキューをセットして」などで自動起動する。
---

# Dober ポスト → Notion登録スキル

リライト済みのポスト（JSONファイル）をNotionデータベースに「Ready」ステータスで一括登録します。

## 前提

- Notionデータベース ID: `21a5aab73db480daa40fed80775f78f8`
- 初回実行時はStatusプロパティをDBに自動追加します（スクリプトが自動処理）

## 実行手順

### Step 1: 入力ファイルの確認

登録対象のJSONファイルを確認する:

```bash
ls -la /Users/nakanokentaro/develop/active/nakano/businesses/dober/content/drafts/
```

ファイルが見当たらない場合は `/dober-post-rewrite` を先に実行してください。

### Step 2: Notionへの一括登録

JSONファイルを指定してスクリプトを実行:

```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 businesses/dober/save_posts_to_notion.py --input [JSONファイルパス]
```

**最新のドラフトファイルを自動指定する場合:**
```bash
cd /Users/nakanokentaro/develop/active/nakano && \
  LATEST=$(ls -t businesses/dober/content/drafts/*_rewrite_posts.json 2>/dev/null | head -1) && \
  if [ -n "$LATEST" ]; then \
    python3 businesses/dober/save_posts_to_notion.py --input "$LATEST"; \
  else \
    echo "ドラフトファイルが見つかりません。先に /dober-post-rewrite を実行してください。"; \
  fi
```

### Step 3: 完了報告

実行結果を報告する:
- Notionに登録したポスト数（成功・失敗）
- 登録したポストのStatusが「Ready」であること
- 失敗した場合はエラー内容と対処法

## Notion DBプロパティ構成

登録後のNotionレコード構成:

| プロパティ | 値 |
|-----------|-----|
| Title | 投稿内容の先頭50文字 |
| Content | 投稿本文（最大2000文字） |
| Status | **Ready** |
| Source Post ID | 元ポストのThreads ID（リライト元がある場合） |

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `400 Bad Request` on Status property | DBにStatusプロパティが未追加 | `--skip-setup` を外して再実行（自動追加される） |
| `401 Unauthorized` | Notion APIトークン期限切れ | スクリプト内 `NOTION_API_TOKEN` を更新 |
| `404 Not Found` | DB IDが不正 | `NOTION_DATABASE_ID` を確認 |
| ファイルが見つからない | パスが間違い | `ls businesses/dober/content/drafts/` で確認 |
