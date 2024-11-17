#!/usr/bin/env bash
# Provide one-by-one summaries of relevant posts from Hacker News discussion
# Using local HN-ThreadSummarizer.py script, calling Perplexity's models at their API.
# by Knut Behrends, Oct 2024

# This script loads the PERPLEXITY API keys from .env file 

# Most of this script is Error checking: arguments, the existence of the script, the default topic, network issues
# The actual call to the Python script is at the end.

if [[ ! $1 =~ ^[0-9]+$ ]]; then
  echo "Please provide a valid integer (the HN thread number) as the first argument."
  exit 1
fi

HN_SCRIPTS_PATH=$(pwd)
HN_SCRIPT_NAME="./HN-ThreadSummarizer.py"
DEFAULT_MODEL="llama-3.1-sonar-huge-128k-online" # llama3.1-405b-instruct
# All models, Okt. 2024:
MODELS="llama-3.1-sonar-small-128k-online llama-3.1-sonar-large-128k-online llama-3.1-sonar-huge-128k-online \
llama-3.1-sonar-small-128k-chat  llama-3.1-sonar-large-128k-chat  \
llama-3.1-8b-instruct llama-3.1-70b-instruct"
# reliable models for text summarization:
#MODELS="llama-3.1-8b-instruct llama-3.1-sonar-small-128k-chat"
MODELS=" llama-3.1-sonar-large-128k-online"
if [[ ! -f "$HN_SCRIPT_NAME" ]];
then
    echo "'$HN_SCRIPT_NAME' script could not be found."
    echo " I've looked in the current directory,"
    echo "      '$HN_SCRIPTS_PATH'"
    echo "call: ./HN-ThreadSummarizer.py --hnitem "$1" --model "$DEFAULT_MODEL" --topic "$topic""
    echo "For Alternative models: (besides 'gpt-4o')"
    echo "call: ./script_attic/show-perplexity-models.py"
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

# HN-ThreadSummarizer.py script defaults to OPENAI API, so here we override it:
PERP_URL="https://api.perplexity.ai/chat/completions"
PERP_KEY=$(grep PERPLEXITY_API_KEY .env | cut -d '=' -f 2)

# Iterate over each model and run the script
for model in $MODELS; do
    echo ""
    echo "####################  Running Perplexity model: '$model'"
    ./HN-ThreadSummarizer.py --hnitem "$1" --model "$model" --topic "$topic" \
      --url "$PERP_URL" --key "$PERP_KEY"
done
echo "run: "
cat <<'EOT'
## delete empty lines in the output file:
perl -ni -e 'print unless /^\s*$/' final_output/outfile
sed -i '/^\s*$/d' final_output/outfile

# add a table header:
perl  -pi -e 'if ($. < 10 && /^.+URLs\s+\|/){ $_ .= "\|------\|-------\|--------\|\n";$_ = "\n" . $_}' final_output/outfile 

# best display outfiles with glow or bat:
< final_output/outfile bat -l markdown
< final_output/outfile glow
EOT

# At the end, run this script to show alternative models:
#echo ""
#echo "Alternative models: (besides '$DEFAULT_MODEL')"
#./script_attic/show-perplexity-models.py
