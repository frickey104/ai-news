#!/usr/bin/env python3
"""
AI ニュース収集スクリプト
毎日実行して最新のAI関連情報をMarkdownに変換する

情報源:
  - RSS: TechCrunch, VentureBeat, The Verge
  - Reddit: r/MachineLearning, r/LocalLLaMA
  - HackerNews: トップ記事のAIキーワードフィルタ
  - YouTube: チャンネルRSS（APIキー不要）
"""

import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import feedparser
import requests

# ===== 設定 =====

JST = timezone(timedelta(hours=9))
NOW = datetime.now(JST)
YEAR = NOW.year
DATE_STR = NOW.strftime("%Y-%m-%d")
PERIOD_START = (NOW - timedelta(days=1)).strftime("%Y年%-m月%-d日")
PERIOD_END = NOW.strftime("%Y年%-m月%-d日")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
DAILY_DIR = os.path.join(DOCS_DIR, "daily")
BASE_PATH = ""  # VitePressのbaseが/cc-company/のため内部リンクはルート相対でOK

HEADERS = {
    "User-Agent": "AI-News-Bot/1.0 (github.com/Shin-sibainu/cc-company)"
}

# ===== 情報源の設定 =====

RSS_SOURCES = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "max": 4,
    },
    {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/category/ai/feed/",
        "max": 3,
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "max": 3,
    },
]

REDDIT_SOURCES = [
    {"sub": "MachineLearning", "limit": 4},
    {"sub": "LocalLLaMA", "limit": 4},
]

HN_KEYWORDS = [
    "AI", "LLM", "GPT", "Claude", "Gemini", "OpenAI", "Anthropic",
    "DeepSeek", "machine learning", "neural", "language model",
    "transformer", "diffusion", "Mistral", "llama", "AGI",
]

YOUTUBE_CHANNELS = [
    {"name": "Matt Wolfe",        "channel_id": "UCfj2Q3-X0HN-BoBByd5aNNA"},
    {"name": "AI Explained",      "channel_id": "UCNJ1Ymd5yFuUPtn21xtRbbw"},
    {"name": "Two Minute Papers", "channel_id": "UCbfYPyITQ-7l4upoX8nvctg"},
]


# ===== ユーティリティ =====

def clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return " ".join(text.split())


def truncate(text: str, max_len: int = 200) -> str:
    text = clean_html(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def parse_date(entry) -> str:
    for attr in ("published", "updated"):
        val = getattr(entry, attr, None)
        if val and len(val) >= 10:
            return val[:10]
    return ""


def extract_keywords(titles: list) -> list:
    KNOWN = [
        "GPT-5", "GPT-4o", "GPT-4", "ChatGPT", "o3", "o1",
        "Claude", "Gemini", "Llama", "Mistral", "DeepSeek", "Grok",
        "OpenAI", "Anthropic", "Google", "Meta", "Microsoft", "Apple",
        "AGI", "LLM", "RAG", "Agent", "Reasoning", "Multimodal",
        "Sora", "Midjourney", "DALL-E", "Stable Diffusion",
        "Copilot", "Perplexity", "Cursor", "Vibe coding",
    ]
    from collections import Counter
    text = " ".join(titles)
    counts = Counter()
    for kw in KNOWN:
        n = text.lower().count(kw.lower())
        if n > 0:
            counts[kw] = n
    return [kw for kw, _ in counts.most_common(12)]


def translate_with_claude(items: list) -> list:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return items
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        payload = [
            {"i": i, "title": item.get("title", ""), "summary": item.get("summary", "")}
            for i, item in enumerate(items)
            if item.get("title")
        ]
        if not payload:
            return items
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": (
                    "以下のAIニュース記事リストのtitleとsummaryを自然な日本語に翻訳してください。"
                    "summaryが空の場合は空のままにしてください。"
                    "同じJSON配列形式のみ返してください。\n\n"
                    + json.dumps(payload[:20], ensure_ascii=False)
                ),
            }],
        )
        translated = json.loads(message.content[0].text)
        result = list(items)
        for t in translated:
            idx = t.get("i")
            if idx is not None and 0 <= idx < len(result):
                result[idx] = dict(result[idx])
                result[idx]["title"] = t.get("title", result[idx]["title"])
                if t.get("summary"):
                    result[idx]["summary"] = t["summary"]
        print(f"  翻訳完了: {len(translated)}件")
        return result
    except Exception as e:
        print(f"  翻訳スキップ: {e}")
        return items


# ===== データ収集 =====

def fetch_rss() -> list:
    items = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[: source["max"]]:
                summary = truncate(
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                )
                items.append(
                    {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": source["name"],
                        "summary": summary,
                        "date": parse_date(entry),
                    }
                )
            print(f"  RSS [{source['name']}]: {min(len(feed.entries), source['max'])}件")
        except Exception as e:
            print(f"  RSS [{source['name']}] エラー: {e}")
    return items


