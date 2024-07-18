<!-- markdownlint-disable MD001 -->
# Hacker-News thread summarizer

README.md

## Synopsis

Summarize ["HN threads "](https://news.ycombinator.com/) using OpenAI API or Perplexity API.

```bash
# calls OpenAI gpt-4o model, (requires you to have Pro Account with OpenAI)
./HN-ThreadSummarizer.py --hnitem 39416436  --topic "Why You're Still Single" 

# expected output on the console
Read output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-4o--input-for-llm.txt...:  28525  chars read.
Number of data chunks: 3
chunk 1 of 3 posted to https://api.openai.com/v1/chat/completions, model gpt-4o, topic # HN Topic: [Why You're Still Single](https://
...

# processed, summarized output is written to a markdown file
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-4o.md
```

## Description

Use OpenAPI Python API to summarize (and flatten) a Hacker-News forum thread.

The summary is written to a markdown file, into the `final_output` directory. The progress of the summarization is printed to the console.

## Run

You must define an environment variable `OPENAI_API_KEY` with your OpenAI API key. Alternatively, you can put the key into an `.env` file.

```text
# .env-example
OPENAI_API_KEY="your_api_key"
```

You must have an account with OpenAI and have an API key.  OpenAI API access was free for a limited number of requests previously, by that seems to have been discontinued.

(To use the OpenAI API, users now need to add a payment method and purchase credits . The minimum amount to start using the API is typically \$5.00.)

#### Example

##### This writes to a file

Here no OPENAI_API_KEY was defined in the environment.

`./HN-ThreadSummarizer.py --hnitem "39416436"  --topic "why you're still single"  `

The script writes intermediate files into subdir `output/`.  Those files are then re-read, processed by the script.  
This is useful for getting immediate feedback, or for debugging.

`./hn-thread2txt2chatgpt2md.py --hnitem "https://news.ycombinator.com/item?id=39416436"  --topic "why you're still single"  --api_key  $OPENAI_API_KEY`

Here no OPENAI_API_KEY is pre-defined in the environment. Hence the OPENAI_API_KEY needs to passed as a command-line argument.  

After summarizing, you it recommended to fine-tune the `.md` output file to your needs, by hand. That file might have a few formatting glitches. The script does not fix those for you.

But during fixing you start to read the summarized comments and get a better understanding of the HN thread.

##### This is the shortest version

Works provided you have the environment variable `OPENAI_API_KEY` defined properly.

```bash
TOPIC="why you're still single"
./HN-ThreadSummarizer.py --hnitem "39416436"  --topic "$TOPIC" 
```

Call [Perplexity API](https://docs.perplexity.ai/docs/model-cards) instead (provided you have an API key for it) - for checking out the differences in summarization quality between OpenAI and the models offered by Perplexity.

```bash
TOPIC="why you're still single"
# 3 more arguments are needed: --model, --api_key, --url
./HN-ThreadSummarizer.py --hnitem 39416436  --topic "Why You're Still Single" --model mixtral-8x7b-instruct  --api_key $PERPLEXITY_API_KEY --url https://api.perplexity.ai/chat/completions
```

### Recommended

Also install and run Simon Willison's [`llm` CLI tool](https://til.simonwillison.net/llms/claude-hacker-news-themes). It is Python-based and can be installed with `pip install llm`. It is a great tool to get a better understanding of the OpenAI API output.

A shellscript [`hn-summary-simonw.sh`](hn-summary-simonw.sh) wrapping the `llm` command is provided in the root directory of this repo.

Script `hn-summary-simonw.sh` works similarly to script `HN-ThreadSummarizer.py`, but provides a much more compact view of the HN Thread output. Well-summarized _conversation themes_ are returned in a more readable way.


### TODO

- [x] ~~Add requirements.txt~~
- [x] ~~Add .env-example~~
- [ ] Fetch correct title of HN Posting (can get updated by HN Moderators, even after days)
- [x] ~~Correct code that processes chunked OpenAI-API-output (Table header is written for each chunk)~~ Better prompt and model gpt-4o does a good job
- [x] ~~Use `textwrap` package to wrap long lines in the markdown file, do more intelligent line breaks and chunking~~ Not needed, found workaround with better table formatting
- [ ] Add an explanation of installation and 1 run example to an INSTALL.md or EXAMPLE.md file

### Directories created

The script creates subdirectories in the script directory.  
The subdirectories are named `./data`, `./final_output`, `./input`, `./output`, `./script_attic`.

### Files created

Lots of .md files are created in the respective directories. Partly for caching, partly for storing intermediate files.

You can delete files in the `./output` directory after the script has finished.  It is only used for intermediate files.

### Requirements

See `requirements.txt` file.  
You can install packages mentioned in the requirements with `pip install -r requirements.txt`.

### License

BSD.

Use it as you wish.  No warranty.  No support.  No liability.  No nothing.  Just use it at your own risk.
