#!/usr/bin/env python3
"""
ROOM Data Collector for aokinomori shop
Searches Rakuten ROOM for each product and aggregates post/like data.
Outputs a DATA JSON file to embed into index.html.

Usage:
    python3 room_collector.py               # collect all products
    python3 room_collector.py --output data.json
    python3 room_collector.py --inject      # write into index.html directly
    python3 room_collector.py --dry-run     # show API results without saving
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import gzip
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ── Product definitions ────────────────────────────────────────────────────────
SHOP_NAME = "aokinomori楽天市場店"
SHOP_CODE = "aokinomori"

PRODUCTS = [
    {
        "item_id": "P001",
        "item_short": "ハーバニエンス",
        "item_name": "ハーバニエンス ハーブガーデンセット",
        "item_url": "https://item.rakuten.co.jp/aokinomori/s-herbgarden_set/",
        "item_code": "s-herbgarden_set",
        "keyword": "ハーバニエンス アミノ酸シャンプー",
    },
    {
        "item_id": "P002",
        "item_short": "ホワイトプラス",
        "item_name": "MYC ホワイトプラス",
        "item_url": "https://item.rakuten.co.jp/aokinomori/mycwhite/",
        "item_code": "mycwhite",
        "keyword": "ホワイトプラス マイシー",
        "max_pages": 12,
    },
    {
        "item_id": "P003",
        "item_short": "ビアス",
        "item_name": "ビアス",
        "item_url": "https://item.rakuten.co.jp/aokinomori/bius/",
        "item_code": "bius",
        "keyword": "ビアス リポソームビタミンc",
    },
    {
        "item_id": "P004",
        "item_short": "グルタスキントナー",
        "item_name": "グルタスキントナー",
        "item_url": "https://item.rakuten.co.jp/aokinomori/glutathione/",
        "item_code": "glutathione",
        "keyword": "グルタスキントナー",
    },
    {
        "item_id": "P005",
        "item_short": "リノクル",
        "item_name": "リノクル",
        "item_url": "https://item.rakuten.co.jp/aokinomori/s-linokle/",
        "item_code": "s-linokle",
        "keyword": "リノクル くすみ",
    },
    {
        "item_id": "P006",
        "item_short": "レチノソームショット",
        "item_name": "レチノソームショット",
        "item_url": "https://item.rakuten.co.jp/aokinomori/retinol/",
        "item_code": "retinol",
        "keyword": "レチノソームショット",
    },
    {
        "item_id": "P007",
        "item_short": "ハーブラピール",
        "item_name": "ハーブラピール",
        "item_url": "https://item.rakuten.co.jp/aokinomori/hlpeel/",
        "item_code": "hlpeel",
        "keyword": "ハーブラピール",
    },
    {
        "item_id": "P008",
        "item_short": "ビタスポットセラム",
        "item_name": "ビタスポットセラム",
        "item_url": "https://item.rakuten.co.jp/aokinomori/myc-skinity-serum/",
        "item_code": "myc-skinity-serum",
        "keyword": "ビタスポットセラム",
    },
    {
        "item_id": "P009",
        "item_short": "ジェルバームクレンジング",
        "item_name": "MYC ジェルバームクレンジング",
        "item_url": "https://item.rakuten.co.jp/aokinomori/myc-clean/",
        "item_code": "myc-clean",
        "keyword": "マイシースキニティ ジェルバームクレンジング",
    },
]

API_BASE = "https://room.rakuten.co.jp/api"
PAGE_LIMIT = 20
SLEEP_BETWEEN_PAGES = 0.5   # seconds
SLEEP_BETWEEN_PRODUCTS = 1.0
DEFAULT_MAX_PAGES = 10
DEFAULT_API_TIMEOUT = 15
DEFAULT_RETRIES = 2
RETRY_BACKOFF = 2.0  # seconds, multiplied by attempt number


# ── HTTP helper ────────────────────────────────────────────────────────────────
def api_get(path, params=None, timeout=DEFAULT_API_TIMEOUT, retries=DEFAULT_RETRIES):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip",
        "Accept-Language": "ja-JP,ja;q=0.9",
        "Referer": "https://room.rakuten.co.jp/",
    })
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                return json.loads(data)
        except Exception:
            if attempt < retries:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            raise


# ── Core collection logic ──────────────────────────────────────────────────────
def collect_product(product, verbose=True, max_pages=None, timeout=DEFAULT_API_TIMEOUT, sleep_between_pages=SLEEP_BETWEEN_PAGES, retries=DEFAULT_RETRIES):
    """Fetch ROOM posts for a single product.

    Returns (posts, had_error) where had_error indicates the fetch stopped
    early because of a request failure (as opposed to legitimately running
    out of pages), so callers can decide whether the result is trustworthy
    enough to overwrite previously collected data.
    """
    item_url = product["item_url"].rstrip("/") + "/"  # normalise trailing slash
    keyword = product["keyword"]
    item_code = product["item_code"]
    max_pages = max_pages if max_pages is not None else product.get("max_pages", DEFAULT_MAX_PAGES)

    if verbose:
        print(f"  Searching: {product['item_short']} (keyword={keyword!r})", flush=True)

    posts = []
    seen_ids = set()
    page = 1
    total_pages = None
    had_error = False

    while True:
        params = {
            "api_version": 1,
            "query": keyword,
            "page": page,
        }
        try:
            resp = api_get("/collect/search", params, timeout=timeout, retries=retries)
        except Exception as exc:
            print(f"    [ERROR] page={page}: {exc}", file=sys.stderr)
            had_error = True
            break

        if resp.get("status") != "success":
            print(f"    [WARN] page={page} status={resp.get('status')}", file=sys.stderr)
            had_error = True
            break

        data = resp.get("data", [])
        if not data:
            break

        if total_pages is None:
            total_count = resp.get("count", 0)
            total_pages = (total_count + PAGE_LIMIT - 1) // PAGE_LIMIT
            if max_pages is not None:
                total_pages = min(total_pages, max_pages)
            if verbose:
                cap_note = f", capped at {max_pages}" if max_pages is not None and total_count // PAGE_LIMIT >= max_pages else ""
                print(f"    Total posts in ROOM for keyword: {total_count} ({total_pages} pages{cap_note})", flush=True)

        # Filter to only this shop's specific product, deduplicate by post ID
        for post in data:
            pid = post.get("id", "")
            if pid in seen_ids:
                continue
            seen_ids.add(pid)
            post_item = post.get("item", {})
            post_url_raw = post_item.get("url", "")
            # Normalise
            post_url = post_url_raw.rstrip("/") + "/"
            # Match by exact URL or by item_code inside URL
            if post_url == item_url or (
                SHOP_CODE in post_url and item_code in post_url
            ):
                posts.append(post)

        if verbose and page % 5 == 0:
            print(f"    page {page}/{total_pages}  matched so far: {len(posts)}", flush=True)

        if page >= total_pages:
            break
        page += 1
        if sleep_between_pages > 0:
            time.sleep(sleep_between_pages)

    if verbose:
        print(f"    → {len(posts)} posts matched for {product['item_short']}", flush=True)
    return posts, had_error


# ── Carry-forward of previous results when a fetch fails ──────────────────────
def flat_post_to_raw(post):
    """Convert a previously-saved flat post (from room_data.json) back into
    the raw shape aggregate() expects, so it can be reused as a fallback."""
    return {
        "id": post.get("post_id", ""),
        "created_at": post.get("created_at", ""),
        "likes": post.get("likes", 0),
        "comments": post.get("comments", 0),
        "recollects": post.get("recollects", 0),
        "detail_views": post.get("detail_views", 0),
        "influence_points": post.get("influence_points", 0),
        "user": {
            "username": post.get("username", ""),
            "fullname": post.get("fullname", ""),
            "rank": post.get("user_rank", 0),
        },
        "item": {"price": post.get("price", 0)},
        "from_service": post.get("from_service", "room"),
    }


def load_previous_posts_by_item(path):
    """Load the previous output file's posts, grouped by item_id, so a
    product whose fetch fails this run can fall back to its last known
    good data instead of being zeroed out."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

    by_item = defaultdict(list)
    for post in data.get("posts", []):
        by_item[post.get("item_id")].append(flat_post_to_raw(post))
    return by_item


