from openai import OpenAI
from typing import Optional
import json
from .conv.conversation import Conversation, ConversationMap


class ConversationMapper:
    """Maps conversations using OpenAI structured output"""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()

    def map_conversation(self, conversation: Conversation) -> Conversation:
        """
        Process a conversation with OpenAI structured output to fulfill mapping

        Args:
            conversation: The conversation object to analyze

        Returns:
            Conversation object with filled analysis field
        """
        # Create the system prompt for analysis
        system_prompt = """You are an expert conversation analyst. Analyze the given conversation and provide structured analysis based on the following categories:

1. Sentiment: Determine if the conversation is positive, negative, or neutral
   - Positive: gratitude ("спасибо", "благодарю"), satisfaction ("отлично", "хорошо")
   - Negative: frustration ("не работает", "проблема"), complaints
   - Neutral: informational requests, routine interactions

2. Emotions: Identify emotions present (frustration, satisfaction, confusion, urgency)
   - Only mark emotions with clear indicators in the text

3. Problems: Detect problem types - BE SPECIFIC:
   - user_confusion: ONLY when user explicitly states confusion or asks for clarification multiple times
   - technical_issues: system errors, functionality problems
   - system_limitations: features not available
   - process_inefficiency: slow or cumbersome workflows
   - communication_failure: misunderstandings, unclear responses

4. Categories: Classify the conversation more precisely:
   - tech_support: technical problems, system issues
   - project_tasks: work assignments, project management
   - information: general information requests
   - hr: HR-related queries
   - organizational: company policies, procedures
   - communication: coordination, meetings, discussions
   - other: only when none of the above fit

5. Intent: Identify the intent more specifically:
   - technical_help: solving technical problems
   - process_question: how to do something
   - project_task: task assignment or status
   - general_info: requesting information
   - coordination: scheduling, planning

6. Problem severity: Rate from 0-10 with clear criteria:
   - 0-2: No problems, successful information exchange
   - 3-4: Minor clarifications needed, slight confusion
   - 5-6: Moderate issues, some user frustration, multiple attempts
   - 7-8: Significant problems, user clearly frustrated, multiple failures
   - 9-10: Critical failures, system completely unhelpful

7. Feedback: Extract any user feedback about the agent system performance, behavior, or interactions (dont write anything if there is no feedback)
8. Suggestions: Extract any user suggestions for improving the agent system or conversation experience (dont write anything if there is no suggestions)

9. Success evaluation: Mark as successful (true) when:
   - User's request was clearly fulfilled
   - User expressed satisfaction or gratitude
   - Task was completed without significant issues
   - Information was successfully provided
   Mark as unsuccessful (false) when:
   - User's request was not fulfilled
   - Multiple failed attempts occurred
   - User expressed frustration or dissatisfaction
   - System could not provide needed help
   
Note: is_successful and problem_severity are related but measure different aspects:
- is_successful: whether the interaction achieved its goal
- problem_severity: how difficult/problematic the process was

Provide confidence scores based on clear textual evidence"""

        user_prompt = f"""
        Analyze this conversation:
        
        Duration: {conversation.duration_minutes} minutes
        Message Count: {conversation.message_count}
        
        Full Conversation Text:
        {conversation.full_text}
        
        Please provide a comprehensive analysis following the structured format.
        """

        try:
            # Make API call with structured output
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=ConversationMap,
            )

            # Extract the parsed response
            analysis = response.choices[0].message.parsed

            # Create a copy of the conversation with analysis
            conversation_copy = conversation.model_copy()
            conversation_copy.analysis = analysis

            return conversation_copy

        except Exception as e:
            # Handle API errors gracefully
            print(f"Error processing conversation {conversation.dialogue_id}: {e}")
            return conversation

    def batch_map_conversations(
        self, conversations: list[Conversation]
    ) -> list[Conversation]:
        """
        Process multiple conversations in batch

        Args:
            conversations: List of conversation objects to analyze

        Returns:
            List of conversation objects with filled analysis fields
        """
        mapped_conversations = []

        for conversation in conversations:
            mapped_conversation = self.map_conversation(conversation)
            mapped_conversations.append(mapped_conversation)

        return mapped_conversations


def create_conversation_mapper(
    openai_client: Optional[OpenAI] = None,
) -> ConversationMapper:
    """Factory function to create a ConversationMapper instance"""
    return ConversationMapper(openai_client)
