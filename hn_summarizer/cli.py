"""Command-line interface for the HN Thread Summarizer."""

import os
import sys
import re
import argparse

from dotenv import load_dotenv

from .utilities import Utilities
from .llm_interaction import LLMInteraction
from .version_check import ensure_structured_output_support


class HNSummarizerCLI:
    """Main CLI class for the HN Thread Summarizer."""

    def __init__(self):
        """Initialize the CLI with parsed arguments."""
        parser = argparse.ArgumentParser(
            description='Process Hacker News threads with OpenAI structured outputs.'
        )
        parser.add_argument(
            '--hnitem',
            help='Hacker News item URL, or id, e.g. 39577113',
            required=True
        )
        parser.add_argument(
            '--topic',
            help='Topic of the discussion',
            default="Hacker news thread"
        )
        parser.add_argument(
            '--key',
            help='OPENAI_API_KEY. Put it in .env or set it on command line',
            required=False,
            default=os.getenv("OPENAI_API_KEY")
        )
        parser.add_argument(
            '--model',
            help='Model to use for OpenAI, e.g. "gpt-4o", "gpt-4o-mini"',
            default='gpt-4o-mini'
        )
        
        args = parser.parse_args()
        self.config = {
            'api_key': args.key,
            'model': args.model,
            'hnitem': args.hnitem,
            'topic': args.topic
        }

    def run(self):
        """Execute the main summarization workflow."""
        Utilities.create_subdirectories()
        
        hnitem_dict = Utilities.check_hnitem(self.config['hnitem'])
        hnitem = hnitem_dict['hnitem']
        hnitem_id = hnitem_dict['hnitem_id']

        topic_line = f"# HN Topic: [{self.config['topic']}]({hnitem}), (hnitem id {hnitem_id}), and discussion"
        topic_cleaned = re.sub(r'\W+', '-', f"{self.config['topic']}-{hnitem}")
        
        intermediate_file = os.path.join("output", f"{topic_cleaned}-{self.config['model']}.xml")
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
        
        # Second pass: categorize the arguments
        llm_interaction.categorize_arguments(final_outfile, max_output_tokens)


def main():
    """Entry point for the CLI."""
    load_dotenv()
    ensure_structured_output_support()
    cli = HNSummarizerCLI()
    cli.run()


if __name__ == "__main__":
    main()
