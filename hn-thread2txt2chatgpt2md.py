#!/usr/bin/env python3
from datetime import datetime
import os
import sys
import re
#import subprocess
import html2text
from urllib.parse import urlparse
import requests
import json
from dotenv import load_dotenv
import argparse

# import time # for sleep(), not used yet

# Load .env file with API keys and credentials
load_dotenv()

def create_subdirectories():
        subdirectories = ['./data', './final_output', './input', './output', './script_attic']
        for directory in subdirectories:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.access(directory, os.W_OK):
                print(f"Warning: {directory} is not writable.", file=sys.stderr)

def check_hnitem(hnitem):
        '''If hnitem argument is just a multi-digit-number, prepend the HN URL'''
        
        if hnitem.isdigit() and len(hnitem) > 5:
            hnitem = f"https://news.ycombinator.com/item?id={hnitem}"
        return hnitem

def get_item_id(hnitem):
    '''Extract the Hacker-News item id from the URL'''
    parsed_url = urlparse(hnitem)
    query_params = dict(q.split('=') for q in parsed_url.query.split('&'))
    return query_params['id']

def download_hn_thread(hnitem, intermediate_file):
    response = requests.get(hnitem)
    response.raise_for_status()  # Raise an exception if the GET request failed
    raw_text = html2text.html2text(response.text)
    with open(intermediate_file, 'w') as f:
        f.write(raw_text)
    #with open(intermediate_file, 'w') as f:
    #    f.write(response.text)

def preprocess(infile, intermediate_file2, intermediate_file3, topic):
    '''Preprocess the Hacker News thread file to remove header and footer, 
        and to remove lines with "next", "reply", "[s.gif]" and "ago" strings.'''
    # remove HEADER / first lines until "login" is found
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
        # POSTS: remove lines with "next", "reply", "[s.gif]"
        with open(intermediate_file2, 'w') as f:
            for line in lines:
                if not any(s in line for s in ['(reply?', '(s.gif)', 'javascript:void']):
                    f.write(line)

        # POSTS: remove strings after "ago" 
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()
        with open(intermediate_file2, 'w') as f:
            for line in lines:
                f.write(re.sub(r'(\[\s*\d+ \w+ ago).+$', r'', line))


    # FOOTER: remove lines containing  "newsguidelines.html" and after
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()

        with open(intermediate_file2, 'w') as f:
            for line in lines:
                f.write(re.sub(r'^\s*\[\d+\].–.$', '', line))

        line_end = next(i for i, line in enumerate(lines) if re.search(r'newsguidelines\.html', line))


    # write to final file
        with open(intermediate_file2, 'r') as f:
            lines = f.readlines()

        with open(intermediate_file3, 'w') as f:
            for line in lines[:line_end]:
                f.write(line)

def chunk_text(text, chunk_size=10000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def chunk_data(chunks, instruction):
    chunks_data = []
    for chunk in chunks:
        chunks_data.append(set_data(config['model'], chunk, instruction))
    print(f"Number of data chunks: {len(chunks_data)}", file=sys.stderr)
    return chunks_data

def set_data(model, chunk, instruction, max_tokens=1024):
    '''perplexity sonar models require freq_penalty > 0'''
    if config['model'] != 'gpt-3.5-turbo-16k':
        freq_penalty = 0.1
        role = "system"
    else:
        # gpt-3.5-turbo-16k requires freq_penalty=0
        freq_penalty = 0
        role = "assistant"
    data = {
        "model": model,
        "messages": [
            {
                "role": role,
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
        "max_tokens": max_tokens,
        "presence_penalty": 0,
        "frequency_penalty": freq_penalty
    }
    return json.dumps(data)

def create_http_headers(api_key):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

## LLM : ChatGPT-3.5 API or Perplexity supported models
def send_to_llm(config, headers, topic, chunks, final_outfile):
    i = 1
    first_response_flag = True
    with open(final_outfile, 'w') as f:
        print(f" model {config['model']}, topic {topic}\n\n", file=f)
        for chunk in chunks:
            print(f"chunk {i} of {len(chunks)} posted to {config['url']}, model {config['model']}, topic {topic}", file=sys.stderr)
            if not first_response_flag:
                chunk = chunk.replace('Provide a markdown table:', 'Provide a markdown table, but do not provide a table header, or remove the table header:', 1)
            response = requests.post(url=config['url'], headers=headers, data=chunk)
            response_json = response.json()
            
            if response.status_code == 200:
                first_response_flag = False
                print(response_json['choices'][0]['message']['content'], file=f)
            else:
                print(f"Error: {response_json['error']['message']}", file=sys.stderr)
            i += 1
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Hacker News threads.')
    parser.add_argument('--hnitem',  help='Hacker News item URL, or id, e.g. 39577113', required=True)
    parser.add_argument('--topic',   help='Topic of the discussion',  default="Hacker news thread")
    parser.add_argument('--api_key', help='OPENAI_API_KEY. Put it in .env or set it on command line', 
                        required=False, default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument('--model',   help='Model to use for the LLM, e.g. "mistral-7b-instruct"', default='gpt-3.5-turbo-16k')
    parser.add_argument('--url',     help='URL for the LLM API, e.g. https://api.perplexity.ai/chat/completions',      default='https://api.openai.com/v1/chat/completions')
    
    args = parser.parse_args()
    config = {
        'api_key': args.api_key,
        'model':   args.model,
        'url':     args.url,
        'hnitem':  args.hnitem,
        'topic' :  args.topic
    }
    create_subdirectories()
    hnitem = check_hnitem(args.hnitem)

    topic_line = f"The topic was: {config['topic']}, hnitem: {hnitem}"
    topic_cleaned = re.sub(r'\W+', '-', f"{config['topic']}-{hnitem}")
    
    
    intermediate_file = f"{topic_cleaned}.txt" if args.topic else f"hacker-news-thread-{get_item_id(config.hnitem)}.txt"
    intermediate_file = os.path.join("output", f"{topic_cleaned}-{config['model']}.txt")
    intermediate_file2 = f"{re.sub('.txt', '', intermediate_file)}-intermediate2.txt"
    intermediate_file3 = f"{re.sub('.txt', '', intermediate_file)}--input-for-llm.txt"
    final_outfile = os.path.join("final_output", f"{topic_cleaned}-{config['model']}.md")
    max_tokens = 4000
    chunk_size = int(max_tokens * 2.5)
    # if file does not exist, download it
    if not os.path.isfile(intermediate_file):
        download_hn_thread(hnitem, intermediate_file)
    else:
        print(f"File {intermediate_file} already exists, skipping download.", file=sys.stderr)
    preprocess(intermediate_file, intermediate_file2, intermediate_file3, args.topic)
    
    with open(intermediate_file3, 'r') as f:
        text = f.read()
    
    print(f"Read {intermediate_file3}...:  {len(text)}  chars read.", file=sys.stderr)
    # the prompt is read from a file
    instruction_file_path = "input/instruction.txt"
    with open(instruction_file_path, 'r') as f:
        instruction = f.read()

    current_date = datetime.now().strftime("%Y-%m-%d")
    topic_line = f'{current_date}: {topic_line}'
    headers = create_http_headers(config['api_key'])
    chunked_rawtext = chunk_text(text, chunk_size)
    chunked_data = chunk_data(chunked_rawtext, instruction)
    
    send_to_llm(config, headers, topic_line, chunked_data, final_outfile)