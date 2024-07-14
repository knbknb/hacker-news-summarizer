#!/usr/bin/env python
from datetime import datetime
import os
import sys
import re
import html
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
    def download_hn_thread(hn_item_id, intermediate_file):
        url = f"https://hn.algolia.com/api/v1/items/{hn_item_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        def extract_comments(comment):
            comments = []
            if comment.get('text'):
                comments.append(f"<author>{html.escape(comment['author'])}</author><comment>{html.escape(comment['text'])}</comment>")
            for child in comment.get('children', []):
                comments.extend(extract_comments(child))
            return comments
        
        comments = extract_comments(data)
        
        with open(intermediate_file, 'w') as f:
            for comment in comments:
                f.write(comment + "\n")


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
        with open(final_outfile, 'w') as f:
            print(f"{topic}\n", file=f)
            print(f"## Date: {current_date}. LLM: {config['model']}\n", file=f)
            for chunk in chunks:
                chunk_num = f'chunk_num {i} of {len(chunks)}'
                print(f"{chunk_num} posted to {config['url']}, model {config['model']}, topic {topic}", file=sys.stderr)
                chunk = f'{chunk_num}:  {chunk}'
                response = requests.post(url=config['url'], headers=headers, data=chunk)
                response_json = response.json()
                
                if response.status_code == 200:
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
        final_outfile = os.path.join("final_output", f"{topic_cleaned}-{self.config['model']}.md")
        max_tokens = 4000
        chunk_size = int(max_tokens * 2.5)

        if not os.path.isfile(intermediate_file):
            Utilities.download_hn_thread(hnitem_id, intermediate_file)
        else:
            print(f"File {intermediate_file} already exists, skipping download.", file=sys.stderr)
        #Utilities.preprocess(intermediate_file, intermediate_file2, intermediate_file3, self.config['topic'])
        
        with open(intermediate_file, 'r') as f:
            text = f.read()
        
        print(f"Read {intermediate_file}...:  {len(text)}  chars read.", file=sys.stderr)

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
