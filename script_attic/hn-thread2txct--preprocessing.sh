#!/usr/bin/env bash
#example: ./hn-thread2txct--preprocessing.sh https://news.ycombinator.com/item?id=37156101
hnitem=$1
outfile=$2
itemid=$(echo $hnitem | cut -d= -f 2)

if [ -z "$hnitem" ]
then
      echo "Usage: $0 <hacker-news-item-url> <outfile>"
      echo "e.g. $0 hnitem=https://news.ycombinator.com/item?id=37156101 hacker-news-thread.txt"
      exit 0
fi
if [ -z "$outfile" ]
then
      outfile="hacker-news-thread-$itemid.txt"      
fi

# html to text
lynx --dump $hnitem > $outfile
line_start=$(grep -n "________________________________________" $outfile | cut -d: -f 1 | tail -1)
#cutoff header: first 30 lines
outfile_intermediate="${outfile}-intermediate.txt"
tail -n +$line_start "$outfile"  | grep -v "\]next\|\]reply\|\[s.gif" > ${outfile_intermediate}
perl -pi.bak -E "s/^(\s*.\d+.\w+) .+ ago .+\$/\$1/g" $outfile_intermediate
perl -pi.bak -E "s/^\s*\[\d+\].–.\$//g" $outfile_intermediate
# find end of thread in lynx output. 
# After the last line of the thread comes a generic footer, find line number of that line.
# The line number is used to cut the file.
line_end=$(grep -nP "Guidelines.+FAQ.+Lists|.+API.+Security" ${outfile_intermediate}  | cut -d: -f 1)
outfile_final="${outfile}-for-chatgpt.txt"
head -$line_end "${outfile_intermediate}" > $outfile_final

firefox "file:///$(pwd)/${outfile_final}"

###
# TODO:
# - [x] add a way to specify the input file via command line
# - [x] add a way to specify the output file via command line
# - [ ] chunk the text into 14k chunks
# - [ ] add a way to specify the chunk size via command line
# - [ ] submit the chunks to ChatGPT API via curl or newman
# - [ ] add a way to specify the ChatGPT API endpoint via command line
# - [ ] add a way to specify the ChatGPT API key via command line or via env var
# - [ ] concatenate the responses from ChatGPT API into a single file, 
#         - markdown format
#         - csv format
#         - see OpenAI playgroud for saved prompt presets https://beta.openai.com/playground/p/1d2f1e8f-8b7d-4f1f-8c1d-2f0b2b2a3a3b
#         - set "system" field to value from prompt preset
#         - set "message" field to chunk of text from lynx output
# - [ ] convert markdown to html 
# - [ ] open html in browser