---
name: dober-lm-create
description: DoberのリードマグネットをアウトラインからNotionへの保存まで一気通貫で作成する。「LMを作って」「LM-Aを作りたい」「リードマグネットを作成して」「LM-B（資産1000万ロードマップ）を作って」などで自動起動する。
---

# Dober LM 一気通貫作成スキル

アウトライン生成 → リサーチ → 執筆 → タイトル生成を順番に実行し、LMを完成させる。

## 前提

作業開始前に必ず参照:
- `assets/brand-guideline.md` — ボイス・トーン
- `CLAUDE.md` — LMのID・名称・対応カテゴリ

## 実行フロー

```
Step 1: アウトライン生成（dober-article-outline）
  ↓
Step 2: セクションごとにループ
  ├── 2a: リサーチ（dober-article-search）
  └── 2b: 執筆（dober-article-write）
  ↓
Step 3: タイトル生成（dober-article-title）
  ↓
Step 4: ファイル保存
  ↓
Step 5: 完了レポート
```

---

## Step 1: アウトライン生成

`dober-article-outline` スキルを実行する。

インプット:
- テーマ: ユーザーから受け取る（例: 「男の総合値」「資産1000万ロードマップ」）
- 種別: `LM`
- ターゲットペルソナ: CLAUDE.mdの対象LMに対応するペルソナ

アウトラインが生成されたら**必ずユーザーに確認**を取り、OKが出てから次に進む。

---

## Step 2: セクションごとのリサーチ → 執筆ループ

アウトラインの章数だけ以下を繰り返す。

### 2a: リサーチ（dober-article-search）

- アウトラインの「要リサーチ: なし」の章はスキップ
- それ以外は `dober-article-search` を実行

### 2b: 執筆（dober-article-write）

- リサーチ結果（または「要リサーチ: なし」）と前章の末尾200字を渡して `dober-article-write` を実行
- 執筆結果をユーザーに見せ、必要に応じて修正してから次の章に進む

**ループの進め方:**
```
[導入] リサーチ → 執筆 → ユーザー確認
[第1章] リサーチ → 執筆 → ユーザー確認
[第2章] リサーチ → 執筆 → ユーザー確認
...
[終章] リサーチ → 執筆 → ユーザー確認
```

---

## Step 3: タイトル生成

全セクションの執筆完了後、`dober-article-title` を実行する。

- 種別: `LM`
- インプット: 各章タイトル + 本文サマリー

候補をユーザーに提示し、採用タイトルを確定する。

---

## Step 4: ファイル保存

```bash
mkdir -p dober/content/drafts/lm/
OUTFILE="dober/content/drafts/lm/$(date +%Y-%m-%d)_[LM-ID]_[タイトル略称].md"
```

保存形式:
```markdown
---
lm_id: [LM-A / LM-B / LM-C]
title: [確定タイトル]
created: [YYYY-MM-DD]
status: draft
---

[全セクションの本文を結合]
```

---

## Step 5: 完了レポート

```
## LM作成完了

- LM ID: [LM-X]
- タイトル: [確定タイトル]
- 総文字数: 約X,XXX字
- セクション数: X章
- 保存先: dober/content/drafts/lm/YYYY-MM-DD_[LM-ID]_xxx.md

### 次のアクション
- [ ] n8nのキーワードDMフローにこのLMのURLを設定する
- [ ] メルマガ登録LPにLMのダウンロードリンクを追加する
- [ ] 対応カテゴリのThreadsポストにLM誘導文を追加する
```

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| アウトラインがユーザーにNG | 修正点を確認し、dober-article-outlineを再実行 |
| 特定章の執筆結果がNG | その章のみ dober-article-write を再実行（他章はやり直し不要） |
| リサーチ情報が不足 | dober-article-writeの「情報不足」フォールバックを適用（著名人事例・体験談で補完） |
