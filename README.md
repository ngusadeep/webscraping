<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Beautiful_Soup4-4.14+-green?style=for-the-badge" alt="Beautiful Soup" />
  <img src="https://img.shields.io/badge/NLTK-3.8+-blue?style=for-the-badge" alt="NLTK" />
  <img src="https://img.shields.io/badge/lxml-6.0+-orange?style=for-the-badge" alt="lxml" />
  <img src="https://img.shields.io/badge/requests-2.32+-red?style=for-the-badge" alt="requests" />
</p>

# Website Knowledge Base Scraper

Scrape site **text only** into a JSON knowledge base. Same domain + subdomains; optional NLP (keywords, summaries). Beautiful Soup + NLTK + lxml.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.uv.dev) — `pip install uv`

## How to run

```bash
uv sync
uv run python main.py <URL>
```

| Command / Option | Description | Default |
|------------------|-------------|---------|
| `--max-pages` | Max pages to scrape | 50 |
| `--all` | Scrape all pages | off |
| `--delay` | Seconds between requests | 1.0 |
| `--output-dir` | Output directory | `knowledge_base` |
| `--enhance` | NLP (keywords, summaries) | off |
| `--verbose` | Full tracebacks | off |
| `uv run python main.py https://example.com` | Basic scrape | — |
| `uv run python main.py https://example.com --all` | All pages | — |
| `uv run python main.py https://example.com --enhance` | With NLP | — |

## License

[MIT](LICENSE)

## Contributing

Open an issue or PR. Run `uv sync` and `uv run python main.py <url>` before submitting.
