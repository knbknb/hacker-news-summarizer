<!-- markdownlint-disable MD001 -->
# Hacker-News Thread Summarizer

USAGE.md

## Synopsis

Summarize ["HN threads"](https://news.ycombinator.com/) using the OpenAI Responses API (with structured outputs) or the legacy Completions API (for Perplexity and other providers).

```bash
# Modern: OpenAI Responses API with structured outputs (requires openai>=1.40.0)
./HN-ThreadSummarizer.py --hnitem 39416436 --topic "Why You're Still Single" --model gpt-5-mini

# Legacy: Completions API for Perplexity and other OpenAI-compatible endpoints
./HN-ThreadSummarizer-completion-api.py --hnitem 39416436 --topic "Why You're Still Single" \
  --model sonar-pro --key $PERPLEXITY_API_KEY --url https://api.perplexity.ai/chat/completions

# Shell script wrappers:
./hn-summary-knb-gpt.sh 39416436 --topic "Why You're Still Single" --model gpt-5-mini
./hn-summary-knb-perplexity.sh 39416436  # Interactive topic selection

# Expected output on the console
[tokenizer] chunk 1: 14325 tokens (58596 chars) / limit 12500
Number of data chunks: 1
chunk_num 1 of 1 processing with model gpt-5-mini

# Processed, summarized output written to:
final_output/Why-You-re-Still-Single-https-news-ycombinator-com-item-id-39416436-gpt-5-mini.md
```

## Description

Use OpenAI Python APIs to summarize (and flatten) a Hacker-News forum thread.

### Two Script Versions

#### `HN-ThreadSummarizer.py` (Modern - Structured Outputs)

- **API**: OpenAI Responses API
- **Features**:
  - Structured outputs using Pydantic models (`ThreadSummaryResponse`)
  - Token-based chunking with tiktoken
  - Automatic version detection (requires `openai>=1.40.0`)
  - Supports GPT-4o, GPT-5 models
- **Shell wrapper**: `hn-summary-knb-gpt.sh`
- **Usage**: Best for modern OpenAI models with structured output support

#### `HN-ThreadSummarizer-completion-api.py` (Legacy - Compatible)

- **API**: Chat Completions API (OpenAI-compatible)
- **Features**:
  - Direct HTTP requests to `/chat/completions` endpoint
  - Supports custom `--url` and `--key` parameters
  - Character-based chunking
  - Works with Perplexity, OpenAI, and other compatible providers
- **Shell wrapper**: `hn-summary-knb-perplexity.sh`
- **Usage**: Best for Perplexity API and other OpenAI-compatible services

### Recent Changes (Nov 2025)

- **Structured Outputs**: Migrated from Completions API to Responses API with Pydantic models for reliable table formatting
- **Token-based Chunking**: Replaced character-based with tiktoken for accurate token counting
- **Version Detection**: Automatic check for `openai>=1.40.0` with clear error messages
- **Shell Script Updates**: Added support for `--topic`, `--model`, and `--key` flags
- **Dual Script Approach**: Separated modern (Responses API) and legacy (Completions API) versions

The summary is written to a markdown file in the `final_output` directory. Progress is printed to the console.

## Run

You must define an environment variable `OPENAI_API_KEY` with your OpenAI API key. Alternatively, you can put the key into an `.env` file.

```text
# .env-example
OPENAI_API_KEY="your_api_key"
```

You must have an account with OpenAI and have an API key.  OpenAI API access was free for a limited number of requests previously, by that seems to have been discontinued.

(To use the OpenAI API, users now need to add a payment method and purchase credits . The minimum amount to start using the API was once \$5.00, but that may have changed. Check the [OpenAI platform page](https://platform.openai.com/) for current details.)

#### Using Shell Script Wrappers

Two convenience scripts are provided:

**For OpenAI (Structured Outputs):**

```bash
# Uses HN-ThreadSummarizer.py with Responses API
./hn-summary-knb-gpt.sh 39416436 --topic "career advice" --model gpt-5-mini

# Interactive topic selection (fetches HN thread title)
./hn-summary-knb-gpt.sh 39416436

# Override API key
./hn-summary-knb-gpt.sh 39416436 --topic "linux" --key sk-proj-...
```

**For Perplexity (Completions API):**

```bash
# Uses HN-ThreadSummarizer-completion-api.py
# Automatically uses PERPLEXITY_API_KEY from .env
./hn-summary-knb-perplexity.sh 39416436

# Tests multiple models: sonar, sonar-pro
./hn-summary-knb-perplexity.sh 39416436 --topic "AI discussion"
```

#### Example runs (Direct Python Scripts)

(See also [EXAMPLE-OUTPUT.md](EXAMPLE-OUTPUT.md))

##### Using OpenAI Directly

Here an OPENAI_API_KEY _was_ defined before, as a shell command, such that a valid environment variable exists for the script to use.

```bash
# Modern Responses API version (requires openai>=1.40.0)
./HN-ThreadSummarizer.py --hnitem 39416436 --topic "why you're still single" --model gpt-5-mini

# With explicit API key
./HN-ThreadSummarizer.py --hnitem 39416436 --topic "why you're still single" \
  --model gpt-4o --key $OPENAI_API_KEY
```

The script writes intermediate files into subdir `output/`. Those files are then re-read and processed by the script. This is useful for getting immediate feedback or for debugging.

For setup and installation details see [INSTALLATION.md](INSTALLATION.md).

##### Perplexity API (Legacy Completions)

Call [Perplexity API](https://docs.perplexity.ai/getting-started/overview) using the completion API version:

```bash
TOPIC="why you're still single"
PERPLEXITY_API_KEY=pplx-1d...    # from .env or environment

# Using completion API script with custom URL
./HN-ThreadSummarizer-completion-api.py --hnitem 39416436 --topic "$TOPIC" \
  --model sonar-pro --key $PERPLEXITY_API_KEY \
  --url https://api.perplexity.ai/chat/completions
```

For Perplexity API, try these values for the `--model` argument:

```text
sonar-deep-research          128k   Chat Completion
sonar-reasoning-pro          128k   Chat Completion
sonar-reasoning              128k   Chat Completion
sonar-pro                    200k   Chat Completion
sonar                        128k   Chat Completion
r1-1776                      128k   Chat Completion
```

##### Previous models

~~llama-3.1-8b-instruct   # fast but degrades into repetitions, and refusals to answer~~  
~~llama-3.1-70b-instruct  # slower, also degrades into repetitions, and refusals to answer~~  
~~mixtral-8x7b-instruct   # good quality with small chunks~~  

~~llama-3-8b-instruct~~  
~~llama-3-70b-instruct~~  

... and more ... change the model to experiment.

### Recommended

##### llm CLI tool

Also install and run Simon Willison's great [`llm` CLI tool](https://llm.datasette.io/), [for HN topic thread summarization](https://til.simonwillison.net/llms/claude-hacker-news-themes). `llm` is Python-based and can be installed with `pip install llm` (or any other Python package manager).

A shellscript [`hn-summary-simonw.sh`](hn-summary-simonw.sh) wrapping the `llm` command is provided in the root directory of this repo.

Script `hn-summary-simonw.sh` works similarly to script `HN-ThreadSummarizer.py`, but provides a much more compact view of the HN Thread output.  `llm` tries to find high-level _conversation themes_ and summarizes postings in a readable way.

##### Hackerstrat Custom GPT

If you have a ChatCPT Plus account, try some Custom GPTs for HN, e.g. [hackerstract](https://chatgpt.com/g/g-67ae411d65f8819183e910d64e5c4a01-hackerstract) Summarizer. It has conversation starters, and very good summarization capabilities.

### TODO

- [x] ~~Add requirements.txt~~
- [x] ~~Add .env-example~~
- [x] ~~Correct code that processes chunked OpenAI-API-output (Table header is written for each chunk)~~ Better prompt and model gpt-4o does a good job
- [x] ~~Use `textwrap` package to wrap long lines in the markdown file, do more intelligent line breaks and chunking~~ Not needed, found workaround with better table formatting
- [x] ~~Add an explanation of installation and 1 run example to an USAGE.md or EXAMPLE-OUTPUT.md file~~
- [x] Migrate to OpenAI Responses API with structured outputs (Pydantic models)
- [x] Implement token-based chunking with tiktoken
- [x] Add version detection for openai>=1.40.0
- [x] Create legacy completion API version for Perplexity compatibility
- [x] Update shell scripts to support --topic, --model, --key flags
- [ ] Experiment with various API parameters (chunk size, model, temperature, custom instructions etc.)
- [ ] Add an analysis and comparison of the model outputs
- [ ] (misc) Fetch correct title of HN Posting (can get updated by HN Moderators, even after days), and use that title as a better "slug" for the output file
- [ ] (idea): re-post the summarized comments back to the API, to clean up the markdown file.  
  (Leverage the ["Self-refine"](https://selfrefine.info/) pattern of LLM usage.)

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
