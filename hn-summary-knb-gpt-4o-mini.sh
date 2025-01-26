#!/usr/bin/env bash
# Provide one-by-one summaries of relevant posts from Hacker News discussion
# Using local HN-ThreadSummarizer.py script, calling OpenAI 'gpt-4o' model.
# by Knut Behrends, Oct 2024

# This script does not load any API keys or secrets. 
# ./HN-ThreadSummarizer.py does load those from .env file.

# Most of this script is Error checking: arguments, the existence of the script, the default topic, network issues
# The actual call to the Python script is at the end.

if [[ ! $1 =~ ^[0-9]+$ ]]; then
  echo "Please provide a valid integer (the HN thread number) as the first argument."
  exit 1
fi

HN_SCRIPTS_PATH=$(pwd)
HN_SCRIPT_NAME="./HN-ThreadSummarizer.py"
DEFAULT_MODEL="gpt-4o-mini"

if [[ ! -f "$HN_SCRIPT_NAME" ]];
then
    echo "'$HN_SCRIPT_NAME' script could not be found."
    echo " I've looked in the current directory,"
    echo "      '$HN_SCRIPTS_PATH'"
    echo "call: ./HN-ThreadSummarizer.py --hnitem "$1" --model "$DEFAULT_MODEL" --topic "$topic""
    exit
fi

# Propose the current title of the HN discussion as default topic. 
# - use python3 oneliner to get the title
# - curl/jq command commented out, as fallback alternative

#default_topic=$(curl -s "https://hn.algolia.com/api/v1/items/$1" | jq -r .title)
default_topic=$(python3 -c "import sys, requests, json; response = requests.get(f'https://hn.algolia.com/api/v1/items/{sys.argv[1]}'); print(json.loads(response.text).get('title', ''))" "$1")
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
./HN-ThreadSummarizer.py --hnitem "$1" --model "$DEFAULT_MODEL" --topic "$topic"
# --url "https://api.perplexity.ai/chat/completions"

# At the end, run this script to show alternative models:
echo ""
echo "# ---------------------------------"
echo "# Alternative models, besides 'gpt-4o', '4o': (Also run 'llm plugins | jq .[].name' to check versions)"
llm models
echo "# ---------------------------------"
echo "# (Also run 'llm plugins | jq .[].name' to check llm plugin availability), and check keys with 'llm keys'"