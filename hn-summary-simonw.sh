#!/usr/bin/env bash
# Provide a one-page summary of a Hacker News discussion
# https://til.simonwillison.net/llms/claude-hacker-news-themes
# by: Simon Willison, based on:
# https://github.com/simonw/llm/, 
# together with the llm-perplexity plugin and the llm-gemini plugin (by others)

# Validate that the first argument is an integer
if [[ ! $1 =~ ^[0-9]+$ ]]; then
  echo "Please provide a valid integer  (the HN thread number) as the first argument."
  exit 1
fi
# add a check that tests for cli tool llm being installed 
if ! command -v llm &> /dev/null
then
    echo "'llm' cli tool could not be found, please install it with 'pip install llm'."
    echo "See https://llm.datasette.io/en/stable/"
    exit
fi

id="$1"

# Parse the optional -m argument. 
# If not provided, use the default model to gemini-pro (has largest context window)
if [[ -z $2 ]]; then
  set -- "$1" "gemini-pro"
fi
model=$2
echo using $model
# Make API call, parse and summarize the discussion
curl -s "https://hn.algolia.com/api/v1/items/$id" | \
  jq -r 'recurse(.children[]) | .author + ": " + .text' | \
  llm -m "$model" 'Summarize the themes of the opinions expressed here.
  Write a short paragraph with details about each theme of the discussion.
  For each theme t, pick a number n(t) randomly from the set 0,1,2,3, and then  include n(t) direct "quotations" (with author attribution) where appropriate.
  You MUST quote directly from users when crediting them, with double quotes.
  Tramslate HTML entities to their equivalent unicode characters if possible. Output markdown. Go long.'
#  llm -m gemini-pro 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
#  llm -m mixtral-8x7b-instruct 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
#  llm -m llama-3-70b-instruct 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
