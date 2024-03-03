<!-- markdownlint-disable MD001 -->
# Hacker.news thread summarizer

README.md

## Description

Use OpenAPI Python API to summarize a Hacker-News forum thread.  The summary is written to a markdown file.  The markdown file is then read and printed to stdout.

## Run

#### Example

##### This writes to stdout

`./hn-thread2txt2chatgpt2md.py "https://news.ycombinator.com/item?id=39416436"  "why you're still single"   --api_key  $OPENAI_API_KEY  --intermediate_file "being_single.md"`

The `--intermediate_file` option writes to an intermediate file.  The file is then re-read and printed to stdout.  This is useful for debugging.

##### This writes to a file

`./hn-thread2txt2chatgpt2md.py "https://news.ycombinator.com/item?id=39416436"  "why you're still single"   --api_key  $OPENAI_API_KEY  --intermediate_file "being_single.md" > being_single.md`

After summarizing, you must customize the md file to your needs.  The script does not do that for you.