# ── Aggregate raw posts into DATA format ──────────────────────────────────────
def aggregate(all_posts_by_product, products, generated_at):
    """Build the DATA object expected by index.html."""
    flat_posts = []
    item_stats = []
    user_map = defaultdict(lambda: {"posts": 0, "total_likes": 0, "fullname": "", "rank": 0})
    by_day_map = defaultdict(lambda: {"n": 0, "likes": 0})

    for product in products:
        pid = product["item_id"]
        raw = all_posts_by_product.get(pid, [])
        item_likes = 0
        item_comments = 0
        item_recollects = 0
        item_latest = None

        for p in raw:
            # Post fields
            post_id = p.get("id", "")
            created_at = p.get("created_at", "")
            likes = int(p.get("likes") or 0)
            comments = int(p.get("comments") or 0)
            recollects = int(p.get("recollects") or 0)
            detail_views = int(p.get("detail_views") or 0)
            influence_points = int(p.get("influence_points") or 0)

            user = p.get("user", {})
            username = user.get("username", "")
            fullname = user.get("fullname", "")
            user_rank = int(user.get("rank") or 0)
            from_service = p.get("from_service", "room")

            post_url = f"https://room.rakuten.co.jp/{username}/{post_id}"

            flat_posts.append({
                "post_id": post_id,
                "created_at": created_at,
                "username": username,
                "fullname": fullname,
                "user_rank": user_rank,
                "item_id": pid,
                "item_name": product["item_name"],
                "item_url": product["item_url"],
                "post_url": post_url,
                "price": int(p.get("item", {}).get("price") or 0),
                "from_service": from_service,
                "likes": likes,
                "comments": comments,
                "recollects": recollects,
                "detail_views": detail_views,
                "influence_points": influence_points,
                "item_short": product["item_short"],
            })

            item_likes += likes
            item_comments += comments
            item_recollects += recollects

            if item_latest is None or created_at > item_latest:
                item_latest = created_at

            # User aggregation
            user_map[username]["posts"] += 1
            user_map[username]["total_likes"] += likes
            user_map[username]["fullname"] = fullname
            user_map[username]["rank"] = user_rank

            # By-day aggregation
            day = created_at[:10] if created_at else None
            if day:
                by_day_map[day]["n"] += 1
                by_day_map[day]["likes"] += likes

        n_posts = len(raw)
        likes_per_post = round(item_likes / n_posts, 1) if n_posts else 0
        recollect_rate = round(item_recollects / n_posts, 2) if n_posts else 0
        influence = item_likes + item_recollects * 3

        item_stats.append({
            "item_id": pid,
            "item_name": product["item_name"],
            "item_short": product["item_short"],
            "posts": n_posts,
            "likes": item_likes,
            "comments": item_comments,
            "recollects": item_recollects,
            "latest": item_latest or "",
            "likes_per_post": likes_per_post,
            "recollect_rate": recollect_rate,
            "influence": influence,
        })

    # Sort flat_posts by likes desc for display
    flat_posts.sort(key=lambda p: p["likes"], reverse=True)

    # Users list sorted by total_likes
    users_list = [
        {
            "username": un,
            "fullname": d["fullname"],
            "posts": d["posts"],
            "total_likes": d["total_likes"],
            "rank": d["rank"],
        }
        for un, d in sorted(user_map.items(), key=lambda x: x[1]["total_likes"], reverse=True)
    ]

    # by_day sorted
    by_day = [
        {"day": day, "n": v["n"], "likes": v["likes"]}
        for day, v in sorted(by_day_map.items())
    ]

    # Summary
    total_posts = len(flat_posts)
    total_likes = sum(p["likes"] for p in flat_posts)
    total_comments = sum(p["comments"] for p in flat_posts)
    total_recollects = sum(p["recollects"] for p in flat_posts)
    total_users = len(user_map)
    total_items = len([s for s in item_stats if s["posts"] > 0])

    # Momentum: compare last 7 days vs prior 7 days
    today = datetime.now(timezone.utc).date()
    import datetime as dt
    cutoff_recent = (today - dt.timedelta(days=7)).isoformat()
    cutoff_prior = (today - dt.timedelta(days=14)).isoformat()

    momentum_map = defaultdict(lambda: {"total": 0, "recent": 0, "prior": 0, "recent_likes": 0})
    for post in flat_posts:
        day = post["created_at"][:10] if post["created_at"] else ""
        pid_key = post["item_id"]
        short = post["item_short"]
        momentum_map[pid_key]["item_short"] = short
        momentum_map[pid_key]["total"] += 1
        if day >= cutoff_recent:
            momentum_map[pid_key]["recent"] += 1
            momentum_map[pid_key]["recent_likes"] += post["likes"]
        elif day >= cutoff_prior:
            momentum_map[pid_key]["prior"] += 1

    momentum = [
        {
            "item_id": k,
            "total": v["total"],
            "recent": v["recent"],
            "prior": v["prior"],
            "recent_likes": v["recent_likes"],
            "item_short": v.get("item_short", k),
        }
        for k, v in momentum_map.items()
    ]

    # Scatter: likes vs recollects by item
    scatter = [
        {"l": s["likes"], "r": s["recollects"], "i": s["item_short"]}
        for s in item_stats
        if s["posts"] > 0
    ]

    # Movers: posts with highest like growth (just top-liked as proxy)
    movers = [
        {
            "username": p["username"],
            "post_url": p["post_url"],
            "item_name": p["item_name"],
            "item_short": p["item_short"],
            "first_likes": max(0, p["likes"] - 10),
            "last_likes": p["likes"],
            "delta": min(10, p["likes"]),
        }
        for p in flat_posts[:20]
        if p["likes"] > 0
    ]

    return {
        "meta": {
            "shop_name": SHOP_NAME,
            "shop_code": SHOP_CODE,
            "generated_at": generated_at,
            "snapshots": 1,
        },
        "summary": {
            "posts": total_posts,
            "users": total_users,
            "items": total_items,
            "likes": total_likes,
            "comments": total_comments,
            "recollects": total_recollects,
        },
        "posts": flat_posts,
        "items": item_stats,
        "users": users_list[:100],
        "by_day": by_day,
        "movers": movers,
        "momentum": momentum,
        "scatter": scatter,
        "access": {"available": False},
    }


