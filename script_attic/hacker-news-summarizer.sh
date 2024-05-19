#!/usr/bin/env bash
# Provide a one-page summary of a Hacker News discussion
# from: Simon Willison
# https://github.com/simonw/llm/, together with the llm-perplexity plugin and the llm-gemini plugin

# Validate that the argument is an integer
if [[ ! $1 =~ ^[0-9]+$ ]]; then
  echo "Please provide a valid integer as the argument."
  exit 1
fi

# Make API call, parse and summarize the discussion
# Set default value for $2 if it's not provided
if [[ -z $2 ]]; then
  set -- "$1" "llama-3-70b-instruct"
fi

# Validate that the $2 argument is a string without blanks
if [[ $2 =~ \  ]]; then
  echo "Please provide a string without blanks as the second argument, or omit it entirely."
  exit 1
fi

MODEL=$2
echo using $MODEL

curl -s "https://hn.algolia.com/api/v1/items/$1" | \
  jq -r 'recurse(.children[]) | .text' | \
  llm -m $MODEL 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'

#  llm -m gemini-pro-latest 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
#  llm -m mixtral-8x7b-instruct 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
#  llm -m llama-3-70b-instruct 'Summarize the themes of the opinions expressed here, including quotes where appropriate.'
