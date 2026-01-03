Legacy Scripts


- **`HN-ThreadSummarizer-completion-api.py`** - Legacy implementation using the Chat Completions API. Works with Perplexity, OpenAI, and other OpenAI-compatible endpoints. Supports custom `--url` and `--key` parameters.


```bash
# Legacy approach: Completion API for Perplexity and other providers
PERPLEXITY_API_KEY=pplx-1d...    # alternative API key
./HN-ThreadSummarizer-completion-api.py --hnitem 39416436 --topic "Why You're Still Single" \
  --model sonar-pro --key $PERPLEXITY_API_KEY --url https://api.perplexity.ai/chat/completions

```