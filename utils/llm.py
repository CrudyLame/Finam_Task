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
2. Emotions: Identify emotions present (frustration, satisfaction, confusion, urgency)
3. Problems: Detect problem types (technical_issues, user_confusion, system_limitations, process_inefficiency, communication_failure)
4. Categories: Classify the conversation (information, communication, other, project_tasks, hr, organizational, tech_support)
5. Intent: Identify the intent (technical_help, process_question, project_task, general_info, coordination)
7. Problem severity: Rate from 0-10 (0 = no problems, 10 = critical issues)
8. Feedback: Extract any user feedback about the agent system performance, behavior, or interactions (dont write anything if there is no feedback)
9. Suggestions: Extract any user suggestions for improving the agent system or conversation experience (dont write anything if there is no suggestions)

Provide confidence scores"""

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
