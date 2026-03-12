#!/usr/bin/env python3
"""
Dober Notion データ分析スクリプト

NotionのDoberデータベースからポストデータを取得し、
分析レポートを生成します。
"""

import os
import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import argparse
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# 設定
# =============================================================================

NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_API_TOKEN = os.environ["NOTION_API_TOKEN"]
NOTION_VERSION = "2022-06-28"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(SCRIPT_DIR, "reports")

# =============================================================================
# Notion データ取得
# =============================================================================

def get_notion_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }


def get_all_notion_records() -> List[Dict]:
    """Notionから全ポストレコードを取得"""
    print("📚 Notionからデータ取得中...")

    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = get_notion_headers()

    all_records = []
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
            props = result.get("properties", {})

            # 各プロパティを安全に取得
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
            if not thread_id:
                continue

            all_records.append({
                "thread_id": thread_id,
                "title": get_title("Title"),
                "content": get_rich_text("Content"),
                "posted_date": get_date("Posted Date"),
                "impressions": get_number("Impressions"),
                "likes": get_number("Likes"),
                "replies": get_number("Replies"),
                "reposts": get_number("Reposts"),
            })

        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")

    print(f"✅ {len(all_records)}件取得完了")
    return all_records


# =============================================================================
# 分析
# =============================================================================

