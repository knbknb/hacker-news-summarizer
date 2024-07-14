#!/usr/bin/env python3
from datetime import datetime
import os
import sys
import re
import html2text
from urllib.parse import urlparse
import requests
import json
from dotenv import load_dotenv
import argparse

class Utilities:
    @staticmethod
    def create_subdirectories():
        subdirectories = ['./data', './final_output', './input', './output', './script_attic']
        for directory in subdirectories:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.access(directory, os.W_OK):
                print(f"Warning: {directory} is not writable.", file=sys.stderr)

    @staticmethod
    def check_hnitem(hnitem, hnitem_id=None):
        if hnitem.isdigit() and len(hnitem) > 5:
            hnitem = f"https://news.ycombinator.com/item?id={hnitem}"
            hnitem_id = Utilities.get_item_id(hnitem)
        hnitem_dict = {'hnitem': hnitem, 'hnitem_id': hnitem_id}
        return hnitem_dict

    @staticmethod
    def get_item_id(hnitem):
        parsed_url = urlparse(hnitem)
        query_params = dict(q.split('=') for q in parsed_url.query.split('&'))
        return query_params['id']

    @staticmethod
    def download_hn_thread(hnitem, intermediate_file):
        response = requests.get(hnitem)
        response.raise_for_status()
        raw_text = html2text.html2text(response.text)
        with open(intermediate_file, 'w') as f:
            f.write(raw_text)

    @staticmethod
    def preprocess(infile, intermediate_file2, intermediate_file3, topic):
        with open(infile, 'r') as f:
            lines = f.readlines()
        lines[0] = lines[0].strip() + f" {topic}\n"
        line_start = next(i for i, line in enumerate(lines) if "login" in line)
        lines = lines[line_start:]

        if os.path.isfile(intermediate_file2):
            print(f"File {infile} already exists, skipping preprocess.", file=sys.stderr)
        else:
            with open(intermediate_file2, 'w') as f:
                for line in lines:
                    if not any(s in line for s in ['(reply?', '(s.gif)', 'javascript:void']):
                        f.write(line)

            with open(intermediate_file2, 'r') as f:
                lines = f.readlines()
            with open(intermediate_file2, 'w') as f:
                for line in lines:
                    f.write(re.sub(r'(\[\s*\d+ \w+ ago).+$', r'', line))

            with open(intermediate_file2, 'r') as f:
                lines = f.readlines()

            with open(intermediate_file2, 'w') as f:
                for line in lines:
                    f.write(re.sub(r'^\s*\[\d+\].–.$', '', line))

            line_end = next(i for i, line in enumerate(lines) if re.search(r'newsguidelines\.html', line))

            with open(intermediate_file2, 'r') as f:
                lines = f.readlines()

            with open(intermediate_file3, 'w') as f:
                for line in lines[:line_end]:
                    f.write(line)

class LLMInteraction:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def chunk_text(text, chunk_size=10000):
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    @staticmethod
    def chunk_data(chunks, instruction, config):
        chunks_data = []
        for chunk in chunks:
            chunks_data.append(LLMInteraction.set_data(config['model'], chunk, instruction))
        print(f"Number of data chunks: {len(chunks_data)}", file=sys.stderr)
        return chunks_data

    @staticmethod
    def set_data(model, chunk, instruction, max_tokens=1024):
        if not re.match(r'^gpt', model):
            freq_penalty = 0.1
            role = "system"
        else:
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

    @staticmethod
    def create_http_headers(api_key):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    @staticmethod
    def send_to_llm(config, headers, topic, chunks, final_outfile):
        i = 1
        current_date = datetime.now().strftime("%Y-%m-%d")
        first_response_flag = True
        with open(final_outfile, 'w') as f:
            print(f"{topic}\n", file=f)
            print(f"## Date: {current_date}. LLM: {config['model']}\n", file=f)
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

class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Process Hacker News threads.')
        parser.add_argument('--hnitem',  help='Hacker News item URL, or id, e.g. 39577113', required=True)
        parser.add_argument('--topic',   help='Topic of the discussion',  default="Hacker news thread")
        parser.add_argument('--api_key', help='OPENAI_API_KEY. Put it in .env or set it on command line', 
                            required=False, default=os.getenv("OPENAI_API_KEY"))
        parser.add_argument('--model',   help='Model to use for the LLM, e.g. "mistral-7b-instruct"', default='gpt-4o')
        parser.add_argument('--url',     help='URL for the LLM API, e.g. https://api.perplexity.ai/chat/completions',      default='https://api.openai.com/v1/chat/completions')
        
        args = parser.parse_args()
        self.config = {
            'api_key': args.api_key,
            'model':   args.model,
            'url':     args.url,
            'hnitem':  args.hnitem,
            'topic' :  args.topic
        }

    def run(self):
        Utilities.create_subdirectories()
        
        hnitem_dict = Utilities.check_hnitem(self.config['hnitem'])
        hnitem = hnitem_dict['hnitem']
        hnitem_id = hnitem_dict['hnitem_id']

        topic_line = f"# HN Topic: [{self.config['topic']}]({hnitem}), (hnitem id {hnitem_id}), and discussion"
        topic_cleaned = re.sub(r'\W+', '-', f"{self.config['topic']}-{hnitem}")
        
        intermediate_file = os.path.join("output", f"{topic_cleaned}-{self.config['model']}.txt")
        intermediate_file2 = f"{re.sub('.txt', '', intermediate_file)}-intermediate2.txt"
        intermediate_file3 = f"{re.sub('.txt', '', intermediate_file)}--input-for-llm.txt"
        final_outfile = os.path.join("final_output", f"{topic_cleaned}-{self.config['model']}.md")
        max_tokens = 4000
        chunk_size = int(max_tokens * 2.5)

        if not os.path.isfile(intermediate_file):
            Utilities.download_hn_thread(hnitem, intermediate_file)
        else:
            print(f"File {intermediate_file} already exists, skipping download.", file=sys.stderr)
        Utilities.preprocess(intermediate_file, intermediate_file2, intermediate_file3, self.config['topic'])
        
        with open(intermediate_file3, 'r') as f:
            text = f.read()
        
        print(f"Read {intermediate_file3}...:  {len(text)}  chars read.", file=sys.stderr)

        instruction_file_path = "input/instruction.txt"
        with open(instruction_file_path, 'r') as f:
            instruction = f.read()

        headers = LLMInteraction.create_http_headers(self.config['api_key'])
        chunked_rawtext = LLMInteraction.chunk_text(text, chunk_size)
        chunked_data = LLMInteraction.chunk_data(chunked_rawtext, instruction, self.config)
        
        LLMInteraction.send_to_llm(self.config, headers, topic_line, chunked_data, final_outfile)

if __name__ == "__main__":
    load_dotenv()
    main = Main()
    main.run()
