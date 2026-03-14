---
name: dober-analysis
description: Doberの投稿パフォーマンスを分析し、インサイトレポートを生成する。「今週のDoberのデータ分析をお願い」「Doberのレポートを出して」「Threads投稿の分析」「先月のDober振り返り」などで自動起動する。データ同期から分析レポート生成まで一気通貫で実行する。
---

# Dober データ分析スキル

ThreadsデータをNotionに同期し、投稿パフォーマンスの分析レポートを生成します。
分析スクリプトは `scripts/analyze_notion_data.py` にバンドルされています。

## 実行手順

### Step 1: 直近30日分のデータ同期

```bash
python3 .claude/skills/dober-analysis/scripts/sync_recent_30days.py
```

同期完了のログ（`✅ 同期完了`）を確認したら、**待たずにすぐStep 2へ進む**。

### Step 2: 分析レポート生成

```bash
python3 .claude/skills/dober-analysis/scripts/analyze_notion_data.py --days 7
```

レポートは `.claude/skills/dober-analysis/reports/YYYY-MM-DD_HHMM_dober_analysis.md` に自動保存される。

### Step 3: インサイトをレポートに追記して保存

スクリプト出力のデータをもとに、以下のセクションを `.claude/skills/dober-analysis/reports/YYYY-MM-DD_HHMM_dober_analysis.md` に追記：

```markdown
## インサイト分析

### 注目投稿の傾向
（高パフォーマンス投稿のテーマ・文体・フォーマットの共通点）

### エンゲージメント考察
（ライク率・リプライ率・週次トレンドから読み取れること）

### 次のアクション
（KPI目標 Threadsフォロワー5,000・メールリスト500 に向けた具体的な改善提案）

### KPIギャップ
| 指標 | 現在 | 目標 | ギャップ |
|------|------|------|---------|
| フォロワー | ? | 5,000 | ? |
| メールリスト | ? | 500 | ? |
```

## 参照コンテキスト

- KPI目標・事業背景: `businesses/dober/CONTEXT.md`
- 今四半期の優先事項: `management/strategy/okr.md`
