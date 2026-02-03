"""Web scraper for knowledge base creation (BeautifulSoup, text only)."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class ScrapedContent:
    url: str
    title: str
    headings: List[str]
    paragraphs: List[str]
    links: List[str]
    metadata: Dict[str, str]
    scraped_at: str
    word_count: int
    text_content: str


@dataclass
class KnowledgeBase:
    website_url: str
    domain: str
    scraped_pages: List[ScrapedContent]
    total_word_count: int
    created_at: str
    metadata: Dict[str, any]


class WebsiteScraper:
    def __init__(self, base_url: str, delay: float = 1.0, max_pages: int = 50):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.root_domain = self._root_domain(self.domain)
        self.delay = delay
        self.max_pages = max_pages

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        self.visited_urls: Set[str] = set()
        self.to_visit_urls: Set[str] = set([base_url])
        self.scraped_content: List[ScrapedContent] = []

    def _root_domain(self, netloc: str) -> str:
        s = netloc.lower().strip()
        parts = s.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return s

    def is_same_domain(self, url: str) -> bool:
        try:
            netloc = urlparse(url).netloc.lower().strip()
            if not netloc:
                return False
            root = self.root_domain
            return netloc == root or netloc.endswith("." + root)
        except Exception:
            return False

    def normalize_url(self, url: str, base_url: str) -> str:
        return urljoin(base_url, url)

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text.strip())
        text = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)

        return text

    def extract_text_content(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return self.clean_text(text)

    def extract_structured_content(
        self, soup: BeautifulSoup, url: str
    ) -> ScrapedContent:
        """Extract structured content from the page"""
        # Title
        title = soup.title.string if soup.title else ""
        title = self.clean_text(title) if title else f"Page from {url}"

        # Headings
        headings = []
        for i in range(1, 7):  # h1 to h6
            h_tags = soup.find_all(f"h{i}")
            headings.extend(
                [self.clean_text(h.get_text()) for h in h_tags if h.get_text()]
            )

        paragraphs = []
        p_tags = soup.find_all("p")
        for p in p_tags:
            text = self.clean_text(p.get_text())
            if text and len(text) > 10:
                paragraphs.append(text)

        links = []
        a_tags = soup.find_all("a", href=True)
        for a in a_tags:
            href = a["href"]
            if href and not href.startswith("#") and not href.startswith("mailto:"):
                full_url = self.normalize_url(href, url)
                if self.is_same_domain(full_url):
                    links.append(full_url)

        # Metadata
        metadata = {}
        meta_tags = soup.find_all("meta")
        for meta in meta_tags:
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content

        text_content = self.extract_text_content(soup)
        word_count = len(text_content.split()) if text_content else 0

        return ScrapedContent(
            url=url,
            title=title,
            headings=headings,
            paragraphs=paragraphs,
            links=list(set(links)),  # Remove duplicates
            metadata=metadata,
            scraped_at=datetime.now().isoformat(),
            word_count=word_count,
            text_content=text_content,
        )

    def scrape_page(self, url: str) -> Optional[ScrapedContent]:
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if not ("text/html" in content_type or "text" in content_type):
                print(f"Skipping non-HTML content: {content_type}")
                return None

            # Parse HTML
            soup = BeautifulSoup(response.content, "lxml")

            # Extract content
            content = self.extract_structured_content(soup, url)

            return content

        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None

    def crawl_website(self) -> KnowledgeBase:
        print(f"Starting crawl of {self.base_url}")
        print(f"Domain: {self.domain}")
        print(f"Max pages: {self.max_pages}")

        page_count = 0

        while self.to_visit_urls and page_count < self.max_pages:
            current_url = self.to_visit_urls.pop()
            if current_url in self.visited_urls:
                continue
            self.visited_urls.add(current_url)

            content = self.scrape_page(current_url)
            if content:
                self.scraped_content.append(content)
                page_count += 1
                for link in content.links:
                    if link not in self.visited_urls and link not in self.to_visit_urls:
                        self.to_visit_urls.add(link)

            if self.delay > 0:
                time.sleep(self.delay)

        # Calculate total word count
        total_word_count = sum(content.word_count for content in self.scraped_content)

        # Create knowledge base
        kb = KnowledgeBase(
            website_url=self.base_url,
            domain=self.domain,
            scraped_pages=self.scraped_content,
            total_word_count=total_word_count,
            created_at=datetime.now().isoformat(),
            metadata={
                "total_pages": len(self.scraped_content),
                "visited_urls": len(self.visited_urls),
                "max_pages_limit": self.max_pages,
                "delay_between_requests": self.delay,
            },
        )

        print(
            f"Crawl completed. Scraped {len(self.scraped_content)} pages with {total_word_count} total words."
        )
        return kb

    def save_knowledge_base(
        self, kb: KnowledgeBase, output_dir: str = "knowledge_base"
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        safe_domain = re.sub(r"[^\w\-_.]", "_", self.domain)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_domain}_knowledge_base_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        kb_dict = asdict(kb)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(kb_dict, f, indent=2, ensure_ascii=False)

        print(f"Knowledge base saved to: {filepath}")
        return filepath

    def save_text_summary(
        self, kb: KnowledgeBase, output_dir: str = "knowledge_base"
    ) -> str:
        """Save a readable text summary of the knowledge base"""
        os.makedirs(output_dir, exist_ok=True)

        safe_domain = re.sub(r"[^\w\-_.]", "_", self.domain)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_domain}_summary_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Knowledge Base for {kb.website_url}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Domain: {kb.domain}\n")
            f.write(f"Total Pages: {len(kb.scraped_pages)}\n")
            f.write(f"Total Words: {kb.total_word_count}\n")
            f.write(f"Created: {kb.created_at}\n\n")

            for i, page in enumerate(kb.scraped_pages, 1):
                f.write(f"Page {i}: {page.title}\n")
                f.write(f"URL: {page.url}\n")
                f.write(f"Words: {page.word_count}\n")

                if page.headings:
                    f.write("Headings:\n")
                    for heading in page.headings:
                        f.write(f"  • {heading}\n")

                f.write("\nContent Preview:\n")
                preview = (
                    page.text_content[:500] + "..."
                    if len(page.text_content) > 500
                    else page.text_content
                )
                f.write(f"{preview}\n\n")
                f.write("-" * 50 + "\n\n")

        print(f"Text summary saved to: {filepath}")
        return filepath


def scrape_website(
    base_url: str, max_pages: int = 50, delay: float = 1.0
) -> KnowledgeBase:
    scraper = WebsiteScraper(base_url, delay=delay, max_pages=max_pages)
    return scraper.crawl_website()