def fetch_reddit() -> list:
    items = []
    for r in REDDIT_SOURCES:
        try:
            url = f"https://www.reddit.com/r/{r['sub']}/top.json?limit={r['limit']}&t=day"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"  Reddit [r/{r['sub']}] ステータス: {resp.status_code}")
                continue
            posts = resp.json()["data"]["children"]
            for post in posts:
                d = post["data"]
                items.append(
                    {
                        "title": d["title"],
                        "url": f"https://reddit.com{d['permalink']}",
                        "sub": r["sub"],
                        "score": d["score"],
                        "comments": d["num_comments"],
                    }
                )
            print(f"  Reddit [r/{r['sub']}]: {len(posts)}件")
        except Exception as e:
            print(f"  Reddit [r/{r['sub']}] エラー: {e}")
    return items


def fetch_hackernews() -> list:
    items = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10
        )
        story_ids = resp.json()[:150]
        count = 0
        for sid in story_ids:
            if count >= 5:
                break
            try:
                story = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=5,
                ).json()
                title = story.get("title", "")
                if any(kw.lower() in title.lower() for kw in HN_KEYWORDS):
                    items.append(
                        {
                            "title": title,
                            "url": story.get(
                                "url",
                                f"https://news.ycombinator.com/item?id={sid}",
                            ),
                            "score": story.get("score", 0),
                            "comments": story.get("descendants", 0),
                            "hn_url": f"https://news.ycombinator.com/item?id={sid}",
                        }
                    )
                    count += 1
            except Exception:
                pass
        print(f"  HackerNews: {len(items)}件")
    except Exception as e:
        print(f"  HackerNews エラー: {e}")
    return items


def fetch_youtube() -> list:
    items = []
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "media": "http://search.yahoo.com/mrss/",
        "yt": "http://www.youtube.com/xml/schemas/2015",
    }
    for ch in YOUTUBE_CHANNELS:
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['channel_id']}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"  YouTube [{ch['name']}] ステータス: {resp.status_code}")
                continue
            root = ET.fromstring(resp.content)
            entries = root.findall("atom:entry", ns)
            fetched = 0
            for entry in entries[:2]:
                title_el = entry.find("atom:title", ns)
                link_el = entry.find("atom:link", ns)
                published_el = entry.find("atom:published", ns)
                desc_el = entry.find(".//media:description", ns)
                if title_el is not None and link_el is not None:
                    items.append(
                        {
                            "title": title_el.text or "",
                            "url": link_el.get("href", ""),
                            "channel": ch["name"],
                            "published": (
                                (published_el.text or "")[:10]
                                if published_el is not None
                                else ""
                            ),
                            "description": truncate(
                                desc_el.text if desc_el is not None else "", 160
                            ),
                        }
                    )
                    fetched += 1
            print(f"  YouTube [{ch['name']}]: {fetched}件")
        except Exception as e:
            print(f"  YouTube [{ch['name']}] エラー: {e}")
    return items


# ===== Markdown 生成 =====

