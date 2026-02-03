#!/usr/bin/env python3
"""Website Knowledge Base Scraper."""

import argparse
import sys
import os
from typing import Optional
from scraper import scrape_website, WebsiteScraper
from processor import TextProcessor, EnhancedKnowledgeBase
import json


def main():
    parser = argparse.ArgumentParser(
        description="Website Knowledge Base Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
                    Examples:
                    python main.py https://example.com
                    python main.py https://example.com --max-pages 100 --delay 2.0
                    python main.py https://example.com --output-dir my_kb --enhance
                    python main.py https://example.com --search "machine learning"
                    python main.py https://example.com --all
                """,
    )

    parser.add_argument("url", help="Website URL to scrape")

    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum number of pages to scrape (default: 50)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        dest="scrape_all",
        help="Scrape all pages on the site (no limit; ignores --max-pages)",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--output-dir",
        default="knowledge_base",
        help="Output directory for knowledge base files (default: knowledge_base)",
    )

    parser.add_argument(
        "--enhance",
        action="store_true",
        help="Apply advanced NLP processing to create enhanced knowledge base",
    )

    parser.add_argument(
        "--search",
        help="Search the knowledge base for specific content (requires existing KB)",
    )

    parser.add_argument(
        "--kb-file", help="Path to existing knowledge base file for search operations"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.scrape_all:
        args.max_pages = 100_000

    if not args.url.startswith(("http://", "https://")):
        print("Error: URL must start with http:// or https://")
        sys.exit(1)

    if args.search:
        if not args.kb_file:
            print("Error: --kb-file is required when using --search")
            sys.exit(1)

        perform_search(args.kb_file, args.search)
        return

    print(f"Starting web scraping for: {args.url}")
    print(
        f"Max pages: {'all' if args.scrape_all else args.max_pages}, Delay: {args.delay}s"
    )

    try:
        # Create scraper and scrape website
        scraper = WebsiteScraper(args.url, delay=args.delay, max_pages=args.max_pages)
        knowledge_base = scraper.crawl_website()

        if not knowledge_base.scraped_pages:
            print(
                "No content was successfully scraped. Please check the URL and try again."
            )
            sys.exit(1)

        kb_file = scraper.save_knowledge_base(knowledge_base, args.output_dir)
        text_file = scraper.save_text_summary(knowledge_base, args.output_dir)

        print("\nBasic knowledge base created:")
        print(f"  JSON: {kb_file}")
        print(f"  Text summary: {text_file}")

        if args.enhance:
            print("\nApplying advanced NLP processing...")
            processor = TextProcessor()
            enhanced_kb = processor.process_knowledge_base(knowledge_base)
            enhanced_file = processor.save_enhanced_kb(enhanced_kb, args.output_dir)

            print(f"Enhanced knowledge base created: {enhanced_file}")

            # Display statistics
            stats = enhanced_kb.statistics
            print("\nStatistics:")
            print(f"  Pages processed: {stats['total_processed_pages']}")
            print(f"  Total sentences: {stats['total_sentences']}")
            print(f"  Avg readability: {stats['avg_readability_score']:.1f}")
            print(f"  Unique keywords: {stats['unique_keywords']}")

        print(f"\nKnowledge base saved to: {args.output_dir}/")
        print("You can now search this knowledge base or use it for your applications!")

    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def perform_search(kb_file: str, query: str):
    """Search an existing knowledge base"""
    if not os.path.exists(kb_file):
        print(f"Error: Knowledge base file not found: {kb_file}")
        sys.exit(1)

    try:
        with open(kb_file, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        if "processed_content" in kb_data:
            enhanced_kb = EnhancedKnowledgeBase(**kb_data)
            processor = TextProcessor()
            results = processor.search_kb(enhanced_kb, query)
        else:
            results = []
            for i, page_data in enumerate(kb_data.get("scraped_pages", [])):
                content = page_data.get("text_content", "").lower()
                title = page_data.get("title", "").lower()
                url = page_data.get("url", "")

                score = 0
                query_lower = query.lower()

                if query_lower in title:
                    score += 3
                if query_lower in content:
                    score += 1

                if score > 0:
                    results.append((i, page_data, score))

            results.sort(key=lambda x: x[2], reverse=True)
            results = results[:10]

        if not results:
            print(f"No results found for query: '{query}'")
            return

        print(f"Search results for '{query}':")
        print(f"Found {len(results)} relevant pages\n")

        for i, (page_idx, page_data, score) in enumerate(results, 1):
            if isinstance(page_data, dict):
                # Basic KB result
                title = page_data.get("title", "Untitled")
                url = page_data.get("url", "")
                word_count = page_data.get("word_count", 0)
                preview = page_data.get("text_content", "")[:200] + "..."
            else:
                title = page_data.original_content.title
                url = page_data.original_content.url
                word_count = page_data.original_content.word_count
                preview = page_data.summary[:200] + "..."

            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   Words: {word_count}, Relevance: {score:.1f}")
            print(f"   Preview: {preview}\n")

    except Exception as e:
        print(f"Error during search: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()