<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Synopsis

Summarize ["Hacker News"](https://news.ycombinator.com/) (HN) comment threads using OpenAI API

```bash
# calls OpenAI gpt-4o model, (requires you to have Pro Account with OpenAI)
./HN-ThreadSummarizer.py --hnitem 39416436  --topic "Why You're Still Single" 

# processed, summarized output is written to a markdown file
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-4o.md
```

## Description

Use OpenAPI Python API to summarize (and flatten) a Hacker-News forum thread.

The summary is written to a markdown file, into the `final_output` directory. The progress of the summarization is printed to the console.

For more, read [USAGE.md](USAGE.md).


