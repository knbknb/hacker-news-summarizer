#!/usr/bin/env bash
# Provide one-by-one summaries of relevant posts from Hacker News discussion
# Using local HN-ThreadSummarizer.py script, calling OpenAI 'gpt-4o-mini' model.
# by Knut Behrends, Oct 2024

# This script does not load any API keys or secrets. 
# ./HN-ThreadSummarizer.py does load those from .env file.

# Most of this script is Error checking: arguments, the existence of the script, the default topic, network issues
# The actual call to the Python script is at the end.
source $HOME/.virtualenvs/openai-api-v1/bin/activate

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <hn_id> [--topic <topic>] [--model <model>] [--key <api_key>]"
    exit 1
fi

if [[ ! $1 =~ ^[0-9]+$ ]]; then
    echo "Please provide a valid integer (the HN thread number) as the first argument."
    exit 1
fi

HN_ITEM_ID="$1"
shift

HN_SCRIPTS_PATH=$(pwd)
HN_SCRIPT_NAME="./HN-ThreadSummarizer.py"
DEFAULT_MODEL="gpt-4o-mini"
#DEFAULT_MODEL="gpt-5-mini"

TOPIC_ARG=""
MODEL_ARG="$DEFAULT_MODEL"
KEY_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --topic)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --topic requires a value."
                exit 1
            fi
            TOPIC_ARG="$2"
            shift 2
            ;;
        --model)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --model requires a value."
                exit 1
            fi
            MODEL_ARG="$2"
            shift 2
            ;;
        --key)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --key requires a value."
                exit 1
            fi
            KEY_ARG="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            if [[ -z "$TOPIC_ARG" ]]; then
                TOPIC_ARG="$1"
                shift 1
            else
                echo "Unknown argument: $1"
                exit 1
            fi
            ;;
    esac
done

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
if [ -z "$TOPIC_ARG" ]; then
    default_topic=$(python3 -c "import sys, requests, json; response = requests.get(f'https://hn.algolia.com/api/v1/items/{sys.argv[1]}'); print(json.loads(response.text).get('title', ''))" "$HN_ITEM_ID")
    # If any of this fails, cannot continue
    if [ $? -ne 0 ] || [ -z "$default_topic" ]; then
        echo "Error: Unable to retrieve the default topic. Network issue or invalid HN item."
        exit 1
    fi

    read -p "No topic provided. Do you want to use the default topic '$default_topic'? (y/n): " use_default
    if [ "$use_default" = "y" ]; then
        topic="$default_topic"
    else
        read -p "Please enter a topic description: " topic
    fi
else
    topic="$TOPIC_ARG"
fi
# Run the HN-ThreadSummarizer.py script
cmd=("./HN-ThreadSummarizer.py" --hnitem "$HN_ITEM_ID" --model "$MODEL_ARG" --topic "$topic")
if [[ -n "$KEY_ARG" ]]; then
    cmd+=(--key "$KEY_ARG")
fi

"${cmd[@]}"
# --url "https://api.perplexity.ai/chat/completions"

# At the end, run this script to show alternative models:
echo ""
echo "# ---------------------------------"
echo "# Alternative models, besides 'gpt-4o', '4o': (First run 'llm models to list names of available models)"
llm models
echo "# ---------------------------------"
echo "# (Also run 'llm plugins | jq .[].name' to list installed llm plugins), and check keys with 'llm keys'"
