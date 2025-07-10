"""
Groq conversation mapper for fast LLM inference.
"""

import json
import re
import time
import random
from typing import Optional

from utils.conv.conversation import Conversation, ConversationMap
from utils.conv.conversation import (
    SentimentType,
    ProblemType,
    CategoryType,
    IntentType,
    EmotionType,
)


class GroqMapper:
    """Conversation mapper using Groq API for fast inference."""

    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "llama3-8b-8192"
    ):
        """
        Initialize Groq mapper.

        Available models:
        - "llama3-8b-8192" (Fast, good quality)
        - "llama3-70b-8192" (Slower, better quality)
        - "mixtral-8x7b-32768" (Good balance)
        - "gemma-7b-it" (Lightweight)
        """
        self.api_key = api_key
        self.model_name = model_name
        self._setup_client()

    def _setup_client(self):
        """Setup Groq client."""
        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
            print(f"Successfully initialized Groq client with {self.model_name}")
        except Exception as e:
            print(f"Error initializing Groq client: {e}")
            raise

    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Process conversation with Groq API with rate limiting and backoff."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                prompt = self._create_analysis_prompt(conversation)

                # Make API call with structured output
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert conversation analyst. Analyze conversations and provide structured analysis.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=512,
                    response_format={"type": "json_object"},
                )

                # Parse response directly using Pydantic
                analysis_text = response.choices[0].message.content
                analysis = self._parse_structured_analysis(analysis_text)

                # Create conversation copy with analysis
                conversation_copy = conversation.model_copy()
                conversation_copy.analysis = analysis

                return conversation_copy

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error
                if "rate_limit_exceeded" in error_str or "429" in error_str:
                    if attempt < max_retries - 1:
                        # Extract suggested wait time from error message
                        wait_time = self._extract_wait_time(error_str)
                        if wait_time is None:
                            # Exponential backoff with jitter
                            wait_time = base_delay * (2**attempt) + random.uniform(0, 1)

                        print(
                            f"Rate limit hit for conversation {conversation.dialogue_id}, waiting {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        print(
                            f"Rate limit exceeded for conversation {conversation.dialogue_id} after {max_retries} attempts"
                        )
                        return conversation
                else:
                    print(
                        f"Error processing conversation {conversation.dialogue_id}: {e}"
                    )
                    return conversation

        return conversation

    def _extract_wait_time(self, error_str: str) -> Optional[float]:
        """Extract wait time from Groq rate limit error message."""
        try:
            # Look for "Please try again in X.XXXs" pattern
            match = re.search(r"Please try again in (\d+\.?\d*)s", error_str)
            if match:
                return float(match.group(1))
        except:
            pass
        return None

    def _create_analysis_prompt(self, conversation: Conversation) -> str:
        """Create analysis prompt for Groq."""
        return f"""Analyze conversation ({conversation.duration_minutes}m, {conversation.message_count} msgs):
{conversation.full_text[:800]}

Rules:
- Sentiment: "positive"=gratitude/satisfaction, "negative"=frustration/problems, "neutral"=info requests
- Emotions: ["frustration", "satisfaction", "confusion", "urgency"]
- Problems: ["technical_issues", "user_confusion", "system_limitations", "process_inefficiency", "communication_failure", "other"]
- user_confusion: ONLY explicit confusion ("не понимаю") or multiple clarifications
- Categories: ["information", "communication", "other", "project_tasks", "hr", "organizational", "tech_support"]
- Intent: ["technical_help", "process_question", "project_task", "general_info", "coordination"]
- Feedback: Extract user feedback about agent system performance and behavior (empty array if none)
- Suggestions: Extract user suggestions for improving system or conversation experience (empty array if none)
- Severity: 0-2=success, 3-4=minor issues, 5-6=moderate problems, 7-8=major failures, 9-10=critical
- is_successful: true if request fulfilled, false if failed

JSON format:
{{
    "sentiment": "neutral",
    "sentiment_confidence": 0.8,
    "emotions": [],
    "problems": [],
    "problem_severity": 2,
    "problem_extra_info": "",
    "categories": ["information"],
    "intent": ["general_info"],
    "feedback": [],
    "suggestions": [],
    "is_successful": true
}}"""

    def _parse_structured_analysis(self, analysis_text: str) -> ConversationMap:
        """Parse structured JSON response directly to ConversationMap."""
        try:
            # Parse JSON directly
            parsed_data = json.loads(analysis_text)

            # Validate and create ConversationMap
            return ConversationMap(
                sentiment=self._parse_sentiment(
                    parsed_data.get("sentiment", "neutral")
                ),
                sentiment_confidence=float(
                    parsed_data.get("sentiment_confidence", 0.5)
                ),
                emotions=[
                    e
                    for e in parsed_data.get("emotions", [])
                    if e in [em.value for em in EmotionType]
                ],
                problems=[
                    ProblemType(p)
                    for p in parsed_data.get("problems", [])
                    if p in [e.value for e in ProblemType]
                ],
                problem_severity=int(parsed_data.get("problem_severity", 5)),
                problem_extra_info=parsed_data.get("problem_extra_info", ""),
                category=[
                    CategoryType(c)
                    for c in parsed_data.get("categories", ["other"])
                    if c in [e.value for e in CategoryType]
                ],
                intent=[
                    IntentType(i)
                    for i in parsed_data.get("intent", ["general_info"])
                    if i in [e.value for e in IntentType]
                ],
                feedback=parsed_data.get("feedback", []),
                suggestions=parsed_data.get("suggestions", []),
                is_successful=parsed_data.get("is_successful", True),
            )
        except Exception as e:
            print(f"Error parsing structured analysis: {e}")
            return self._default_analysis()

    def _parse_sentiment(self, sentiment_str: str) -> SentimentType:
        """Parse sentiment string to SentimentType."""
        sentiment_map = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)

    def _default_analysis(self) -> ConversationMap:
        """Return default analysis when parsing fails."""
        return ConversationMap(
            sentiment=SentimentType.NEUTRAL,
            sentiment_confidence=0.5,
            emotions=[],
            problems=[ProblemType.USER_CONFUSION],
            problem_severity=5,
            problem_extra_info="",
            category=[CategoryType.OTHER],
            intent=[IntentType.GENERAL_INFO],
            feedback=[],
            suggestions=[],
            is_successful=True,
        )
