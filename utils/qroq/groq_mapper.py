"""
Groq conversation mapper for fast LLM inference.
"""

import json
import re
import time
import random
from typing import TYPE_CHECKING, Union, Optional

from utils.conv.conversation import (
    Conversation, 
    ConversationMap, 
    RequestCategory, 
    ProblemDetection, 
    UX,
    validate_request_category,
    get_category_for_intent,
    BlockType
)

if TYPE_CHECKING:
    from groq import Groq
from utils.problem_eda import create_problem_detection_for_conversation
from utils.conv.conversation import (
    SentimentType,
    ProblemType,
    CategoryType,
    IntentType,
    EmotionType,
)


class GroqMapper:
    """UX mapper using Groq API for fast user experience analysis."""

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
        self.client: Optional['Groq'] = None
        self._setup_client()

    def _setup_client(self) -> None:
        """Setup Groq client."""
        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
            self._log_client_setup()
        except Exception as e:
            self._log_client_error(e)
            raise

    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Process conversation with UX and Intent analysis using Groq API."""
        try:
            # Analyze UX
            ux_analysis = self._analyze_ux(conversation)
            
            # Analyze Intent
            request_category = self._analyze_intent(conversation)
            
            # Create problem detection using keyword analysis
            problem_detection = create_problem_detection_for_conversation(conversation)

            # Create ConversationMap with all analyses
            conversation_map = ConversationMap(
                request=request_category,
                problems=problem_detection,
                ux=ux_analysis
            )

            # Create conversation copy with analysis
            conversation_copy = conversation.model_copy()
            conversation_copy.analysis = conversation_map

            return conversation_copy
            
        except Exception as e:
            self._log_processing_error(conversation.dialogue_id, e)
            return conversation

    def _extract_wait_time(self, error_str: str) -> Optional[float]:
        """Extract wait time from Groq rate limit error message."""
        try:
            # Look for "Please try again in X.XXXs" pattern
            match = re.search(r"Please try again in (\d+\.?\d*)s", error_str)
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None

    def _analyze_ux(self, conversation: Conversation) -> UX:
        """Analyze UX aspects of conversation using Groq API."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                prompt = self._create_ux_prompt(conversation)

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert UX analyst. Analyze conversations for user experience aspects.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )

                analysis_text = response.choices[0].message.content
                return self._parse_ux_analysis(analysis_text)

            except Exception as e:
                if self._handle_rate_limit_error(e, conversation.dialogue_id, attempt, max_retries, base_delay):
                    continue
                else:
                    return self._default_ux_analysis()

        return self._default_ux_analysis()

    def _analyze_intent(self, conversation: Conversation) -> RequestCategory:
        """Analyze intent and category of conversation using Groq API."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                prompt = self._create_intent_prompt(conversation)

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert conversation analyst. Identify user intent and request category.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=512,
                    response_format={"type": "json_object"},
                )

                analysis_text = response.choices[0].message.content
                return self._parse_intent_analysis(analysis_text)

            except Exception as e:
                if self._handle_rate_limit_error(e, conversation.dialogue_id, attempt, max_retries, base_delay):
                    continue
                else:
                    return self._default_request_category()

        return self._default_request_category()

    def _handle_rate_limit_error(self, error: Exception, dialogue_id: int, attempt: int, max_retries: int, base_delay: float) -> bool:
        """Handle rate limit errors with backoff. Returns True if should retry, False otherwise."""
        error_str = str(error)
        
        if "rate_limit_exceeded" in error_str or "429" in error_str:
            if attempt < max_retries - 1:
                wait_time = self._extract_wait_time(error_str)
                if wait_time is None:
                    wait_time = base_delay * (2**attempt) + random.uniform(0, 1)

                self._log_rate_limit_wait(dialogue_id, wait_time, attempt + 1, max_retries)
                time.sleep(wait_time)
                return True
            else:
                self._log_rate_limit_exceeded(dialogue_id, max_retries)
        else:
            self._log_processing_error(dialogue_id, error)
        
        return False

    def _create_ux_prompt(self, conversation: Conversation) -> str:
        """Create UX analysis prompt for Groq using only user messages."""
        # Use the new method to get only user messages
        user_messages = conversation.get_user_messages()
        
        # If no user messages found, fallback to full_text for backward compatibility
        if not user_messages.strip():
            user_messages = conversation.full_text[:800]
        else:
            # Limit user messages to 800 chars for the prompt
            user_messages = user_messages[:800]
        
        # Get agent types used in this conversation
        agent_types_str = ", ".join([agent.value for agent in conversation.agent_types]) if conversation.agent_types else "none"
        
        return f"""Analyze USER EXPERIENCE for conversation ({conversation.duration_minutes}m, {conversation.message_count} msgs):
User Messages:
{user_messages}

Agents Involved: {agent_types_str}

Focus ONLY on UX aspects - extract user sentiment, emotions, feedback and suggestions:

Rules:
- Sentiment: "positive"=gratitude/satisfaction, "negative"=frustration/problems, "neutral"=info requests
- Emotions: ["frustration", "satisfaction", "confusion", "urgency"] - only mark emotions with clear indicators
- Feedback: Extract user feedback about agent system performance and behavior (empty array if none)
- Suggestions: Extract user suggestions for improving system or conversation experience (empty array if none)
- is_successful: true if request fulfilled and user satisfied, false if failed or user frustrated

