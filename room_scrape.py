#!/usr/bin/env python3
import argparse
import json
from urllib.parse import quote_plus

from playwright.sync_api import Error as PlaywrightError, sync_playwright

SEARCH_URL_TEMPLATE = 'https://room.rakuten.co.jp/search?keyword={}'

DEFAULT_KEYWORDS = [
    'リノクル',
    'ビタスポットセラム',
    'マイシースキニティジェルバームクレンジング',
    'ビアス',
    'ハーブラピール',
    'レチノソームショット',
    'ホワイトプラス',
    'ハーバニエンス',
]


def build_context_options():
    return {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'locale': 'ja-JP',
        'timezone_id': 'Asia/Tokyo',
        'viewport': {'width': 1440, 'height': 900},
        'java_script_enabled': True,
    }


def add_stealth_scripts(page):
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    page.add_init_script("window.navigator.chrome = { runtime: {} };")
    page.add_init_script("Object.defineProperty(navigator, 'languages', {get: () => ['ja-JP', 'ja']});")
    page.add_init_script("Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});")


def fetch_room_search(keyword: str, headless: bool = True, channel: str = None, screenshot: str = None):
    result = {
        'keyword': keyword,
        'search_url': SEARCH_URL_TEMPLATE.format(quote_plus(keyword)),
        'main_response': None,
        'search_request': None,
        'search_response': None,
        'page_title': None,
        'page_url': None,
        'page_text_snippet': None,
        'redirects': [],
        'errors': [],
    }

    with sync_playwright() as p:
        chromium = p.chromium
        launch_args = ['--disable-blink-features=AutomationControlled']
        try:
            browser = chromium.launch(channel=channel, headless=headless, args=launch_args)
        except PlaywrightError as exc:
            result['errors'].append(f'launch_failed: {exc}')
            return result

        context = browser.new_context(**build_context_options())
        context.set_extra_http_headers({'accept-language': 'ja-JP,ja;q=0.9'})
        page = context.new_page()
        add_stealth_scripts(page)

        def on_request(req):
            if 'search/items' in req.url or req.url.startswith('https://room.rakuten.co.jp/search?keyword='):
                result['search_request'] = {
                    'url': req.url,
                    'method': req.method,
                    'headers': req.headers,
                    'post_data': req.post_data,
                }

        def on_response(resp):
            if result['search_request'] and resp.url == result['search_request']['url']:
                try:
                    body = resp.text()
                except Exception as exc:
                    body = f'ERROR: {exc}'
                result['search_response'] = {
                    'url': resp.url,
                    'status': resp.status,
                    'headers': resp.headers,
                    'body_snippet': body[:2000],
                }
                if 300 <= resp.status < 400 and 'location' in resp.headers:
                    result['redirects'].append(resp.headers.get('location'))

        def on_request_failed(req):
            if result['search_request'] and req.url == result['search_request']['url']:
                result['errors'].append(f'request_failed: {req.failure}')

        page.on('request', on_request)
        page.on('response', on_response)
        page.on('requestfailed', on_request_failed)

        try:
            response = page.goto(result['search_url'], timeout=120000, wait_until='domcontentloaded')
            result['main_response'] = {
                'status': response.status if response else None,
                'url': response.url if response else None,
                'headers': response.headers if response else None,
            }
            page.wait_for_timeout(5000)
            result['page_url'] = page.url
            result['page_title'] = page.title()
            result['page_text_snippet'] = page.locator('body').inner_text()[:600]
            if screenshot:
                page.screenshot(path=screenshot, full_page=True)
                result['screenshot'] = screenshot
        except PlaywrightError as exc:
            result['errors'].append(f'playwright_error: {exc}')
        except Exception as exc:
            result['errors'].append(f'unexpected_error: {exc}')
        finally:
            browser.close()

    return result


def main():
    parser = argparse.ArgumentParser(description='Investigate Rakuten ROOM keyword search behavior.')
    parser.add_argument('--keyword', '-k', help='Keyword to search on Rakuten ROOM', default='ハーバニエンス')
    parser.add_argument('--headful', action='store_true', help='Launch browser in headful mode')
    parser.add_argument('--channel', help='Playwright browser channel (chrome, msedge, etc.)')
    parser.add_argument('--screenshot', help='Save a screenshot of the final page')
    parser.add_argument('--json', help='Save output as JSON to the path specified')
    args = parser.parse_args()

    output = fetch_room_search(args.keyword, headless=not args.headful, channel=args.channel, screenshot=args.screenshot)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
