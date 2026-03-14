---
name: dober-data-sync
description: ThreadsのポストデータをNotionデータベースに同期する。「Doberのデータを更新」「Threadsの最新データを取得・同期」「Notionにデータを反映して」などで自動起動する。データ分析の前処理として必ず実行する。
---

# Dober データ同期スキル

ThreadsのポストとインサイトデータをNotionデータベースに同期します。

## 実行手順

以下のスクリプトを実行してください：

```bash
python3 skills/dober-data-sync/scripts/sync_threads_to_notion.py
```

## 完了後の報告

実行完了後、以下をサマリーとして報告してください：

- 処理した総ポスト数
- 更新件数・新規作成件数・スキップ件数
- エラーが発生した場合はその内容と対処法

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| 401 Unauthorized | アクセストークン期限切れ | Threads Developerでトークンを再発行 |
| 400 Bad Request | Notion APIバージョン不一致 | スクリプト内 NOTION_VERSION を確認 |
| タイムアウト | 投稿数が多い（400件超） | 正常。数分待つ |
