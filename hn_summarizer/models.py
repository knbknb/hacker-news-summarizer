"""Pydantic models for structured output from the LLM."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CommentSummary(BaseModel):
    """Structured model for a single comment summary in the HN thread."""
    participant: str = Field(description="The username/participant name")
    argument: str = Field(description="Summary of the participant's argument in short sentences or keywords")
    urls: Optional[str] = Field(default="", description="URLs mentioned in the comment, formatted in markdown if long")


class ThreadSummaryResponse(BaseModel):
    """Structured model for the complete thread summary response."""
    summaries: List[CommentSummary] = Field(description="List of comment summaries from the thread")
