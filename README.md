<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Synopsis

Summarize ["Hacker News"](https://news.ycombinator.com/) (HN) comment threads using LLM APIs

```bash
# calls OpenAI gpt-4o model, (requires you to have Pro Account with OpenAI)
OPENAI_API_KEY=sk-0...           # your OpenAI API key, for better results
PERPLEXITY_API_KEY=pplx-1d...    # alternative API key, for experimenting
./HN-ThreadSummarizer.py --hnitem 39416436  --topic "Why You're Still Single" 

# processed, summarized output is written to a markdown file
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-4o.md
```

## Description

Use LLM Python APIs (e.g. OpenAI) to summarize (and flatten) a Hacker-News forum thread.

The summary is written to a markdown file, into the `final_output` directory. The progress of the summarization is printed to the console.

For more, read [USAGE.md](USAGE.md) and [EXAMPLE-OUTPUT.md](EXAMPLE-OUTPUT.md).
