#!/usr/bin/env python
from datetime import datetime
import os
import sys
import re
import html
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv
import argparse
from typing import List, Optional
from pydantic import BaseModel, Field
import openai as _openai_module
from openai import OpenAI
import tiktoken

# Pydantic models for structured output
_REQUIRED_OPENAI_STRUCTURED_VERSION = (1, 40, 0)

def _parse_version_tuple(version_str: str) -> tuple[int, ...]:
    digits = re.findall(r"\d+", version_str)
    return tuple(int(part) for part in digits)


def _has_responses_feature() -> bool:
    if getattr(OpenAI, "responses", None) is not None:
        return True
    beta = getattr(OpenAI, "beta", None)
    return getattr(beta, "responses", None) is not None


def _ensure_structured_output_support() -> None:
    version_str = getattr(_openai_module, "__version__", None)
    if not version_str:
        raise RuntimeError(
            "Cannot determine the installed 'openai' version. "
            "Install openai>=1.40.0 to use structured outputs."
        )
    version_tuple = _parse_version_tuple(version_str)
    if not version_tuple or version_tuple < _REQUIRED_OPENAI_STRUCTURED_VERSION:
        raise RuntimeError(
            f"OpenAI {version_str} does not support structured outputs. "
            "Upgrade to openai>=1.40.0 to proceed."
        )
    if not _has_responses_feature():
        raise RuntimeError(
            "The installed OpenAI package lacks the Responses interface required for structured outputs. "
            "Please upgrade to openai>=1.40.0."
        )


_ensure_structured_output_support()

class CommentSummary(BaseModel):
    """Structured model for a single comment summary in the HN thread."""
    participant: str = Field(description="The username/participant name")
    argument: str = Field(description="Summary of the participant's argument in short sentences or keywords")
    urls: Optional[str] = Field(default="", description="URLs mentioned in the comment, formatted in markdown if long")


class ThreadSummaryResponse(BaseModel):
    """Structured model for the complete thread summary response."""
    summaries: List[CommentSummary] = Field(description="List of comment summaries from the thread")


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
            f.write('<tableheader/>' + "\n")
            for comment in comments:
                f.write(comment + "\n")


