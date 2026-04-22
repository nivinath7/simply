import requests
from bs4 import BeautifulSoup
import json
import time 
import os 
from datetime import datetime 
import re

def load_urls(filepath: str) -> list[str]:

    with open(filepath, "r") as f:
        urls = json.load(f)
    
    print(f"Loaded {len(urls)} URLs from {filepath}")
    return urls


def scrape_page(url: str) -> dict | None:
    """
    Scrapes a single NHS page.
    Returns structured dict or None if it fails.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; research project)"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"  ✗ Failed — status {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = ""
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Extract main content
        content = soup.find("div", {"class": "nhsuk-main-wrapper"})
        if not content:
            content = soup.find("main")
        if not content:
            print(f"  ✗ No content found")
            return None

        # Extract paragraphs
        paragraphs = content.find_all("p")
        text_blocks = [
        p.get_text(separator=" ", strip=True)
        for p in paragraphs
        if p.get_text(separator=" ", strip=True)
    ]

        # Extract headings
        headings = content.find_all(["h2", "h3"])
        heading_texts = [h.get_text(strip=True) for h in headings]

        full_text = "\n\n".join(text_blocks)
# Add this:
        full_text = re.sub(r'\s+([.,;:!?])', r'\1', full_text)

        if not full_text:
            print(f"  ✗ Empty content")
            return None

        return {
            "url": url,
            "title": title,
            "headings": heading_texts,
            "text": full_text,
            "source": "NHS",
            "scraped_at": datetime.now().isoformat(),
            "word_count": len(full_text.split())
        }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def url_to_filename(url: str) -> str:
    """Converts a URL into a clean filename."""
    clean = url.replace("https://", "").replace("http://", "")
    clean = clean.replace("/", "_").replace(".", "_").strip("_")
    return f"{clean}.json"


def save_document(doc: dict, output_dir: str) -> str:
    """Saves a document as JSON. Returns the filepath."""
    os.makedirs(output_dir, exist_ok=True)
    filename = url_to_filename(doc["url"])
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    return filepath


def run_scraper(urls_file: str, output_dir: str):
    """Main function — reads URLs, scrapes, saves."""
    urls = load_urls(urls_file)
    print(f"\nStarting scraper — {len(urls)} pages\n")

    success, failed = 0, 0

    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] {url}")
        doc = scrape_page(url)

        if doc:
            filepath = save_document(doc, output_dir)
            print(f"  ✓ Saved: {filepath} ({doc['word_count']} words)")
            success += 1
        else:
            failed += 1

        time.sleep(1.5)  # be polite to NHS servers

    print(f"\nDone — {success} succeeded, {failed} failed")
    print(f"Files saved to: {output_dir}")


if __name__ == '__main__':
    run_scraper(
        urls_file="../../data/nhs_links.txt",
        output_dir="../../data/raw/nhs"
    )


