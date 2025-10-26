#!/usr/bin/env python3
"""
Test different methods to bypass FBref's 403 protection
"""

import sys

def test_method_1_cloudscraper():
    """Method 1: Try cloudscraper (Cloudflare bypass)"""
    print("\n" + "=" * 80)
    print("METHOD 1: CloudScraper (Cloudflare Bypass)")
    print("=" * 80)

    try:
        import cloudscraper

        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

        url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
        print(f"Fetching: {url}")

        response = scraper.get(url, timeout=30)
        response.raise_for_status()

        print(f"✓ SUCCESS! Status code: {response.status_code}")
        print(f"✓ Content length: {len(response.content)} bytes")

        # Check if we got actual content
        if 'Bundesliga' in response.text:
            print("✓ Page contains 'Bundesliga' - looks good!")
            return True, scraper
        else:
            print("⚠️  Page doesn't contain expected content")
            return False, None

    except ImportError:
        print("✗ cloudscraper not installed")
        print("  Install with: pip install cloudscraper")
        return False, None
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None


def test_method_2_improved_headers():
    """Method 2: Try requests with improved headers"""
    print("\n" + "=" * 80)
    print("METHOD 2: Improved Headers with Referer")
    print("=" * 80)

    try:
        import requests

        session = requests.Session()

        # More complete browser headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })

        url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
        print(f"Fetching: {url}")

        response = session.get(url, timeout=30)
        response.raise_for_status()

        print(f"✓ SUCCESS! Status code: {response.status_code}")
        print(f"✓ Content length: {len(response.content)} bytes")

        if 'Bundesliga' in response.text:
            print("✓ Page contains 'Bundesliga' - looks good!")
            return True, session
        else:
            print("⚠️  Page doesn't contain expected content")
            return False, None

    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None


def test_method_3_playwright():
    """Method 3: Try Playwright (real browser)"""
    print("\n" + "=" * 80)
    print("METHOD 3: Playwright (Real Browser Automation)")
    print("=" * 80)

    try:
        from playwright.sync_api import sync_playwright

        print("Starting browser...")

        with sync_playwright() as p:
            # Launch browser (headless)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
            print(f"Fetching: {url}")

            # Navigate to page
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)

            if response.status == 200:
                print(f"✓ SUCCESS! Status code: {response.status}")

                # Get content
                content = page.content()
                print(f"✓ Content length: {len(content)} bytes")

                if 'Bundesliga' in content:
                    print("✓ Page contains 'Bundesliga' - looks good!")

                    # Close browser
                    browser.close()
                    return True, 'playwright'
                else:
                    print("⚠️  Page doesn't contain expected content")
                    browser.close()
                    return False, None
            else:
                print(f"✗ FAILED: Status code {response.status}")
                browser.close()
                return False, None

    except ImportError:
        print("✗ Playwright not installed")
        print("  Install with: pip install playwright")
        print("  Then run: playwright install chromium")
        return False, None
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None


def main():
    """Test all methods"""
    print("=" * 80)
    print("FBREF 403 BYPASS TEST - TRYING MULTIPLE METHODS")
    print("=" * 80)

    results = []

    # Test Method 1: CloudScraper
    success, scraper = test_method_1_cloudscraper()
    results.append(('CloudScraper', success, scraper))

    # Test Method 2: Improved Headers
    if not success:
        success, scraper = test_method_2_improved_headers()
        results.append(('Improved Headers', success, scraper))

    # Test Method 3: Playwright
    if not success:
        success, scraper = test_method_3_playwright()
        results.append(('Playwright', success, scraper))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for method, success, _ in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{method:20s} : {status}")

    # Recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    working_methods = [m for m, s, _ in results if s]

    if working_methods:
        print(f"✓ Working method(s): {', '.join(working_methods)}")
        print(f"\nI will update fbref.py to use: {working_methods[0]}")
    else:
        print("✗ None of the methods worked")
        print("\nPossible reasons:")
        print("  1. FBref has very strong anti-bot protection")
        print("  2. IP might be temporarily blocked")
        print("  3. Additional authentication might be required")
        print("\nAlternatives:")
        print("  - Use Understat API for xG data (free)")
        print("  - Use goals as xG proxy (current fallback)")
        print("  - Try from different IP/network")

    print("=" * 80)


if __name__ == "__main__":
    main()