class LLMInteraction:
    def __init__(self, config):
        self.config = config
        self.client = OpenAI(api_key=config['api_key'])
        self.encoding = self._resolve_encoding(config['model'])
        self.responses_api = self._resolve_responses_api(self.client)

    @staticmethod
    def _resolve_encoding(model_name):
        try:
            return tiktoken.encoding_for_model(model_name)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")

    @staticmethod
    def _resolve_responses_api(client):
        responses_attr = getattr(client, "responses", None)
        if responses_attr is not None:
            return responses_attr

        # Check if the OpenAI client exposes the newer responses API under the 'beta' namespace (pre-release)
        beta_namespace = getattr(client, "beta", None)
        beta_responses = getattr(beta_namespace, "responses", None) if beta_namespace else None
        if beta_responses is not None:
            return beta_responses

        raise RuntimeError(
            "Please upgrade to openai>=1.0.0."
        )

    @staticmethod
    def _extract_parsed_response(response):
        parsed_output = getattr(response, "output_parsed", None)
        if parsed_output:
            if isinstance(parsed_output, ThreadSummaryResponse):
                return parsed_output
            if isinstance(parsed_output, dict):
                return ThreadSummaryResponse(**parsed_output)
            if isinstance(parsed_output, list):
                for item in parsed_output:
                    if isinstance(item, ThreadSummaryResponse):
                        return item
                    if isinstance(item, dict):
                        return ThreadSummaryResponse(**item)

        output_items = getattr(response, "output", None)
        if output_items:
            for item in output_items:
                for content in getattr(item, "content", []):
                    parsed_payload = getattr(content, "parsed", None)
                    if parsed_payload:
                        if isinstance(parsed_payload, ThreadSummaryResponse):
                            return parsed_payload
                        if isinstance(parsed_payload, dict):
                            return ThreadSummaryResponse(**parsed_payload)
        if hasattr(response, "model_dump"):
            dumped = response.model_dump()
            for item in dumped.get("output", []):
                for content in item.get("content", []):
                    parsed_payload = content.get("parsed")
                    if parsed_payload:
                        if isinstance(parsed_payload, dict):
                            return ThreadSummaryResponse(**parsed_payload)
                        return parsed_payload
        return None

    @staticmethod
    def _extract_text_output(response):
        texts = []

        direct_output_text = getattr(response, "output_text", None)
        if direct_output_text:
            if isinstance(direct_output_text, str):
                texts.append(direct_output_text)
            elif isinstance(direct_output_text, list):
                texts.extend(str(t) for t in direct_output_text if t)

        output_items = getattr(response, "output", None)
        if output_items:
            for item in output_items:
                for content in getattr(item, "content", []):
                    text_value = getattr(content, "text", None)
                    if text_value:
                        texts.append(text_value)
        if not texts and hasattr(response, "model_dump"):
            dumped = response.model_dump()
            for item in dumped.get("output", []):
                for content in item.get("content", []):
                    text_value = content.get("text")
                    if text_value:
                        texts.append(text_value)
        return "\n".join(texts).strip()

    def chunk_text(self, text, chunk_token_limit=10000):
        if chunk_token_limit <= 0:
            raise ValueError("chunk_token_limit must be greater than zero")

        lines = text.splitlines(keepends=True)
        chunks = []
        current_lines = []
        current_tokens = 0

        def flush_chunk():
            nonlocal current_lines, current_tokens
            if not current_lines:
                return
            chunk_text = ''.join(current_lines)
            chunk_index = len(chunks) + 1
            chunk_info = {
                'text': chunk_text,
                'token_count': current_tokens,
                'char_count': len(chunk_text)
            }
            chunks.append(chunk_info)
            print(
                f"[tokenizer] chunk {chunk_index}: {current_tokens} tokens ({len(chunk_text)} chars) / limit {chunk_token_limit}",
                file=sys.stdout
            )
            current_lines = []
            current_tokens = 0

        for line in lines:
            line_tokens = len(self.encoding.encode(line))
            if current_tokens and current_tokens + line_tokens > chunk_token_limit:
                flush_chunk()

            if line_tokens > chunk_token_limit:
                chunk_index = len(chunks) + 1
                chunk_info = {
                    'text': line,
                    'token_count': line_tokens,
                    'char_count': len(line)
                }
                chunks.append(chunk_info)
                print(
                    f"[tokenizer] chunk {chunk_index}: {line_tokens} tokens ({len(line)} chars) / limit {chunk_token_limit} (single-line overflow)",
                    file=sys.stdout
                )
                continue

            current_lines.append(line)
            current_tokens += line_tokens

        flush_chunk()
        return chunks

    def send_to_llm(self, topic, chunks, instruction, final_outfile, max_output_tokens=4096):
        """Send chunks to OpenAI Responses API using structured outputs with Pydantic models."""
        i = 1
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        with open(final_outfile, 'w') as f:
            # Write header
            print(f"{topic}\n", file=f)
            print(f"## Date: {current_date}. LLM: {self.config['model']}\n", file=f)
            
            # Write markdown table header only once
            is_first_chunk = True
            
            for chunk in chunks:
                chunk_num = f'chunk_num {i} of {len(chunks)}'
                print(f"{chunk_num} processing with model {self.config['model']}", file=sys.stderr)
                chunk_text = chunk['text'] if isinstance(chunk, dict) else chunk
                
                messages = [
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": instruction}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": chunk_text}
                        ]
                    }
                ]

                try:
                    structured_response = self.responses_api.parse(
                        model=self.config['model'],
                        input=messages,
                        text_format=ThreadSummaryResponse,
                        #temperature=0.1,
                        max_output_tokens=max_output_tokens,
                    )

                    response_data = self._extract_parsed_response(structured_response)
                    
                    if response_data:
                        # Write table header for first chunk
                        if is_first_chunk and '<tableheader/>' in chunk_text:
                            print("| Participant/User name | Argument | Argument objections(keyword-style)/URLs |", file=f)
                            print("|---|---|---|", file=f)
                            is_first_chunk = False
                        
                        # Write each comment summary as a table row
                        for summary in response_data.summaries:
                            participant = summary.participant.replace('|', '\\|')
                            argument = summary.argument.replace('|', '\\|')
                            urls = summary.urls.replace('|', '\\|') if summary.urls else ""
                            print(f"| {participant} | {argument} | {urls} |", file=f)
                    
                except Exception as e:
                    print(f"Error processing chunk {i}: {str(e)}", file=sys.stderr)
                    try:
                        fallback_response = self.responses_api.create(
                            model=self.config['model'],
                            input=messages,
                            temperature=0.1,
                            max_output_tokens=max_output_tokens,
                        )
                        fallback_text = self._extract_text_output(fallback_response)
                        if fallback_text:
                            print(fallback_text, file=f)
                    except Exception as fallback_error:
                        print(f"Fallback also failed for chunk {i}: {str(fallback_error)}", file=sys.stderr)
                
                i += 1


class Main:
    def __init__(self):
        parser = argparse.ArgumentParser(description='Process Hacker News threads with OpenAI structured outputs.')
        parser.add_argument('--hnitem',  help='Hacker News item URL, or id, e.g. 39577113', required=True)
        parser.add_argument('--topic',   help='Topic of the discussion',  default="Hacker news thread")
        parser.add_argument('--key',     help='OPENAI_API_KEY. Put it in .env or set it on command line', 
                            required=False, default=os.getenv("OPENAI_API_KEY"))
        parser.add_argument('--model',   help='Model to use for OpenAI, e.g. "gpt-4o", "gpt-4o-mini"', default='gpt-4o-mini')
        
        args = parser.parse_args()
        self.config = {
            'api_key': args.key,
            'model':   args.model,
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
        max_output_tokens = 5000
        chunk_token_limit = int(max_output_tokens * 2.5)

        if not os.path.isfile(intermediate_file):
            Utilities.download_hn_thread(hnitem_id, intermediate_file)
        else:
            print(f"File {intermediate_file} already exists, skipping download.", file=sys.stderr)
        
        with open(intermediate_file, 'r') as f:
            text = f.read()
        
        print(f"Read {intermediate_file}...:  {len(text)}  chars read.", file=sys.stderr)

        instruction_file_path = "input/instruction.txt"
        with open(instruction_file_path, 'r') as f:
            instruction = f.read()

        llm_interaction = LLMInteraction(self.config)
        chunked_rawtext = llm_interaction.chunk_text(text, chunk_token_limit)
        
        print(f"Number of data chunks: {len(chunked_rawtext)}", file=sys.stderr)
        
        llm_interaction.send_to_llm(topic_line, chunked_rawtext, instruction, final_outfile, max_output_tokens)


if __name__ == "__main__":
    load_dotenv()
    main = Main()
    main.run()
