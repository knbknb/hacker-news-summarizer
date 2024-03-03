#!/usr/bin/env python3
import os
import sys
import re
import subprocess
from urllib.parse import urlparse
import requests
import json
from dotenv import load_dotenv
import argparse

# import time # for sleep(), not used yet

# Load .env file with API keys and credentials
load_dotenv()
# Add your OpenAI API key here

def get_item_id(hnitem):
    parsed_url = urlparse(hnitem)
    query_params = dict(q.split('=') for q in parsed_url.query.split('&'))
    return query_params['id']

def download_hn_thread(hnitem, intermediate_file):
    subprocess.run(['lynx', '--dump', hnitem], stdout=open(intermediate_file, 'w'))

def preprocess(infile, intermediate_file2, final_file, topic):

    # remove HEADER 
    with open(infile, 'r') as f:
        lines = f.readlines()
    # add topic string to end of first line
    lines[0] = lines[0].strip() + f" {topic}\n"
    line_start = next(i for i, line in enumerate(lines) if "login" in line)
    lines = lines[line_start:]

# if intermediate file does not exist, preprocess it
    if os.path.isfile(intermediate_file2):
        # send to standard error
        print(f"File {infile} already exists, skipping preprocess.", file=sys.stderr)
    
    else:
        with open(intermediate_file2, 'w') as f:
            for line in lines:
                if not any(s in line for s in [']next', ']reply', '[s.gif']):
                    f.write(line)
        # POSTS: remove lines with "ago" 
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()

        with open(intermediate_file2, 'w') as f:
            for line in lines:
                f.write(re.sub(r'^(\s*\d+\.\w+) .+ ago .+$', r'\1', line))


    # FOOTER: remove lines starting with  "Guidelines...FAQ...Lists...API...Security" 
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()

        with open(intermediate_file2, 'w') as f:
            for line in lines:
                f.write(re.sub(r'^\s*\[\d+\].–.$', '', line))

        line_end = next(i for i, line in enumerate(lines) if re.search(r'\]Guidelines', line))


    # write to final file
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()

        with open(final_file, 'w') as f:
            for line in lines[:line_end]:
                f.write(line)

def chunk_text(text, chunk_size=10000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def chunks_data(chunks):
    chunks_data = []
    for chunk in chunks:
        chunks_data.append(set_data(config['model'], chunk, instruction))
    print(f"Number of data chunks: {len(chunks_data)}", file=sys.stderr)
    return chunks_data
    
def set_data(model, chunk, instruction):
    
    if config['model'] != 'gpt-3.5-turbo-16k':
        freq_penalty = 0.1
    else:
        freq_penalty = 0
    data = {"model": model,
        "messages": [
            {
                "role": "assistant",
                "content": instruction
            },
            {
                "role": "user",
                "content": chunk
            }
        ],
        "temperature": 0.1,
        "top_p": 1,
        "n": 1,
        "stream": False,
        "max_tokens": 2500,
        "presence_penalty": 0,
        "frequency_penalty": freq_penalty
    }
    return json.dumps(data)

def create_headers(api_key):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

## LLM : ChatGPT-3.5 API
def send_to_llm(config, headers, topic, chunks, first_response_flag):
    i = 1
    for chunk in chunks:
        print(f"chunk {i} of {len(chunks)} posted to {config['url']}, model {config['model']}]", file=sys.stderr)
        response = requests.post(config['url'], headers=headers, data=chunk)
        response_json = response.json()
        
        if response.status_code == 200:
            if first_response_flag:
                print(f"topic: {topic} | ... | ...", topic)
                first_response_flag = False
            print(response_json['choices'][0]['message']['content'])
        else:
            print(f"Error: {response_json['error']['message']}", file=sys.stderr)
        i += 1
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Hacker News threads.')
    parser.add_argument('--hnitem',  help='Hacker News item URL, or id, e.g. 39577113', required=True)
    parser.add_argument('--topic',   help='Topic of the discussion',  default="Hacker news thread")
    parser.add_argument('--intermediate_file', help='Output file',              default=None)
    parser.add_argument('--api_key', help='OPENAI_API_KEY. Put it in .env or set it on command line', 
                        required=False, default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument('--model',   help='Model to use for the LLM', default='gpt-3.5-turbo-16k')
    parser.add_argument('--url',     help='URL for the LLM API',      default='https://api.openai.com/v1/chat/completions')
    args = parser.parse_args()
    config = {
        'api_key': args.api_key,
        'model':   args.model,
        'url':     args.url,
        'hnitem':  args.hnitem,
        'topic' :  args.topic
    }

    intermediate_file = args.intermediate_file if args.intermediate_file else f"hacker-news-thread-{get_item_id(args.hnitem)}.txt"
    intermediate_file = os.path.join("output", intermediate_file)
    intermediate_file2 = f"{intermediate_file}-intermediate2.txt"
    final_file = f"{intermediate_file}-input-for-llm.txt"

    # if file does not exist, download it
    if not os.path.isfile(intermediate_file):
        download_hn_thread(args.hnitem, intermediate_file)
    else:
        print(f"File {intermediate_file} already exists, skipping download.", file=sys.stderr)
    preprocess(intermediate_file, intermediate_file2, final_file, args.topic)
    
    with open(final_file, 'r') as f:
        text = f.read()
    
    print(f"Read {final_file}...{len(text)}  chars read.", file=sys.stderr)
    instruction_file_path = "input/instruction.txt"
    with open(instruction_file_path, 'r') as f:
        instruction = f.read()



    topic_line = ": ".join(["The topic was", args.topic])
    instruction = "\n".join([topic_line,instruction])
    first_response_flag = True
    headers = create_headers(config['api_key'])
    chunks_rawtext = chunk_text(text)
    chunks_data = chunks_data(chunks_rawtext)
    send_to_llm(config, headers, topic_line, chunks_data, first_response_flag)