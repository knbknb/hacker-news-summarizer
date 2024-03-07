<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Description

Use OpenAPI Python API to summarize (and flatten) a Hacker-News forum thread.

The summary is written to a markdown file.  The markdown file is then read and printed to stdout. Use redirect to write to a file. Recommended: write into the `final_output` directory.

## Run

You must define an environment variable `OPENAI_API_KEY` with your OpenAI API key. Alternatively, you can put the key into an .env file.

```text
# .env-example
OPENAI_API_KEY="your_api_key"
```

You must have an account with OpenAI and have an API key.  The API key is free for a limited number of requests.  You can use the free tier to test the script.

#### Example

##### This writes to stdout

`./hn-thread2txt2chatgpt2md.py --hnitem "39416436"  --topic "why you're still single"  `

The script writes to an intermediate file in subdir `output/`.  That file is then re-read, processed and printed to stdout.  This is useful for getting immediate feedback, or for debugging.

##### This writes to a file

`./hn-thread2txt2chatgpt2md.py --hnitem "https://news.ycombinator.com/item?id=39416436"  --topic "why you're still single"  --api_key  $OPENAI_API_KEY > final_output/being_single.md`

Here no OPENAI_API_KEY is defined in the environment.  The OPENAI_API_KEY is passed as an argument.  The output is redirected to a file.

After summarizing, you must customize the `.md` file to your needs by hand. It might have a few formatting glitches. The script does not fix those for you.

But during fixing you start to read the summarized comments and get a better understanding of the thread.

##### This is the shortest version

Works provided you have the environment variable `OPENAI_API_KEY` defined properly.

```bash
TOPIC="why you're still single"
./hn-thread2txt2chatgpt2md.py --hnitem "39416436"  --topic "$TOPIC" > final_output/$TOPIC.md
```

## TODO

- [x] ~~Add requirements.txt~~
- [x] ~~Add .env-example~~
- [ ] Correct code that processes chunked OpenAI-API-output (Table header is written for each chunk)
- [ ] Use `textwrap` package to wrap long lines in the markdown file, do more intelligent line breaks and chunking
- [ ] Add an explanation of installation and 1 run example to an INSTALL.md or EXAMPLE.md file

### Directories created

The script creates subdirectories in the script directory.  
The subdirectories are named `./data`, `./final_output`, `./input`, `./output`, `./script_attic`.

### Files created

Lots of .md files are created in the respective directories. Partly for caching, partly for storing intermediate files.

### Requirements

See `requirements.txt` file.  
You can install packages mentioned in the requirements with `pip install -r requirements.txt`.

### License

BSD.

Use it as you wish.  No warranty.  No support.  No liability.  No nothing.  Just use it at your own risk.
