#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from urllib.parse import urlparse
import requests
import json
from dotenv import load_dotenv

# import time # for sleep(), not used yet

# Load .env file with API keys and credentials
load_dotenv()
# Add your OpenAI API key here

def get_item_id(hnitem):
    parsed_url = urlparse(hnitem)
    query_params = dict(q.split('=') for q in parsed_url.query.split('&'))
    return query_params['id']

def download_hn_thread(hnitem, outfile):
    subprocess.run(['lynx', '--dump', hnitem], stdout=open(outfile, 'w'))

def preprocess(outfile, intermediate_file, final_file):

    # remove HEADER 
    with open(outfile, 'r') as f:
        lines = f.readlines()

    line_start = next(i for i, line in enumerate(lines) if "login" in line)
    lines = lines[line_start:]

    with open(intermediate_file, 'w') as f:
        for line in lines:
            if not any(s in line for s in [']next', ']reply', '[s.gif']):
                f.write(line)


    # POSTS: remove lines with "ago" 
    with open(intermediate_file, 'r') as f:
        lines = f.readlines()

    with open(intermediate_file, 'w') as f:
        for line in lines:
            f.write(re.sub(r'^(\s*\d+\.\w+) .+ ago .+$', r'\1', line))


    # FOOTER: remove lines starting with  "Guidelines...FAQ...Lists...API...Security" 
    with open(intermediate_file, 'r') as f:
        lines = f.readlines()

    with open(intermediate_file, 'w') as f:
        for line in lines:
            f.write(re.sub(r'^\s*\[\d+\].–.$', '', line))

    line_end = next(i for i, line in enumerate(lines) if re.search(r'Guidelines.+FAQ.+Lists|.+API.+Security', line))


    # write to final file
    with open(intermediate_file, 'r') as f:
        lines = f.readlines()

    with open(final_file, 'w') as f:
        for line in lines[:line_end]:
            f.write(line)

def chunk_text(text, chunk_size=14000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

## LLM : ChatGPT-3.5 API
def send_to_llm(url, instruction, topic, chunks, first_response):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    instruction = "\n".join([topic,instruction])
    for chunk in chunks:
        data = {
            "model": "gpt-3.5-turbo-16k",
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
            "frequency_penalty": 0
        }
        data = json.dumps(data)
        response = requests.post(url, headers=headers, data=data)
        response_json = response.json()
        
        if response.status_code == 200:
            if first_response:
                print(f"topic: {topic} | ... | ...", topic)
                first_response = False
            print(response_json['choices'][0]['message']['content'])
        else:
            print(f"Error: {response_json['error']['message']}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python hn-thread2txt2chatgpt2md.py <hacker-news-item-url> <topic> [outfile]")
        print("e.g. python hn-thread2txt2chatgpt2md.py https://news.ycombinator.com/item?id=37156101 'Why did people in the past look so much older' hacker-news-thread.txt")
        sys.exit(0)

    hnitem = sys.argv[1]
    topic = sys.argv[2]
    outfile = sys.argv[3] if len(sys.argv) > 3 else f"hacker-news-thread-{get_item_id(hnitem)}.txt"
    outfile = os.path.join("output", outfile)
    intermediate_file = f"{outfile}-intermediate.txt"
    final_file = f"{outfile}-for-chatgpt.txt"

    download_hn_thread(hnitem, outfile)
    preprocess(outfile, intermediate_file, final_file)
    
    with open(final_file, 'r') as f:
        text = f.read()
    # Reading the instruction from a file in the "input" subdirectory
    instruction_file_path = "input/instruction.txt"
    with open(instruction_file_path, 'r') as f:
        instruction = f.read()

    # send topic, instruction, and text to ChatGPT-3.5 API
    # Output will be a markdown table sent to stdout
    topic_line = ": ".join(["The topic was", topic])
    first_response = True
    chunks = chunk_text(text)
    API_KEY = os.getenv('OPENAI_API_KEY')
    url = "https://api.openai.com/v1/chat/completions"
    send_to_llm(instruction, topic_line, chunks, first_response)