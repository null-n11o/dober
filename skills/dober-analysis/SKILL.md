---
name: dober-analysis
description: Doberの投稿パフォーマンスを分析し、インサイトレポートを生成する。「今週のDoberのデータ分析をお願い」「Doberのレポートを出して」「Threads投稿の分析」「先月のDober振り返り」などで自動起動する。データ同期から分析レポート生成まで一気通貫で実行する。
---

# Dober データ分析スキル

ThreadsデータをNotionに同期し、投稿パフォーマンスの分析レポートを生成します。
分析スクリプトは `scripts/analyze_notion_data.py` にバンドルされています。

## 実行手順

### Step 1: データ同期

最新のThreadsデータをNotionに反映します：

```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 businesses/dober/sync_threads_to_notion.py
```

### Step 2: 分析レポート生成

ユーザーの指定期間に応じてコマンドを選択：

**今週（直近7日）— デフォルト:**
```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 .claude/commands/dober-analysis/scripts/analyze_notion_data.py --days 7
```

**今月（直近30日）:**
```bash
cd /Users/nakanokentaro/develop/active/nakano && python3 .claude/commands/dober-analysis/scripts/analyze_notion_data.py --days 30
```

レポートは `businesses/dober/data-analysis/reports/YYYY-MM-DD_HHMM_dober_analysis.md` に自動保存されます。

### Step 3: インサイト提示

スクリプト出力のレポートを表示した後、以下の観点でコメントを追加：

1. **注目投稿**: 高パフォーマンス投稿の傾向（テーマ・文体・長さの共通点）
2. **エンゲージメント考察**: ライク率・リプライ率から読み取れること
3. **次のアクション**: KPI目標（Threadsフォロワー5,000・メールリスト1,000）に向けた具体的な改善提案

## 参照コンテキスト

- KPI目標・事業背景: `businesses/dober/CONTEXT.md`
- 今四半期の優先事項: `management/strategy/okr.md`