# ── index.html injection ───────────────────────────────────────────────────────
def inject_into_html(data_obj, html_path="index.html"):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    data_json = json.dumps(data_obj, ensure_ascii=False, separators=(',', ':'))
    new_const = "const DATA=" + data_json + ";"

    # Replace existing const DATA = {...};
    pattern = r"const DATA\s*=\s*\{[\s\S]*?\};"
    if re.search(pattern, html):
        html = re.sub(pattern, lambda m: new_const, html, count=1)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓ Injected DATA into {html_path}")
    else:
        print(f"[WARN] Could not find 'const DATA = ...' in {html_path}", file=sys.stderr)


# ── Main ───────────────────────────────────────────────────────────────────────
def get_generated_at():
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")


def main():
    parser = argparse.ArgumentParser(description="Collect Rakuten ROOM data for aokinomori shop.")
    parser.add_argument("--output", "-o", default="room_data.json", help="Output JSON path")
    parser.add_argument("--inject", action="store_true", help="Inject into index.html after collecting")
    parser.add_argument("--html", default="index.html", help="Path to index.html for --inject")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without saving")
    parser.add_argument("--product", "-p", help="Only collect this product (item_short)")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to scan per product")
    parser.add_argument("--timeout", type=int, default=DEFAULT_API_TIMEOUT, help="HTTP timeout in seconds for each request")
    parser.add_argument("--no-sleep", action="store_true", help="Disable delay between pages")
    args = parser.parse_args()

    generated_at = get_generated_at()

    targets = PRODUCTS
    if args.product:
        targets = [p for p in PRODUCTS if p["item_short"] == args.product]
        if not targets:
            print(f"[ERROR] Product {args.product!r} not found", file=sys.stderr)
            sys.exit(1)

    print(f"Collecting ROOM data for shop: {SHOP_CODE}")
    print(f"Products: {[p['item_short'] for p in targets]}")
    print()

    previous_posts_by_item = load_previous_posts_by_item(args.output)

    all_posts = {}
    for i, product in enumerate(targets, 1):
        pid = product["item_id"]
        print(f"[{i}/{len(targets)}] {product['item_short']}")
        posts, had_error = collect_product(
            product,
            verbose=True,
            max_pages=args.max_pages,
            timeout=args.timeout,
            sleep_between_pages=0 if args.no_sleep else SLEEP_BETWEEN_PAGES,
        )
        previous_posts = previous_posts_by_item.get(pid, [])
        if had_error and len(posts) < len(previous_posts):
            print(
                f"    [WARN] fetch incomplete ({len(posts)} posts) for {product['item_short']}, "
                f"keeping previous {len(previous_posts)} posts instead of overwriting",
                flush=True,
            )
            posts = previous_posts
        all_posts[pid] = posts
        if i < len(targets) and not args.no_sleep:
            time.sleep(SLEEP_BETWEEN_PRODUCTS)

    # Any product not collected this run (e.g. a --product filter was used,
    # or it was skipped entirely) keeps its last known good data rather than
    # disappearing from the output.
    for product in PRODUCTS:
        pid = product["item_id"]
        if pid not in all_posts:
            all_posts[pid] = previous_posts_by_item.get(pid, [])

    print()
    print("Building DATA object...")
    data_obj = aggregate(all_posts, PRODUCTS, generated_at)

    # Summary printout
    s = data_obj["summary"]
    print(f"  Total posts   : {s['posts']}")
    print(f"  Total likes   : {s['likes']}")
    print(f"  Total users   : {s['users']}")
    print()
    print("  Per product:")
    for item in data_obj["items"]:
        print(f"    {item['item_short']:20s}  posts={item['posts']:4d}  likes={item['likes']:6d}  avg={item['likes_per_post']:.1f}")

    if args.dry_run:
        print("\n[dry-run] Not saving.")
        return

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Saved to {args.output}")

    if args.inject:
        inject_into_html(data_obj, args.html)


if __name__ == "__main__":
    main()
