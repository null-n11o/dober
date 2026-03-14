#!/usr/bin/env python3
import os, requests, time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

THREADS_USER_ID = os.environ["THREADS_USER_ID"]
THREADS_ACCESS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_API_TOKEN = os.environ["NOTION_API_TOKEN"]
NOTION_VERSION = "2022-06-28"
DAYS = 30
CUTOFF = datetime.now(timezone.utc) - timedelta(days=DAYS)

def notion_headers():
    return {"Authorization": f"Bearer {NOTION_API_TOKEN}", "Content-Type": "application/json", "Notion-Version": NOTION_VERSION}

def get_notion_records():
    print("📚 Notionレコード取得中...")
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    records = {}
    cursor = None
    while True:
        payload = {"start_cursor": cursor} if cursor else {}
        r = requests.post(url, headers=notion_headers(), json=payload)
        data = r.json()
        for result in data.get("results", []):
            tid_prop = result["properties"].get("Threads Post ID", {}).get("rich_text", [])
            if tid_prop:
                tid = tid_prop[0]["text"]["content"]
                props = result["properties"]
                content_arr = props.get("Content", {}).get("rich_text", [])
                content = content_arr[0]["text"]["content"] if content_arr else ""
                records[tid] = {
                    "page_id": result["id"],
                    "impressions": props.get("Impressions", {}).get("number", 0) or 0,
                    "likes": props.get("Likes", {}).get("number", 0) or 0,
                    "replies": props.get("Replies", {}).get("number", 0) or 0,
                    "reposts": props.get("Reposts", {}).get("number", 0) or 0,
                    "content": content,
                    "post_count": props.get("Post Count", {}).get("number", 0) or 0,
                }
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    print(f"✅ {len(records)}件取得")
    return records

def get_recent_posts():
    print(f"🧵 直近{DAYS}日のポスト取得中...")
    url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    params = {"fields": "id,text,timestamp,permalink,media_type", "access_token": THREADS_ACCESS_TOKEN, "limit": 100}
    posts = []
    while url:
        r = requests.get(url, params=params if params else None)
        data = r.json()
        for post in data.get("data", []):
            ts = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
            if ts < CUTOFF:
                print(f"  カットオフ到達: {ts.date()} — 取得終了")
                return posts
            posts.append(post)
        paging = data.get("paging", {})
        url = paging.get("next")
        params = None
    print(f"✅ {len(posts)}件取得")
    return posts

def get_insights(tid):
    r = requests.get(f"https://graph.threads.net/v1.0/{tid}/insights",
        params={"metric": "views,likes,replies,reposts,quotes,shares", "access_token": THREADS_ACCESS_TOKEN})
    if r.status_code != 200:
        return {"impressions": 0, "likes": 0, "replies": 0, "reposts": 0}
    def val(name):
        for m in r.json().get("data", []):
            if m["name"] == name:
                v = m.get("values", [])
                return v[0]["value"] if v else 0
        return 0
    return {"impressions": val("views"), "likes": val("likes"), "replies": val("replies"), "reposts": val("reposts")}

def update_notion(page_id, data):
    r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=notion_headers(),
        json={"properties": {"Impressions": {"number": data["impressions"]}, "Likes": {"number": data["likes"]},
            "Replies": {"number": data["replies"]}, "Reposts": {"number": data["reposts"]}}})
    return r.status_code == 200

def update_post_count(page_id, count):
    r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=notion_headers(),
        json={"properties": {"Post Count": {"number": count}}})
    return r.status_code == 200

def recalculate_post_counts(notion_records):
    print("\n🔢 Post Count を再計算中...")
    groups = defaultdict(list)
    no_content = []
    for record in notion_records.values():
        content = record.get("content", "").strip()
        if content:
            groups[content].append(record)
        else:
            no_content.append(record)
    updated = 0
    for content, records in groups.items():
        count = len(records)
        for record in records:
            if record.get("post_count", 0) != count:
                if update_post_count(record["page_id"], count):
                    updated += 1
                time.sleep(0.3)
    for record in no_content:
        if record.get("post_count", 0) != 1:
            if update_post_count(record["page_id"], 1):
                updated += 1
            time.sleep(0.3)
    print(f"✅ Post Count 更新: {updated}件")

def create_notion(data):
    r = requests.post("https://api.notion.com/v1/pages", headers=notion_headers(), json={
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {"title": [{"text": {"content": (data.get("text") or data["id"])[:100]}}]},
            "Threads Post ID": {"rich_text": [{"text": {"content": data["id"]}}]},
            "Content": {"rich_text": [{"text": {"content": (data.get("text") or "")[:2000]}}]},
            "Posted Date": {"date": {"start": data.get("timestamp", "")}},
            "Impressions": {"number": data["impressions"]}, "Likes": {"number": data["likes"]},
            "Replies": {"number": data["replies"]}, "Reposts": {"number": data["reposts"]},
        }})
    return r.json().get("id") if r.status_code == 200 else None

notion_records = get_notion_records()
posts = get_recent_posts()
updated = created = skipped = 0

for i, post in enumerate(posts, 1):
    tid = post["id"]
    print(f"[{i}/{len(posts)}] {tid[:20]}...", end=" ")
    insights = get_insights(tid)
    time.sleep(1)
    if tid in notion_records:
        ex = notion_records[tid]
        if any(ex[k] != insights[k] for k in insights):
            ok = update_notion(ex["page_id"], insights)
            print(f"更新 impressions:{insights['impressions']}" if ok else "更新失敗")
            if ok: updated += 1
        else:
            print("スキップ")
            skipped += 1
    else:
        data = {**post, **insights}
        page_id = create_notion(data)
        print(f"新規作成" if page_id else "作成失敗")
        if page_id:
            created += 1
            notion_records[tid] = {
                "page_id": page_id,
                "content": post.get("text", ""),
                "post_count": 0,
                **insights
            }

recalculate_post_counts(notion_records)
print(f"\n✅ 同期完了 — 更新:{updated} 新規:{created} スキップ:{skipped}")
