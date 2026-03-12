#!/usr/bin/env python3
"""
Threads Insights to Notion Sync Script

ThreadsのポストとインサイトをNotionデータベースに同期します。
- Notionの既存レコードを取得
- Threadsの全ポストとインサイトを取得
- 差分があれば更新、なければスキップ
- 新規ポストがあれば作成
"""

import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import time
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# 設定
# =============================================================================

THREADS_USER_ID = os.environ["THREADS_USER_ID"]
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]

NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_API_TOKEN = os.environ["NOTION_API_TOKEN"]

NOTION_VERSION = "2022-06-28"

# =============================================================================
# Notion API
# =============================================================================

def get_notion_headers() -> Dict[str, str]:
    """Notion APIのヘッダーを返す"""
    return {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


def get_all_notion_records() -> Dict[str, Dict]:
    """
    Notionデータベースから全レコードを取得

    Returns:
        Dict[thread_id, record]: Threads Post IDをキーとした辞書
    """
    print("📚 Notionから全レコードを取得中...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = get_notion_headers()

    all_records = {}
    has_more = True
    next_cursor = None

    while has_more:
        payload = {}
        if next_cursor:
            payload["start_cursor"] = next_cursor

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"❌ Notion API エラー: {response.status_code}")
            print(response.text)
            break

        data = response.json()

        for result in data.get("results", []):
            # Threads Post IDを取得（rich_textプロパティ）
            thread_id_prop = result.get("properties", {}).get("Threads Post ID", {})
            rich_text_array = thread_id_prop.get("rich_text", [])

            if rich_text_array:
                thread_id = rich_text_array[0].get("text", {}).get("content", "")

                if thread_id:
                    # 数値プロパティを取得
                    props = result.get("properties", {})

                    all_records[thread_id] = {
                        "page_id": result["id"],
                        "impressions": props.get("Impressions", {}).get("number", 0) or 0,
                        "likes": props.get("Likes", {}).get("number", 0) or 0,
                        "replies": props.get("Replies", {}).get("number", 0) or 0,
                        "reposts": props.get("Reposts", {}).get("number", 0) or 0,
                    }

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    print(f"✅ Notionレコード取得完了: {len(all_records)}件")
    return all_records


def update_notion_record(page_id: str, data: Dict) -> bool:
    """
    Notionレコードを更新

    Args:
        page_id: NotionページID
        data: 更新するデータ

    Returns:
        成功した場合True
    """
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = get_notion_headers()

    payload = {
        "properties": {
            "Impressions": {"number": data.get("impressions", 0)},
            "Likes": {"number": data.get("likes", 0)},
            "Replies": {"number": data.get("replies", 0)},
            "Reposts": {"number": data.get("reposts", 0)},
        }
    }

    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"❌ 更新エラー (Page ID: {page_id}): {response.status_code}")
        print(response.text)
        return False


def create_notion_record(data: Dict) -> bool:
    """
    Notionに新規レコードを作成

    Args:
        data: 作成するデータ

    Returns:
        成功した場合True
    """
    url = "https://api.notion.com/v1/pages"
    headers = get_notion_headers()

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": data.get("text", "")[:100] if data.get("text") else data["thread_id"]
                        }
                    }
                ]
            },
            "Threads Post ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": data["thread_id"]
                        }
                    }
                ]
            },
            "Content": {
                "rich_text": [
                    {
                        "text": {
                            "content": data.get("text", "")[:2000]  # Notion制限2000文字
                        }
                    }
                ]
            },
            "Posted Date": {
                "date": {
                    "start": data.get("timestamp", "")
                }
            },
            "Impressions": {"number": data.get("impressions", 0)},
            "Likes": {"number": data.get("likes", 0)},
            "Replies": {"number": data.get("replies", 0)},
            "Reposts": {"number": data.get("reposts", 0)},
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return True
    else:
        print(f"❌ 作成エラー (Thread ID: {data['thread_id']}): {response.status_code}")
        print(response.text)
        return False


# =============================================================================
# Threads API
# =============================================================================

