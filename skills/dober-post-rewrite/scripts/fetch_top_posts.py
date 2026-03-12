#!/usr/bin/env python3
"""
Dober Top Posts Fetch Script

Notionデータベースからインプレッション3000以上のポストを抽出します。
リライト素材の選定に使用します。
"""

import os
import requests
import json
import argparse
from datetime import datetime, timezone
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


def fetch_top_posts(min_impressions: int = 3000) -> List[Dict]:
    """
    インプレッション閾値以上のポストをNotionから取得

    Args:
        min_impressions: 最低インプレッション数（デフォルト: 3000）

    Returns:
        ポストのリスト（インプレッション降順）
    """
    print(f"📚 Notionからインプレッション{min_impressions}以上のポストを取得中...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = get_notion_headers()

    # Notion APIのフィルタ: Impressions >= min_impressions かつ Contentが存在する
    payload = {
        "filter": {
            "and": [
                {
                    "property": "Impressions",
                    "number": {
                        "greater_than_or_equal_to": min_impressions
                    }
                },
                {
                    "property": "Content",
                    "rich_text": {
                        "is_not_empty": True
                    }
                }
            ]
        },
        "sorts": [
            {
                "property": "Impressions",
                "direction": "descending"
            }
        ]
    }

    all_posts = []
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"❌ Notion API エラー: {response.status_code}")
            print(response.text)
            break

        data = response.json()

        for result in data.get("results", []):
            props = result.get("properties", {})

            def get_rich_text(prop_name):
                arr = props.get(prop_name, {}).get("rich_text", [])
                return arr[0].get("text", {}).get("content", "") if arr else ""

            def get_title(prop_name):
                arr = props.get(prop_name, {}).get("title", [])
                return arr[0].get("text", {}).get("content", "") if arr else ""

            def get_number(prop_name):
                return props.get(prop_name, {}).get("number", 0) or 0

            def get_date(prop_name):
                date_obj = props.get(prop_name, {}).get("date", {})
                return date_obj.get("start", "") if date_obj else ""

            thread_id = get_rich_text("Threads Post ID")
            content = get_rich_text("Content")

            if not content:
                continue

            impressions = get_number("Impressions")
            likes = get_number("Likes")
            replies = get_number("Replies")
            reposts = get_number("Reposts")

            engagement_rate = round(
                (likes + replies + reposts) / impressions * 100, 2
            ) if impressions > 0 else 0.0

            all_posts.append({
                "thread_id": thread_id,
                "content": content,
                "posted_date": get_date("Posted Date"),
                "impressions": impressions,
                "likes": likes,
                "replies": replies,
                "reposts": reposts,
                "engagement_rate": engagement_rate,
            })

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    print(f"✅ {len(all_posts)}件のトップポストを取得完了")
    return all_posts


def display_posts(posts: List[Dict]) -> None:
    """ポスト一覧をコンソールに表示"""
    if not posts:
        print("⚠️  対象ポストが見つかりませんでした")
        return

    print("\n" + "=" * 70)
    print(f"📊 インプレッション上位ポスト ({len(posts)}件)")
    print("=" * 70)

    for i, post in enumerate(posts, 1):
        content_preview = post["content"][:60].replace("\n", " ")
        print(f"\n[{i}] インプレ: {post['impressions']:,} | エンゲージ: {post['engagement_rate']}%")
        print(f"    ライク: {post['likes']:,} | リプライ: {post['replies']:,} | リポスト: {post['reposts']:,}")
        print(f"    {content_preview}...")
        if post["posted_date"]:
            print(f"    投稿日: {post['posted_date'][:10]}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(description="インプレッション上位のDoberポストを取得")
    parser.add_argument(
        "--min-impressions", type=int, default=3000,
        help="最低インプレッション数（デフォルト: 3000）"
    )
    parser.add_argument(
        "--output", type=str, default="",
        help="JSONファイルの出力パス（省略時はコンソールのみ）"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="JSON形式でコンソール出力"
    )
    args = parser.parse_args()

    posts = fetch_top_posts(min_impressions=args.min_impressions)

    if args.json:
        print(json.dumps(posts, ensure_ascii=False, indent=2))
    else:
        display_posts(posts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSONを保存しました: {args.output}")

    return posts


if __name__ == "__main__":
    main()
