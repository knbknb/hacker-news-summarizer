"""LLM interaction module for OpenAI API calls."""

import sys
from datetime import datetime

import tiktoken
from openai import OpenAI

from .models import ThreadSummaryResponse


class LLMInteraction:
    """Handle interactions with the OpenAI API for thread summarization."""

    def __init__(self, config):
        """
        Initialize the LLM interaction handler.
        
        Args:
            config: Dictionary containing 'api_key' and 'model' keys
        """
        self.config = config
        self.client = OpenAI(api_key=config['api_key'])
        self.encoding = self._resolve_encoding(config['model'])
        self.responses_api = self._resolve_responses_api(self.client)

    @staticmethod
    def _resolve_encoding(model_name):
        """Get the tiktoken encoding for the specified model."""
        try:
            return tiktoken.encoding_for_model(model_name)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")

    @staticmethod
    def _resolve_responses_api(client):
        """
        Resolve the responses API from the OpenAI client.
        
        Args:
            client: OpenAI client instance
            
        Returns:
            The responses API object
            
        Raises:
            RuntimeError: If the responses API is not available
        """
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
        """
        Extract the parsed ThreadSummaryResponse from an API response.
        
        Args:
            response: The API response object
            
        Returns:
            ThreadSummaryResponse or None if extraction fails
        """
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
                for content in (getattr(item, "content", []) or []):
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
        """
        Extract plain text output from an API response (fallback).
        
        Args:
            response: The API response object
            
        Returns:
            Extracted text as a string
        """
        # Try direct output_text first (preferred)
        direct_output_text = getattr(response, "output_text", None)
        if direct_output_text:
            if isinstance(direct_output_text, str):
                return direct_output_text.strip()
            elif isinstance(direct_output_text, list):
                return "\n".join(str(t) for t in direct_output_text if t).strip()

        # Fall back to iterating through output items
        texts = []
        output_items = getattr(response, "output", None)
        if output_items:
            for item in output_items:
                for content in (getattr(item, "content", []) or []):
                    text_value = getattr(content, "text", None)
                    if text_value:
                        texts.append(text_value)
        if texts:
            return "\n".join(texts).strip()

        # Last resort: model_dump
        if hasattr(response, "model_dump"):
            dumped = response.model_dump()
            for item in dumped.get("output", []):
                for content in item.get("content", []):
                    text_value = content.get("text")
                    if text_value:
                        texts.append(text_value)
        return "\n".join(texts).strip()

    def chunk_text(self, text, chunk_token_limit=10000):
        """
        Split text into chunks that fit within the token limit.
        
        Args:
            text: The text to chunk
            chunk_token_limit: Maximum tokens per chunk
            
        Returns:
            List of chunk dictionaries with 'text', 'token_count', and 'char_count' keys
            
        Raises:
            ValueError: If chunk_token_limit is not positive
        """
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
        """
        Send chunks to OpenAI Responses API using structured outputs with Pydantic models.
        
        Args:
            topic: The topic header line for the output file
            chunks: List of text chunks to process
            instruction: System instruction for the LLM
            final_outfile: Path to write the final markdown output
            max_output_tokens: Maximum tokens for LLM response
        """
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
                        # Write table header before the first data row
                        if is_first_chunk:
                            print("| Participant/User name | Argument | Argument objections(keyword-style)/URLs |", file=f)
                            print("| --- | --- | --- |", file=f)
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
                            #temperature=0.1,
                            max_output_tokens=max_output_tokens,
                        )
                        fallback_text = self._extract_text_output(fallback_response)
                        if fallback_text:
                            print(fallback_text, file=f)
                    except Exception as fallback_error:
                        print(f"Fallback also failed for chunk {i}: {str(fallback_error)}", file=sys.stderr)
                
                i += 1

    def categorize_arguments(self, markdown_file, max_output_tokens=4096):
        """
        Second pass: Read the markdown file and categorize the arguments.
        
        Args:
            markdown_file: Path to the markdown file to process
            max_output_tokens: Maximum tokens for LLM response
            
        Returns:
            The path to the updated file with categories inserted
        """
        print(f"Starting second pass: categorizing arguments in {markdown_file}", file=sys.stderr)
        
        with open(markdown_file, 'r') as f:
            content = f.read()
        
        # Extract the table content for categorization
        categorization_prompt = """Group the arguments from the table into meaningful categories. Invent your own categories. Output only those proposed new categories.

Format your response as:

Here are proposed categories for organizing the arguments:

1. Category Name
- Sub-point about what this category covers
- Another sub-point

2. Another Category Name
- Sub-point
- Another sub-point

(continue for all categories)"""
        
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "input_text", "text": categorization_prompt}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": content}
                ]
            }
        ]
        
        try:
            response = self.responses_api.create(
                model=self.config['model'],
                input=messages,
                max_output_tokens=max_output_tokens,
            )
            
            categories_text = self._extract_text_output(response)
            
            if categories_text:
                # Find the Date/LLM line and insert categories after it
                lines = content.split('\n')
                new_lines = []
                inserted = False
                
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    # Insert after the "## Date:" line
                    if not inserted and line.startswith('## Date:'):
                        new_lines.append('')  # blank line
                        new_lines.append(categories_text)
                        new_lines.append('')  # blank line
                        inserted = True
                
                # Write back to the same file
                with open(markdown_file, 'w') as f:
                    f.write('\n'.join(new_lines))
                
                print(f"Categories inserted into {markdown_file}", file=sys.stderr)
            else:
                print("No categories generated from LLM response", file=sys.stderr)
                
        except Exception as e:
            print(f"Error during categorization: {str(e)}", file=sys.stderr)
        
        return markdown_file