def get_threads_posts() -> List[Dict]:
    """
    Threadsから全ポストを取得

    Returns:
        ポストのリスト
    """
    print("🧵 Threadsから全ポストを取得中...")

    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {
        "fields": "id,text,timestamp,permalink,media_type",
        "access_token": THREADS_ACCESS_TOKEN,
        "limit": 100
    }

    all_posts = []

    while url:
        response = requests.get(url, params=params if params else None)

        if response.status_code != 200:
            print(f"❌ Threads API エラー: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        posts = data.get("data", [])
        all_posts.extend(posts)

        # 次のページがあるか確認
        paging = data.get("paging", {})
        url = paging.get("next")
        params = None  # 次のURLには既にパラメータが含まれている

    print(f"✅ Threadsポスト取得完了: {len(all_posts)}件")
    return all_posts


def get_post_insights(thread_id: str) -> Dict[str, int]:
    """
    特定のポストのインサイトを取得

    Args:
        thread_id: Threads Post ID

    Returns:
        インサイトデータ (views, likes, replies, reposts)
    """
    url = f"https://graph.threads.net/v1.0/{thread_id}/insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes,shares",
        "access_token": THREADS_ACCESS_TOKEN
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"⚠️  インサイト取得エラー (Thread ID: {thread_id}): {response.status_code}")
        return {
            "impressions": 0,
            "likes": 0,
            "replies": 0,
            "reposts": 0
        }

    data = response.json()
    insights_data = data.get("data", [])

    def get_value(name: str) -> int:
        for metric in insights_data:
            if metric.get("name") == name:
                values = metric.get("values", [])
                if values:
                    return values[0].get("value", 0)
        return 0

    return {
        "impressions": get_value("views"),
        "likes": get_value("likes"),
        "replies": get_value("replies"),
        "reposts": get_value("reposts")
    }


# =============================================================================
# メイン処理
# =============================================================================

def sync_threads_to_notion():
    """
    ThreadsのデータをNotionに同期
    """
    print("=" * 60)
    print("🚀 Threads → Notion 同期開始")
    print("=" * 60)

    # 1. Notionから既存レコードを取得
    notion_records = get_all_notion_records()

    # 2. Threadsから全ポストを取得
    threads_posts = get_threads_posts()

    # 3. 各ポストを処理
    print(f"\n🔄 ポストを処理中...")

    updated_count = 0
    created_count = 0
    skipped_count = 0

    for i, post in enumerate(threads_posts, 1):
        thread_id = post["id"]
        print(f"\n[{i}/{len(threads_posts)}] Processing: {thread_id}")

        # インサイトを取得
        insights = get_post_insights(thread_id)

        # レート制限対策（1秒待機）
        time.sleep(1)

        # Notionに既存レコードがあるか確認
        if thread_id in notion_records:
            existing = notion_records[thread_id]

            # 差分があるか確認
            has_changes = (
                existing["impressions"] != insights["impressions"] or
                existing["likes"] != insights["likes"] or
                existing["replies"] != insights["replies"] or
                existing["reposts"] != insights["reposts"]
            )

            if has_changes:
                print(f"  📝 更新: impressions {existing['impressions']} → {insights['impressions']}")
                if update_notion_record(existing["page_id"], insights):
                    updated_count += 1
            else:
                print(f"  ⏭️  スキップ（変更なし）")
                skipped_count += 1
        else:
            # 新規作成
            print(f"  ✨ 新規作成")
            data = {
                "thread_id": thread_id,
                "text": post.get("text", ""),
                "timestamp": post.get("timestamp", ""),
                "permalink": post.get("permalink", ""),
                **insights
            }
            if create_notion_record(data):
                created_count += 1

    # 結果サマリー
    print("\n" + "=" * 60)
    print("✅ 同期完了")
    print("=" * 60)
    print(f"📊 総ポスト数: {len(threads_posts)}")
    print(f"📝 更新: {updated_count}件")
    print(f"✨ 新規作成: {created_count}件")
    print(f"⏭️  スキップ: {skipped_count}件")
    print("=" * 60)


if __name__ == "__main__":
    try:
        sync_threads_to_notion()
    except KeyboardInterrupt:
        print("\n\n⚠️  中断されました")
    except Exception as e:
        print(f"\n\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
