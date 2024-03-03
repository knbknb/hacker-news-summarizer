<!-- markdownlint-disable MD001 -->
# Hacker.news thread summarizer

README.md

## Description

Use OpenAPI Python API to summarize a Hacker-News forum thread.  

The summary is written to a markdown file.  The markdown file is then read and printed to stdout. Use redirect to write to a file. Recommended: write into the `final_output` directory.

## Run

You must define an environment variable `OPENAI_API_KEY` with your OpenAI API key. Alternatively, you can put the key into an .env file.

```text
# .env-example
OPENAI_API_KEY="your_api_key"
```

#### Example

##### This writes to stdout

`./hn-thread2txt2chatgpt2md.py "https://news.ycombinator.com/item?id=39416436"  "why you're still single"  --intermediate_file "being_single.md"`

The `--intermediate_file` option writes to an intermediate file.  The file is then re-read, processed and printed to stdout.  This is useful for debugging.

##### This writes to a file

`./hn-thread2txt2chatgpt2md.py "https://news.ycombinator.com/item?id=39416436"  "why you're still single"  --api_key  $OPENAI_API_KEY --intermediate_file "being_single.md" > being_single.md`

Here no OPENAI_API_KEY is defined in the environment.  The OPENAI_API_KEY is passed as an argument.  The output is redirected to a file.

After summarizing, you must customize the md file to your needs.  The script does not do that for you.

## TODO

- [x] ~~Add requirements.txt~~
- [x] ~~Add .env-example~~
- [ ] Correct code that processes chunked OpenAI-API-output (Table header is written for each chunk)

### Directories created

The script creates subdirectories in the script directory.  
The subdirectories are named `./data`, `./final_output`, `./input`, `./output`, `./script_attic`.

### Files created

Lots of ,md files are created in the respective directories. PArtly for caching, partly for storing intermediate.

### Requirements

See `requirements.txt` file.  
Also, the lynx browser must be installed.

### License

BSD.

Use it as you wish.  No warranty.  No support.  No liability.  No nothing.  Just use it at your own risk.
