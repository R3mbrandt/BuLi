#!/usr/bin/env python3
"""
Script to download and analyze the HTML structure of Transfermarkt injury page
"""

import requests
from bs4 import BeautifulSoup
import time

MODERN_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

def analyze_html():
    """Download and analyze Transfermarkt injury page HTML"""

    url = "https://www.transfermarkt.de/bundesliga/verletztespieler/wettbewerb/L1/plus/1"

    session = requests.Session()
    session.headers.update({
        'User-Agent': MODERN_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    })

    print("Fetching Transfermarkt page...")
    response = session.get(url, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'lxml')

    # Find injury table
    injury_table = soup.find('table', class_='items')

    if not injury_table:
        print("No table found!")
        return

    rows = injury_table.find_all('tr', class_=['odd', 'even'])
    print(f"\nFound {len(rows)} rows")

    # Analyze first 3 rows in detail
    for idx in range(min(3, len(rows))):
        row = rows[idx]
        print(f"\n{'=' * 80}")
        print(f"ROW {idx}")
        print(f"{'=' * 80}")

        # Get all cells
        cells = row.find_all('td')

        print(f"Number of cells: {len(cells)}")

        for cell_idx, cell in enumerate(cells):
            print(f"\n  Cell {cell_idx}:")
            print(f"    Classes: {cell.get('class', [])}")
            print(f"    Text: {cell.text.strip()[:100]}")

            # Check for images
            imgs = cell.find_all('img')
            if imgs:
                print(f"    Images found: {len(imgs)}")
                for img_idx, img in enumerate(imgs):
                    print(f"      Img {img_idx}:")
                    print(f"        src: {img.get('src', '')[:80]}")
                    print(f"        alt: {img.get('alt', '')}")
                    print(f"        title: {img.get('title', '')}")

            # Check for links
            links = cell.find_all('a')
            if links:
                print(f"    Links found: {len(links)}")
                for link_idx, link in enumerate(links):
                    print(f"      Link {link_idx}:")
                    print(f"        href: {link.get('href', '')[:80]}")
                    print(f"        text: {link.text.strip()[:50]}")
                    print(f"        title: {link.get('title', '')[:50]}")

    # Save a sample row to file for inspection
    if rows:
        with open('sample_row.html', 'w', encoding='utf-8') as f:
            f.write(str(rows[0].prettify()))
        print(f"\n\n✓ First row saved to sample_row.html")

if __name__ == "__main__":
    analyze_html()
