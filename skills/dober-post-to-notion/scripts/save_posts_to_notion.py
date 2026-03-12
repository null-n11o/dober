#!/usr/bin/env python3
"""
Dober リライトポスト Notion保存スクリプト

リライトされたポスト（JSON形式）をNotionデータベースに保存します。
Statusプロパティを "Ready" に設定して登録します。

使用方法:
    python3 save_posts_to_notion.py --input posts.json
    echo '[{"content": "投稿内容"}]' | python3 save_posts_to_notion.py --stdin
"""

import os
import requests
import json
import argparse
import sys
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# 設定
# =============================================================================

NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_API_TOKEN = os.environ["NOTION_API_TOKEN"]
NOTION_VERSION = "2022-06-28"

# =============================================================================
# Notion API
# =============================================================================

def get_notion_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


def ensure_status_property() -> bool:
    """
    NotionデータベースにStatusプロパティが存在することを確認。
    存在しない場合は追加する。
    """
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"
    headers = get_notion_headers()

    # 現在のDB構造を確認
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ DB情報取得エラー: {response.status_code}")
        return False

    db_data = response.json()
    existing_props = db_data.get("properties", {})

    if "Status" in existing_props:
        print("✅ Statusプロパティは既に存在します")
        return True

    # Statusプロパティを追加
    print("📝 NotionDBにStatusプロパティを追加中...")
    patch_payload = {
        "properties": {
            "Status": {
                "select": {
                    "options": [
                        {"name": "Ready", "color": "green"},
                        {"name": "Draft", "color": "gray"},
                        {"name": "Posted", "color": "blue"},
                        {"name": "Archive", "color": "red"}
                    ]
                }
            },
            "Source Post ID": {
                "rich_text": {}
            }
        }
    }

    patch_response = requests.patch(url, headers=headers, json=patch_payload)
    if patch_response.status_code == 200:
        print("✅ Statusプロパティを追加しました")
        return True
    else:
        print(f"❌ プロパティ追加エラー: {patch_response.status_code}")
        print(patch_response.text)
        return False


def create_rewrite_post(post: Dict) -> bool:
    """
    リライトポストをNotionに新規作成

    Args:
        post: {
            "content": str,          # 投稿内容（必須）
            "source_post_id": str,   # 元ポストのThreads ID（任意）
            "category": str,         # カテゴリ（任意）
        }

    Returns:
        成功した場合True
    """
    url = "https://api.notion.com/v1/pages"
    headers = get_notion_headers()

    content = post.get("content", "")
    title = content[:50].replace("\n", " ") + "..." if len(content) > 50 else content

    properties = {
        "Title": {
            "title": [
                {"text": {"content": title}}
            ]
        },
        "Content": {
            "rich_text": [
                {"text": {"content": content[:2000]}}
            ]
        },
        "Status": {
            "select": {"name": "Ready"}
        }
    }

    # 元ポストIDがあれば記録
    source_id = post.get("source_post_id", "")
    if source_id:
        properties["Source Post ID"] = {
            "rich_text": [
                {"text": {"content": source_id}}
            ]
        }

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"❌ 作成エラー: {response.status_code}")
        print(response.text)
        return False


def save_posts_to_notion(posts: List[Dict]) -> Dict[str, int]:
    """
    複数のリライトポストをNotionに保存

    Args:
        posts: ポストのリスト

    Returns:
        {"success": int, "failed": int}
    """
    print(f"\n🚀 {len(posts)}件のポストをNotionに保存開始...")

    success_count = 0
    failed_count = 0

    for i, post in enumerate(posts, 1):
        content_preview = post.get("content", "")[:50].replace("\n", " ")
        print(f"[{i}/{len(posts)}] 保存中: {content_preview}...")

        if create_rewrite_post(post):
            success_count += 1
            print(f"  ✅ 保存完了")
        else:
            failed_count += 1
            print(f"  ❌ 保存失敗")

    return {"success": success_count, "failed": failed_count}


def main():
    parser = argparse.ArgumentParser(description="リライトポストをNotionに保存")
    parser.add_argument(
        "--input", type=str, default="",
        help="入力JSONファイルパス"
    )
    parser.add_argument(
        "--stdin", action="store_true",
        help="標準入力からJSONを読み込む"
    )
    parser.add_argument(
        "--skip-setup", action="store_true",
        help="Statusプロパティの確認をスキップ"
    )
    args = parser.parse_args()

    # Statusプロパティの確認・追加
    if not args.skip_setup:
        if not ensure_status_property():
            print("⚠️  Statusプロパティの確認に失敗しましたが、続行します")

    # ポストデータの読み込み
    posts = []

    if args.stdin:
        raw = sys.stdin.read()
        posts = json.loads(raw)
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        print("❌ --input または --stdin を指定してください")
        sys.exit(1)

    if not posts:
        print("⚠️  保存するポストがありません")
        sys.exit(0)

    # 保存実行
    result = save_posts_to_notion(posts)

    # 結果表示
    print("\n" + "=" * 50)
    print("✅ 保存完了")
    print("=" * 50)
    print(f"成功: {result['success']}件")
    print(f"失敗: {result['failed']}件")
    print("=" * 50)


if __name__ == "__main__":
    main()
