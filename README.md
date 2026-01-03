<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Synopsis

Summarize ["Hacker News"](https://news.ycombinator.com/) (HN) comment threads using LLM APIs

```bash
# OpenAI Responses API with structured outputs (GPT-4o, GPT-5 and higher)
OPENAI_API_KEY=sk-0...           # your OpenAI API key
./HN-ThreadSummarizer.py --hnitem 39416436 \
  --topic "Why You're Still Single" \
  --model gpt-5-mini
```

Processed, summarized output is written to a markdown file
in the `final_output` directory, e.g.:

```
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-5-mini.md
```

## Description

Use LLM Python APIs (e.g. OpenAI, Perplexity) to summarize (and flatten) a Hacker-News forum thread.

The main script is:

- **`HN-ThreadSummarizer.py`** - Modern implementation using OpenAI's Responses API with structured outputs (Pydantic models). Requires `openai>=1.40.0`. Best for GPT-4o, GPT-5 models. Features token-based chunking with tiktoken.

The summary is written to a markdown file in the `final_output` directory. Progress is printed to the console.

For more, read [INSTALLATION.md](INSTALLATION.md), [USAGE.md](USAGE.md) and [EXAMPLE-OUTPUT.md](EXAMPLE-OUTPUT.md), or try code from simonw's [HN Thread Summarizer](https://til.simonwillison.net/llms/claude-hacker-news-themes) blog post.