def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        # ISO 8601形式 (例: 2026-03-01T10:00:00+00:00 or 2026-03-01)
        if "T" in date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def filter_by_days(records: List[Dict], days: int) -> List[Dict]:
    """指定日数以内の投稿にフィルタリング"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [r for r in records if parse_date(r["posted_date"]) and parse_date(r["posted_date"]) >= cutoff]


def calc_engagement_rate(impressions: int, likes: int, replies: int, reposts: int) -> float:
    if impressions == 0:
        return 0.0
    return round((likes + replies + reposts) / impressions * 100, 2)


def analyze(records: List[Dict], days_recent: int = 7) -> Dict:
    """データ分析を実行"""
    if not records:
        return {}

    # 日付でソート
    dated = [(r, parse_date(r["posted_date"])) for r in records]
    dated_valid = [(r, d) for r, d in dated if d is not None]
    dated_valid.sort(key=lambda x: x[1], reverse=True)

    all_posts = [r for r, _ in dated_valid]
    recent_posts = filter_by_days(records, days_recent)
    last_30 = filter_by_days(records, 30)

    def total(posts, key):
        return sum(p[key] for p in posts)

    def avg(posts, key):
        return round(total(posts, key) / len(posts), 1) if posts else 0

    # エンゲージメント率を各投稿に付与
    for r in records:
        r["engagement_rate"] = calc_engagement_rate(
            r["impressions"], r["likes"], r["replies"], r["reposts"]
        )

    # TOP投稿 (直近30日、インプレッション順)
    top_by_impressions = sorted(last_30, key=lambda x: x["impressions"], reverse=True)[:10]
    top_by_engagement = sorted(last_30, key=lambda x: x["engagement_rate"], reverse=True)[:5]

    # 週次トレンド (直近8週)
    weekly_trend = []
    now = datetime.now(timezone.utc)
    for week in range(8):
        week_end = now - timedelta(weeks=week)
        week_start = week_end - timedelta(weeks=1)
        week_posts = [
            r for r in records
            if parse_date(r["posted_date"]) and
               week_start <= parse_date(r["posted_date"]) < week_end
        ]
        if week_posts or week == 0:
            weekly_trend.append({
                "week_label": week_end.strftime("%m/%d"),
                "posts_count": len(week_posts),
                "impressions": total(week_posts, "impressions"),
                "likes": total(week_posts, "likes"),
                "avg_engagement": round(
                    sum(p["engagement_rate"] for p in week_posts) / len(week_posts), 2
                ) if week_posts else 0
            })

    return {
        "total_posts": len(records),
        "total_impressions": total(records, "impressions"),
        "total_likes": total(records, "likes"),
        "total_replies": total(records, "replies"),
        "total_reposts": total(records, "reposts"),
        "recent_posts_count": len(recent_posts),
        "recent_impressions": total(recent_posts, "impressions"),
        "recent_likes": total(recent_posts, "likes"),
        "avg_impressions_all": avg(records, "impressions"),
        "avg_impressions_recent": avg(recent_posts, "impressions"),
        "avg_engagement_rate": round(
            sum(r["engagement_rate"] for r in records) / len(records), 2
        ) if records else 0,
        "top_by_impressions": top_by_impressions,
        "top_by_engagement": top_by_engagement,
        "weekly_trend": weekly_trend,
        "days_recent": days_recent,
        "latest_post_date": dated_valid[0][1].strftime("%Y-%m-%d") if dated_valid else "N/A",
        "oldest_post_date": dated_valid[-1][1].strftime("%Y-%m-%d") if dated_valid else "N/A",
    }


# =============================================================================
# レポート生成
# =============================================================================

def generate_report(data: Dict, days_recent: int) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    report_date = datetime.now().strftime("%Y年%m月%d日")

    lines = []
    lines.append(f"# Dober データ分析レポート ({report_date})")
    lines.append("")

    # サマリー
    lines.append("## 全体サマリー")
    lines.append("")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 総投稿数 | {data['total_posts']:,}件 |")
    lines.append(f"| 総インプレッション | {data['total_impressions']:,} |")
    lines.append(f"| 総ライク | {data['total_likes']:,} |")
    lines.append(f"| 総リプライ | {data['total_replies']:,} |")
    lines.append(f"| 総リポスト | {data['total_reposts']:,} |")
    lines.append(f"| 平均インプレッション/投稿 | {data['avg_impressions_all']:,} |")
    lines.append(f"| 平均エンゲージメント率 | {data['avg_engagement_rate']}% |")
    lines.append(f"| データ期間 | {data['oldest_post_date']} 〜 {data['latest_post_date']} |")
    lines.append("")

    # 直近N日
    lines.append(f"## 直近{days_recent}日間のパフォーマンス")
    lines.append("")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 投稿数 | {data['recent_posts_count']}件 |")
    lines.append(f"| インプレッション合計 | {data['recent_impressions']:,} |")
    lines.append(f"| ライク合計 | {data['recent_likes']:,} |")
    lines.append(f"| 平均インプレッション/投稿 | {data['avg_impressions_recent']:,} |")
    lines.append("")

    # 週次トレンド
    lines.append("## 週次トレンド（直近8週）")
    lines.append("")
    lines.append("| 週末日 | 投稿数 | インプレッション | ライク | 平均エンゲージメント率 |")
    lines.append("|--------|--------|----------------|--------|----------------------|")
    for w in data["weekly_trend"]:
        lines.append(f"| {w['week_label']} | {w['posts_count']} | {w['impressions']:,} | {w['likes']:,} | {w['avg_engagement']}% |")
    lines.append("")

    # TOP投稿 by インプレッション
    lines.append("## TOP10投稿（インプレッション順・直近30日）")
    lines.append("")
    lines.append("| # | 投稿内容（先頭70字） | インプレ | ライク | リプライ | リポスト | エンゲ率 |")
    lines.append("|---|---------------------|---------|--------|---------|---------|---------|")
    for i, post in enumerate(data["top_by_impressions"], 1):
        title = (post["title"] or post["content"] or "（内容なし）")[:70].replace("|", "｜").replace("\n", " ")
        lines.append(
            f"| {i} | {title} | {post['impressions']:,} | {post['likes']:,} | "
            f"{post['replies']:,} | {post['reposts']:,} | {post['engagement_rate']}% |"
        )
    lines.append("")

    # TOP投稿 by エンゲージメント率
    lines.append("## TOP5投稿（エンゲージメント率順・直近30日）")
    lines.append("")
    lines.append("| # | 投稿内容（先頭70字） | エンゲ率 | インプレ | ライク |")
    lines.append("|---|---------------------|---------|---------|--------|")
    for i, post in enumerate(data["top_by_engagement"], 1):
        title = (post["title"] or post["content"] or "（内容なし）")[:70].replace("|", "｜").replace("\n", " ")
        lines.append(
            f"| {i} | {title} | {post['engagement_rate']}% | "
            f"{post['impressions']:,} | {post['likes']:,} |"
        )
    lines.append("")

    lines.append("---")
    lines.append(f"*生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


# =============================================================================
# メイン
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Dober Notionデータ分析")
    parser.add_argument("--days", type=int, default=7, help="直近N日を分析対象にする（デフォルト: 7）")
    parser.add_argument("--output", type=str, default="", help="出力ファイルパス（省略時は自動命名）")
    parser.add_argument("--no-save", action="store_true", help="ファイルに保存しない")
    args = parser.parse_args()

    # データ取得
    records = get_all_notion_records()
    if not records:
        print("❌ データが取得できませんでした")
        return

    # 分析
    print("🔍 データを分析中...")
    data = analyze(records, days_recent=args.days)

    # レポート生成
    report = generate_report(data, args.days)

    # 出力
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)

    # ファイル保存
    if not args.no_save:
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = args.output or os.path.join(
            REPORTS_DIR,
            f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_dober_analysis.md"
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n💾 レポートを保存しました: {filename}")


if __name__ == "__main__":
    main()
