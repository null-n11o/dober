---
name: メモリーシステム再設計
description: ROADMAP.mdをタスク管理と統合し、decisions/への記録を必須化
type: project
---

# 決定: メモリーシステム再設計

日付: 2026-03-15

## 変更内容

### Before
```
MEMORY.md          → 軽量インデックス（ポインターのみ）
projects/dober.md  → 事業現在状態・タスク（更新が滞りがち）
ROADMAP.md         → フェーズ・スペック・意思決定ログ
daily/             → 作業ログ
```

### After
```
MEMORY.md          → 現状スナップショット（KPI・フェーズ・直近決定）+ ポインター
ROADMAP.md         → フェーズ構造 + タスク管理（毎セッション更新）
daily/             → セッション作業ログ
decisions/         → 重要な意思決定の詳細記録（必須）
```

## 変更の根拠

- `projects/dober.md` が機能しておらず更新が滞っていた
- タスク管理とロードマップは同じファイルで管理した方がコンテキストが保たれる
- 意思決定が `decisions/` に記録されるルールがなく、散逸していた
- MEMORY.md はポインターだけでなく現状スナップショットも持つべき

## 廃止ファイル

- `memory/projects/dober.md` → 廃止

## セッション手順

### 開始時
1. `memory/MEMORY.md` → 現状スナップショットを30秒で把握
2. `ROADMAP.md` → 今日のタスクを確認
3. 必要に応じて `memory/daily/` の直近ログを確認

### 終了時
1. `memory/daily/YYYY-MM-DD.md` に作業ログを追記
2. `ROADMAP.md` のタスクステータスを更新
3. `memory/MEMORY.md` のスナップショットを更新
4. 重要な意思決定があれば `memory/decisions/` にファイルを作成