JSON format:
{{
    "sentiment": "neutral",
    "sentiment_confidence": 0.8,
    "emotions": [],
    "feedback": [],
    "suggestions": [],
    "is_successful": true
}}"""

    def _create_intent_prompt(self, conversation: Conversation) -> str:
        """Create intent analysis prompt for Groq using only first user message."""
        # Get only the first user message (the initial request)
        user_blocks = [block for block in conversation.blocks if block.block_type == BlockType.USER]
        
        if user_blocks:
            first_user_message = user_blocks[0].text[:500]  # Limit to 500 chars
        else:
            # Fallback to full_text if no user blocks found
            first_user_message = conversation.full_text[:500]
        
        intent_options = ", ".join([intent.value for intent in IntentType])
        
        return f"""Analyze the USER INTENT from the FIRST user message:

User Request: "{first_user_message}"

Identify the PRIMARY intent of this initial user request. Choose from these options:
{intent_options}

Intent Descriptions:
- technical_help: User needs help with technical issues, bugs, or system problems
- process_question: User asks about business processes, procedures, or workflows  
- general_info: User requests general information, facts, or explanations
- product_info: User asks about products, services, features, or specifications
- organization_info: User requests information about company structure, departments, or people
- source_request: User asks for sources, references, or documentation
- statistics: User requests metrics, reports, or statistical data
- coordination: User wants to coordinate activities, schedules, or collaborate
- feedback: User provides feedback, complaints, or suggestions
- project_task: User discusses specific project work or task assignments
- task_management: User manages personal tasks, reminders, or to-dos
- hr_request: User has HR-related questions (hiring, policies, benefits, etc.)
- meeting_management: User schedules, manages, or asks about meetings
- faq_usage: User asks how to use the system or needs basic help
- design_request: User requests visual materials, presentations, or design work

JSON format:
{{
    "intent": "general_info"
}}"""

    def _parse_ux_analysis(self, analysis_text: str) -> UX:
        """Parse structured JSON response to UX object."""
        try:
            # Parse JSON directly
            parsed_data = json.loads(analysis_text)

            # Create UX object with parsed data
            return UX(
                sentiment=self._parse_sentiment(
                    parsed_data.get("sentiment", "neutral")
                ),
                sentiment_confidence=float(
                    parsed_data.get("sentiment_confidence", 0.5)
                ),
                emotions=[
                    EmotionType(e)
                    for e in parsed_data.get("emotions", [])
                    if e in [em.value for em in EmotionType]
                ],
                feedback=parsed_data.get("feedback", []),
                suggestions=parsed_data.get("suggestions", []),
                is_successful=parsed_data.get("is_successful", True),
            )
        except Exception as e:
            self._log_ux_parsing_error(e)
            return self._default_ux_analysis()

    def _parse_sentiment(self, sentiment_str: str) -> SentimentType:
        """Parse sentiment string to SentimentType."""
        sentiment_map = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)

    def _default_ux_analysis(self) -> UX:
        """Return default UX analysis when parsing fails."""
        return UX(
            sentiment=SentimentType.NEUTRAL,
            sentiment_confidence=0.5,
            emotions=[],
            feedback=[],
            suggestions=[],
            is_successful=True,
        )

    def _parse_intent_analysis(self, analysis_text: str) -> RequestCategory:
        """Parse intent analysis JSON response to RequestCategory object."""
        try:
            parsed_data = json.loads(analysis_text)
            intent_str = parsed_data.get("intent", "general_info")
            
            # Parse intent
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.GENERAL_INFO
            
            # Auto-determine category based on intent
            category = get_category_for_intent(intent)
            
            return RequestCategory(
                category=[category],
                intent=[intent]
            )
        except Exception as e:
            self._log_intent_parsing_error(e)
            return self._default_request_category()

    def _default_request_category(self) -> RequestCategory:
        """Return default request category when parsing fails."""
        return RequestCategory(
            category=[CategoryType.OTHER],
            intent=[IntentType.GENERAL_INFO]
        )

    def _log_client_setup(self) -> None:
        """Log successful client setup."""
        print(f"Successfully initialized Groq client with {self.model_name}")

    def _log_client_error(self, error: Exception) -> None:
        """Log client setup error."""
        print(f"Error initializing Groq client: {error}")

    def _log_processing_error(self, dialogue_id: int, error: Exception) -> None:
        """Log conversation processing error."""
        print(f"Error processing conversation {dialogue_id}: {error}")

    def _log_rate_limit_wait(self, dialogue_id: int, wait_time: float, attempt: int, max_retries: int) -> None:
        """Log rate limit wait."""
        print(f"Rate limit hit for conversation {dialogue_id}, waiting {wait_time:.2f}s (attempt {attempt}/{max_retries})")

    def _log_rate_limit_exceeded(self, dialogue_id: int, max_retries: int) -> None:
        """Log rate limit exceeded."""
        print(f"Rate limit exceeded for conversation {dialogue_id} after {max_retries} attempts")

    def _log_ux_parsing_error(self, error: Exception) -> None:
        """Log UX parsing error."""
        print(f"Error parsing UX analysis: {error}")

    def _log_intent_parsing_error(self, error: Exception) -> None:
        """Log intent parsing error."""
        print(f"Error parsing intent analysis: {error}")
