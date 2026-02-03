<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Beautiful_Soup4-4.14+-green?style=for-the-badge" alt="Beautiful Soup" />
  <img src="https://img.shields.io/badge/NLTK-3.8+-blue?style=for-the-badge" alt="NLTK" />
  <img src="https://img.shields.io/badge/lxml-6.0+-orange?style=for-the-badge" alt="lxml" />
  <img src="https://img.shields.io/badge/requests-2.32+-red?style=for-the-badge" alt="requests" />
</p>

# Website Knowledge Base Scraper

Scrape website **text only** (no images or video) into a knowledge base. Crawls same domain and subdomains, outputs JSON and optional NLP-enhanced data.

## Overview

This tool uses **Beautiful Soup** to parse HTML and extract all text content from a site. It follows links on the same domain (and subdomains, e.g. `help.example.com`), saves structured data (titles, headings, paragraphs, metadata) to JSON, and can optionally run **NLTK**-based processing for keywords, summaries, and search. **lxml** is used as the parser; **requests** handles HTTP. No images or video are downloaded.


## Prerequisites

- **Python** 3.12 or newer  
- **uv** — install: `pip install uv` or see [docs.uv.dev](https://docs.uv.dev)


## How to run

**1. Clone and enter the project**

```bash
cd webscraping
```

**2. Create environment and install dependencies**

```bash
uv sync
```

This creates a `.venv` and installs dependencies. Activate it if you want to run `python` directly:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (cmd):** `.venv\Scripts\activate.bat`
- **macOS/Linux:** `source .venv/bin/activate`

**3. Scrape a site**

```bash
uv run python main.py <URL>
```

**Example**

| Command / Option | Description | Default |
|------------------|-------------|---------|
| `--max-pages` | Maximum pages to scrape | 50 |
| `--all` | Scrape all pages (no limit) | off |
| `--delay` | Seconds between requests | 1.0 |
| `--output-dir` | Output directory for KB files | `knowledge_base` |
| `--enhance` | NLP processing (keywords, summaries) | off |
| `--verbose` | Show full tracebacks on errors | off |
| `uv run python main.py https://example.com` | Basic scrape (up to 50 pages) | — |
| `uv run python main.py https://example.com --all` | Scrape all pages on the site | — |
| `uv run python main.py https://example.com --max-pages 100 --delay 2.0` | Up to 100 pages, 2s delay between requests | — |
| `uv run python main.py https://example.com --output-dir my_kb --enhance` | Save to `my_kb/` with NLP enhancement | — |
| `uv run python main.py https://example.com --search "query" --kb-file path/to/kb.json` | Search an existing knowledge base | — |

Output is written to the `knowledge_base/` directory (or `--output-dir` if set).


## License

This project is provided as-is. Use and modify it as you like. If you distribute it, keep attribution to the original authors.


## Contributing

Contributions are welcome. Please open an issue to discuss larger changes, or send a pull request with clear description of the change. Ensure the project still runs with `uv sync` and `uv run python main.py <url>` before submitting.