def generate_markdown(rss_items, reddit_items, hn_items, youtube_items) -> str:
    print("\n[翻訳]")
    translated_rss = translate_with_claude(rss_items)

    all_titles = [i.get("title", "") for i in rss_items + reddit_items + hn_items + youtube_items]
    keywords = extract_keywords(all_titles)

    total = len(rss_items) + len(reddit_items) + len(hn_items) + len(youtube_items)
    highlights = translated_rss[:3]
    rest_rss = translated_rss[3:]
    date_jp = NOW.strftime("%Y年%-m月%-d日")

    L = []

    L += [
        "---",
        f'title: "AI NEWS | {DATE_STR}"',
        f'description: "{date_jp} の生成AI最新ニュース ({total}件)"',
        f"date: {DATE_STR}",
        "---",
        "",
        '<div class="ai-page">',
        "",
        '<div class="page-header">',
        '<h1 class="page-title">AI NEWS</h1>',
        f'<p class="page-date">{date_jp}</p>',
        '<div class="page-stats">',
        f'<span class="stat">{total} articles</span>',
        '<span class="stat">Updated daily 6:00 AM JST</span>',
        "</div></div>",
        "",
    ]

    if keywords:
        L.append('<p class="section-label">TODAY\'S KEYWORDS</p>')
        L.append('<div class="trend-tags">')
        for i, kw in enumerate(keywords):
            cls = "trend-tag hot" if i < 3 else "trend-tag"
            L.append(f'<span class="{cls}">{kw}</span>')
        L += ["</div>", ""]

    if highlights:
        L.append('<p class="section-label">HIGHLIGHTS</p>')
        L.append('<div class="highlights-grid">')
        for item in highlights:
            meta = f'<span class="source-badge">{item.get("source","")}</span>'
            if item.get("date"):
                meta += f' · {item["date"]}'
            L += [
                '<div class="highlight-card">',
                '<div class="highlight-badge">PICK UP</div>',
                f'<h3><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></h3>',
            ]
            if item.get("summary"):
                L.append(f'<p>{item["summary"]}</p>')
            L += [f'<div class="card-meta">{meta}</div>', "</div>"]
        L += ["</div>", ""]

    if rest_rss:
        L.append('<p class="section-label">AI NEWS</p>')
        L.append('<div class="news-grid">')
        for item in rest_rss:
            meta = f'<span class="source-badge">{item.get("source","")}</span>'
            if item.get("date"):
                meta += f' · {item["date"]}'
            L.append('<div class="news-item">')
            L.append(f'<h3><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></h3>')
            if item.get("summary"):
                L.append(f'<p>{item["summary"]}</p>')
            L += [f'<div class="card-meta">{meta}</div>', "</div>"]
        L += ["</div>", ""]

    if reddit_items or hn_items:
        L.append('<p class="section-label">COMMUNITY</p>')
        L.append('<div class="news-grid">')
        for item in reddit_items:
            L += [
                '<div class="news-item reddit">',
                f'<h3><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></h3>',
                f'<div class="card-meta"><span class="source-badge">r/{item["sub"]}</span>'
                f' · {item["score"]:,} pts · {item["comments"]:,} comments</div>',
                "</div>",
            ]
        for item in hn_items:
            L += [
                '<div class="news-item hn">',
                f'<h3><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></h3>',
                f'<div class="card-meta"><span class="source-badge">HackerNews</span>'
                f' · {item["score"]} pts'
                f' · <a href="{item["hn_url"]}">{item["comments"]} comments</a></div>',
                "</div>",
            ]
        L += ["</div>", ""]

    if youtube_items:
        L.append('<p class="section-label">VIDEOS</p>')
        L.append('<div class="news-grid">')
        for item in youtube_items:
            meta = f'<span class="source-badge">{item["channel"]}</span>'
            if item.get("published"):
                meta += f' · {item["published"]}'
            L.append('<div class="news-item youtube">')
            L.append(f'<h3><a href="{item["url"]}" target="_blank" rel="noopener">{item["title"]}</a></h3>')
            if item.get("description"):
                L.append(f'<p>{item["description"]}</p>')
            L += [f'<div class="card-meta">{meta}</div>', "</div>"]
        L += ["</div>", ""]

    L += [
        '<div class="page-footer">',
        f'Last updated: {NOW.strftime("%Y-%m-%d %H:%M")} JST'
        f' &nbsp;|&nbsp; <a href="{BASE_PATH}/daily/">Archive</a>',
        "</div>",
        "",
        "</div>",
        "",
    ]

    return "\n".join(L)


# ===== アーカイブ更新 =====

def update_archive(title: str):
    os.makedirs(DAILY_DIR, exist_ok=True)
    index_path = os.path.join(DAILY_DIR, "index.md")
    entry_line = f"- [{title}]({BASE_PATH}/daily/{DATE_STR})"

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        if DATE_STR in content:
            return  # 今日分は既に追記済み
        lines = content.split("\n")
        insert_idx = None
        for i, line in enumerate(lines):
            if line.startswith("- ["):
                insert_idx = i
                break
        if insert_idx is not None:
            lines.insert(insert_idx, entry_line)
        else:
            # リストがない場合: _まだアーカイブ..._ 行を置換
            lines = [
                line if not line.startswith("_まだアーカイブ") else entry_line
                for line in lines
            ]
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    else:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(
                "---\ntitle: アーカイブ\ndescription: 過去のAIニュースまとめ一覧\n---\n\n"
                "# 過去のレポート\n\n"
                f"{entry_line}\n"
            )


# ===== メイン =====

def main():
    print(f"=== AI ニュース収集開始 ({DATE_STR}) ===")

    print("\n[RSS]")
    rss_items = fetch_rss()

    print("\n[Reddit]")
    reddit_items = fetch_reddit()

    print("\n[HackerNews]")
    hn_items = fetch_hackernews()

    print("\n[YouTube]")
    youtube_items = fetch_youtube()

    total = len(rss_items) + len(reddit_items) + len(hn_items) + len(youtube_items)
    print(f"\n合計 {total} 件収集")

    # Markdown 生成
    content = generate_markdown(rss_items, reddit_items, hn_items, youtube_items)
    title = f"AI NEWS | {DATE_STR}"

    # 日次ファイル保存
    os.makedirs(DAILY_DIR, exist_ok=True)
    daily_path = os.path.join(DAILY_DIR, f"{DATE_STR}.md")
    with open(daily_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n日次ファイル: {daily_path}")

    # ホームページ更新（最新号を常にトップに表示）
    home_path = os.path.join(DOCS_DIR, "index.md")
    with open(home_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"ホームページ更新: {home_path}")

    # アーカイブ更新
    update_archive(title)
    print("アーカイブ更新完了")

    print(f"\n=== 完了 ===")


if __name__ == "__main__":
    main()
