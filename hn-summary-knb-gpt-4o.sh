#!/usr/bin/env bash
# Provide a one-page summary of a Hacker News discussion
# using HN-ThreadSummarizer.py, 
# together with the llm-perplexity plugin and the llm-gemini plugin (by others)

# Validate that the first argument is an integer
if [[ ! $1 =~ ^[0-9]+$ ]]; then
  echo "Please provide a valid integer (the HN thread number) as the first argument."
  exit 1
fi
# add a check that tests for cli tool llm being installed 
HN_SCRIPTS_PATH=$(dirname $0)
HN_SCRIPT_NAME="./HN-ThreadSummarizer.py"

if [[ ! -f "$HN_SCRIPT_NAME" ]];
then
    echo "'$HN_SCRIPTS_PATH' script could not be found."
    echo " (I've looked in the current directory. '$HN_SCRIPTS_PATH')."
    exit
fi

# Propose the current title of the HN discussion as default topic
default_topic=$(curl -s "https://hn.algolia.com/api/v1/items/$1" | jq -r .title)

# If any of this fails, cannot continue
if [ $? -ne 0 ] || [ -z "$default_topic" ]; then
    echo "Error: Unable to retrieve the default topic. Network issue or invalid HN item."
    exit 1
fi

# Check if a topic argument is provided by the user. If not, ask for it.
if [ -z "$2" ]; then
    read -p "No topic provided. Do you want to use the default topic '$default_topic'? (y/n): " use_default
    if [ "$use_default" = "y" ]; then
        topic="$default_topic"
    else
        read -p "Please enter a topic description: " topic
    fi
else
    topic="$2"
fi
# Run the HN-ThreadSummarizer.py script
./HN-ThreadSummarizer.py --hnitem "$1" --model "gpt-4o" --topic "$topic"
# --url "https://api.perplexity.ai/chat/completions"