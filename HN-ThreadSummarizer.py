#!/usr/bin/env python
"""
HN Thread Summarizer - Summarize Hacker News threads using OpenAI.

This is the main entry point. The implementation has been refactored into
the hn_summarizer package for better modularity.
"""

from hn_summarizer.cli import main

if __name__ == "__main__":
    main()
