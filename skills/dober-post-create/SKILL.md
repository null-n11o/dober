---
name: dober-post-create
description: Doberの今月分のポストを一気通貫で作成しNotionに登録する。「今月のDoberのポストを作成して」「Doberの投稿を30本作って」「今月のThreadsポストを用意して」「Doberのポストキューを作って」などで自動起動する。
---

# Dober ポスト一括作成スキル

トップポスト取得 → リライト生成 → Notion登録を一気通貫で実行します。
「今月のDoberのポストを作成して」で30件のポストがNotionにReadyステータスで登録されます。

## 前提

作業開始前に必ず確認:
- `businesses/dober/CONTEXT.md` — ブランド定義・KPI

## 実行フロー

```
Step 1: データ同期（最新インサイトをNotionに反映）
  ↓
Step 2: トップポスト取得（3000インプ以上）
  ↓
Step 3: リライトポスト生成（30本）
  ↓
Step 4: Notionへ一括登録（Readyステータス）
  ↓
Step 5: 完了レポート
```

---

## Step 1: データ同期（任意）

直近データを反映したい場合は先にデータ同期を実行:

```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 businesses/dober/sync_threads_to_notion.py
```

> スキップしてよいケース: 直近1週間以内にデータ同期済みの場合

---

## Step 2: トップポスト取得

```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 businesses/dober/fetch_top_posts.py --min-impressions 3000 --json
```

取得結果を分析して以下を把握する:
- 総取得数・カテゴリ分布
- 最高インプレッション数・最高エンゲージメント率
- 共通する成功パターン（文体・構成・フック手法）

---

## Step 3: リライトポスト生成

`/dober-post-rewrite` スキルの生成ルールに従い、30本のポストを生成する。

**生成方針（30本の構成目安）:**
| カテゴリ | 本数 |
|---------|------|
| 1. 精神・規律（喝/習慣化/ドーパミン） | 8本 |
| 2. 社交・恋愛（女性心理/アプリ/LTR） | 8本 |
| 3. 経済・事業（資本主義/投資/事業） | 7本 |
| 4. 知力・OS（学習/AI/自己分析） | 4本 |
| 5. 身体能力（筋トレ/食事） | 3本 |

**リライトの優先順位:**
1. インプレッション上位5本 → 各2〜3バリエーション
2. エンゲージメント率上位5本 → 各1〜2バリエーション
3. 残りはカテゴリバランスを考慮して選択

**出力JSON（後工程で使用）:**
```json
[
  {
    "content": "投稿本文（100〜300文字）",
    "source_post_id": "元のThreads Post ID",
    "category": "1-1"
  }
]
```

ファイルに保存:
```bash
mkdir -p /Users/nakanokentaro/develop/active/nakano/businesses/dober/content/drafts/
OUTFILE="/Users/nakanokentaro/develop/active/nakano/businesses/dober/content/drafts/$(date +%Y-%m)_rewrite_posts.json"
# → 生成したJSONをこのパスに書き込む
```

---

## Step 4: Notionへ一括登録

```bash
cd /Users/nakanokentaro/develop/active/nakano && \
  python3 businesses/dober/save_posts_to_notion.py \
    --input businesses/dober/content/drafts/$(date +%Y-%m)_rewrite_posts.json
```

---

## Step 5: 完了レポート

以下の形式でレポートを出力する:

```
## 今月のDober ポスト作成完了

### 生成サマリー
- 元にしたトップポスト: X本（インプレッション3000以上）
- 生成ポスト数: 30本
- Notion登録: 成功X本 / 失敗X本

### カテゴリ別内訳
| カテゴリ | 本数 |
|---------|------|
| 精神・規律 | X本 |
| 社交・恋愛 | X本 |
| 経済・事業 | X本 |
| 知力・OS | X本 |
| 身体能力 | X本 |

### トップポストの成功パターン（観察）
- [パターン1]
- [パターン2]

### 次のアクション
- Notionの「Ready」ポストをn8n投稿スケジュールに組み込む
- LM誘導ポストは週1〜2本のペースで配置推奨
```

---

## エラー時の対処

| 状況 | 対処 |
|------|------|
| トップポストが0件 | まず `/dober-data-sync` を実行してデータ同期 |
| Notion登録が全て失敗 | APIトークンを確認。`save_posts_to_notion.py` 内 `NOTION_API_TOKEN` をチェック |
| 生成ポストが30本に届かない | `--min-impressions 2000` に閾値を下げて再実行 |
