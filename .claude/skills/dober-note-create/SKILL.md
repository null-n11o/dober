---
name: dober-note-create
description: Doberのnote記事をキーワードリサーチからファイル保存まで一気通貫で作成する。「note記事を作って」「noteを書いて」「○○というテーマでnote記事を作りたい」「SEOを意識したnote記事を書いて」などで自動起動する。
---

# Dober note記事 一気通貫作成スキル

キーワードリサーチ → アウトライン生成 → リサーチ → 執筆 → タイトル生成を順番に実行し、note記事を完成させる。

## 前提

作業開始前に必ず参照:
- `assets/brand-guideline.md` — ボイス・トーン
- `CLAUDE.md` — コンテンツカテゴリ構造

## 実行フロー

```
Step 1: SEOキーワードリスト化（dober-article-keyword）
  ↓
Step 2: アウトライン生成（dober-article-outline）
  ↓
Step 3: セクションごとにループ
  ├── 3a: リサーチ（dober-article-search）
  └── 3b: 執筆（dober-article-write）
  ↓
Step 4: タイトル生成（dober-article-title）
  ↓
Step 5: ファイル保存
  ↓
Step 6: 完了レポート
```

---

## Step 1: SEOキーワードリスト化

`dober-article-keyword` スキルを実行する。

インプット:
- テーマ: ユーザーから受け取る
- ターゲット読者: CLAUDE.mdのプライマリーペルソナ（20〜30代男性）

出力されたキーワードリストをユーザーに確認し、**メインキーワードを1つ確定**してから次に進む。

---

## Step 2: アウトライン生成

`dober-article-outline` スキルを実行する。

インプット:
- テーマ: ユーザーから受け取ったテーマ
- 種別: `note`
- ターゲットキーワード: Step 1で確定したメインキーワード

アウトラインが生成されたら**必ずユーザーに確認**を取り、OKが出てから次に進む。

---

## Step 3: セクションごとのリサーチ → 執筆ループ

アウトラインの章数だけ以下を繰り返す。

### 3a: リサーチ（dober-article-search）

- アウトラインの「要リサーチ: なし」の章はスキップ
- それ以外は `dober-article-search` を実行

### 3b: 執筆（dober-article-write）

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

## Step 4: タイトル生成

全セクションの執筆完了後、`dober-article-title` を実行する。

- 種別: `note`
- インプット: 各章タイトル + 本文サマリー + メインキーワード

候補をユーザーに提示し、採用タイトルを確定する。

---

## Step 5: ファイル保存

```bash
mkdir -p dober/content/drafts/note/
OUTFILE="dober/content/drafts/note/$(date +%Y-%m-%d)_[テーマ略称].md"
```

保存形式:
```markdown
---
title: [確定タイトル]
main_keyword: [メインキーワード]
category: [Doberカテゴリ（例: 2-1）]
created: [YYYY-MM-DD]
status: draft
---

[全セクションの本文を結合]
```

---

## Step 6: 完了レポート

```
## note記事作成完了

- タイトル: [確定タイトル]
- メインキーワード: [キーワード]
- カテゴリ: [Doberカテゴリ]
- 総文字数: 約X,XXX字
- セクション数: X章
- 保存先: dober/content/drafts/note/YYYY-MM-DD_xxx.md

### 次のアクション
- [ ] noteに投稿（下書き保存 → 公開）
- [ ] 公開後URLをThreadsポストで告知する
- [ ] 記事内にメルマガ登録CTAを追加する（対応LMへの誘導）
```

## エラーハンドリング

| 状況 | 対処 |
|------|------|
| キーワードが見つからない | テーマをより一般的なワードに変えて dober-article-keyword を再実行 |
| アウトラインがユーザーにNG | 修正点を確認し、dober-article-outlineを再実行 |
| 特定章の執筆結果がNG | その章のみ dober-article-write を再実行（他章はやり直し不要） |
| リサーチ情報が不足 | dober-article-writeの「情報不足」フォールバックを適用（著名人事例・体験談で補完） |
