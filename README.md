<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Synopsis

Summarize ["Hacker News"](https://news.ycombinator.com/) (HN) comment threads using LLM APIs

```bash
# Modern approach: OpenAI Responses API with structured outputs (GPT-4o, GPT-5)
OPENAI_API_KEY=sk-0...           # your OpenAI API key
./HN-ThreadSummarizer.py --hnitem 39416436 --topic "Why You're Still Single" --model gpt-5-mini

# Legacy approach: Completion API for Perplexity and other providers
PERPLEXITY_API_KEY=pplx-1d...    # alternative API key
./HN-ThreadSummarizer-completion-api.py --hnitem 39416436 --topic "Why You're Still Single" \
  --model sonar-pro --key $PERPLEXITY_API_KEY --url https://api.perplexity.ai/chat/completions

# Processed, summarized output is written to a markdown file
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-5-mini.md
```

## Description

Use LLM Python APIs (e.g. OpenAI, Perplexity) to summarize (and flatten) a Hacker-News forum thread.

**Two versions available:**

- **`HN-ThreadSummarizer.py`** - Modern implementation using OpenAI's Responses API with structured outputs (Pydantic models). Requires `openai>=1.40.0`. Best for GPT-4o, GPT-5 models. Features token-based chunking with tiktoken.

- **`HN-ThreadSummarizer-completion-api.py`** - Legacy implementation using the Chat Completions API. Works with Perplexity, OpenAI, and other OpenAI-compatible endpoints. Supports custom `--url` and `--key` parameters.

The summary is written to a markdown file in the `final_output` directory. Progress is printed to the console.

For more, read [USAGE.md](USAGE.md) and [EXAMPLE-OUTPUT.md](EXAMPLE-OUTPUT.md).
