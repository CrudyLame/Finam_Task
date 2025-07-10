"""
Simple Groq conversation processor with concurrent processing and progress tracking.
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Any, Tuple

if TYPE_CHECKING:
    from groq import Groq

from utils.conv.conversation import Conversation
from utils.qroq.groq_mapper import GroqMapper


class GroqProcessor:
    """Simple conversation processor using only Groq for analysis."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "llama3-8b-8192",
        max_concurrent_requests: int = 3,
        batch_size: int = 25,
        conversations_file: str = "conversations_parsed.json",
    ):
        """
        Initialize the Groq processor.

        Args:
            api_key: Groq API key
            model_name: Groq model name
            max_concurrent_requests: Maximum concurrent API requests
            batch_size: Number of conversations to process before saving
            conversations_file: Conversations JSON file to update with UX analysis
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_concurrent_requests = max_concurrent_requests
        self.batch_size = batch_size
        self.conversations_file = conversations_file
        self.progress_file = "processing_progress_groq.json"

    def conversation_to_dict(self, conv: Conversation) -> dict[str, any]:
        """Convert Conversation object to dictionary for JSON serialization."""
        result = {
            "dialogue_id": conv.dialogue_id,
            "user_id": conv.user_id,
            "start_time": conv.start_time.isoformat(),
            "end_time": conv.end_time.isoformat(),
            "duration_minutes": conv.duration_minutes,
            "message_count": conv.message_count,
            "full_text": conv.full_text,
            "departments": conv.departments,
            "blocks": [block.model_dump() for block in conv.blocks] if conv.blocks else [],
            "agent_types": [agent.value for agent in conv.agent_types] if conv.agent_types else [],
            "analysis": None,
        }

        if conv.analysis:
            result["analysis"] = {
                "request": {
                    "category": [cat.value for cat in conv.analysis.request.category],
                    "intent": [intent.value for intent in conv.analysis.request.intent],
                },
                "problems": {
                    "problems": [prob.value for prob in conv.analysis.problems.problems],
                },
                "ux": {
                    "sentiment": conv.analysis.ux.sentiment.value,
                    "sentiment_confidence": conv.analysis.ux.sentiment_confidence,
                    "emotions": [em.value for em in conv.analysis.ux.emotions],
                    "feedback": conv.analysis.ux.feedback,
                    "suggestions": conv.analysis.ux.suggestions,
                    "is_successful": conv.analysis.ux.is_successful,
                }
            }

        return result

    def save_progress(self, current_index: int, total_count: int):
        """Save current progress to file."""
        progress_data = {
            "current_index": current_index,
            "total_count": total_count,
            "timestamp": datetime.now().isoformat(),
            "conversations_file": self.conversations_file,
        }

        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def load_progress(self) -> dict[str, any]:
        """Load progress from file if exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def update_conversations_file(self, updated_conversations: list[Conversation]) -> None:
        """Update the conversations file with UX analysis."""
        # Load existing conversations file
        with open(self.conversations_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Update conversations with new UX analysis
        for i, conv in enumerate(updated_conversations):
            if i < len(data["conversations"]):
                conv_dict = self.conversation_to_dict(conv)
                data["conversations"][i] = conv_dict
        
        # Update metadata
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Save updated file
        with open(self.conversations_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_conversations_from_file(self) -> list[Conversation]:
        """Load conversations from the JSON file."""
        with open(self.conversations_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        conversations = []
        for conv_data in data["conversations"]:
            # Handle datetime fields
            conv_data["start_time"] = datetime.fromisoformat(conv_data["start_time"])
            conv_data["end_time"] = datetime.fromisoformat(conv_data["end_time"])
            
            # Reconstruct conversation object
            conversations.append(Conversation(**conv_data))
        
        return conversations

    def process_conversation_sync(self, args: tuple[Conversation, GroqMapper]) -> dict[str, any]:
        """Synchronous wrapper for processing a single conversation."""
        conversation, mapper = args
        try:
            start_time = time.time()
            analyzed_conv = mapper.map_conversation(conversation)
            processing_time = time.time() - start_time

            return {
                "conversation": analyzed_conv,
                "success": True,
                "processing_time": processing_time,
                "error": None,
            }
        except Exception as e:
            return {
                "conversation": conversation,
                "success": False,
                "processing_time": 0,
                "error": str(e),
            }

    async def process_ux_and_intent_analysis(self, start_index: int = 0) -> list[Conversation]:
        """Process both UX and Intent analysis and update conversations file."""
        
        # Load conversations from file
        conversations = self.load_conversations_from_file()
        
        print(f"Starting Groq UX and Intent processing from index {start_index}")
        print(f"Total conversations to process: {len(conversations) - start_index}")

        # Initialize Groq mapper
        mapper = GroqMapper(api_key=self.api_key, model_name=self.model_name)

        updated_conversations = conversations.copy()
        total_processed = start_index
        
        # Track analysis statistics
        ux_stats = {"positive": 0, "negative": 0, "neutral": 0}
        intent_stats = {}
        successful_analyses = 0

        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            for i in range(start_index, len(conversations), self.batch_size):
                batch_end = min(i + self.batch_size, len(conversations))
                batch = conversations[i:batch_end]

                print(
                    f"\\nProcessing batch {i//self.batch_size + 1}: conversations {i+1}-{batch_end}"
                )

                # Prepare arguments for concurrent processing
                batch_args = [(conv, mapper) for conv in batch]

                # Submit batch for concurrent processing
                batch_start_time = time.time()
                futures = [
                    executor.submit(self.process_conversation_sync, args)
                    for args in batch_args
                ]

                # Collect results and update conversations
                successful_count = 0
                failed_count = 0

                for j, future in enumerate(futures):
                    try:
                        result = future.result(timeout=120)

                        if result["success"]:
                            # Update the conversation in our list
                            analyzed_conv = result["conversation"]
                            updated_conversations[i + j] = analyzed_conv
                            successful_count += 1
                            successful_analyses += 1
                            
                            # Track UX and intent statistics
                            if analyzed_conv.analysis and analyzed_conv.analysis.ux:
                                sentiment = analyzed_conv.analysis.ux.sentiment.value
                                ux_stats[sentiment] = ux_stats.get(sentiment, 0) + 1
                            
                            if analyzed_conv.analysis and analyzed_conv.analysis.request:
                                for intent in analyzed_conv.analysis.request.intent:
                                    intent_stats[intent.value] = intent_stats.get(intent.value, 0) + 1
                        else:
                            print(
                                f"Failed to process conversation {batch[j].dialogue_id}: {result['error']}"
                            )
                            failed_count += 1

                        # Progress indicator
                        if (j + 1) % 5 == 0:
                            print(f"  Completed {j + 1}/{len(batch)} in batch")

                    except Exception as e:
                        print(
                            f"Error processing conversation {batch[j].dialogue_id}: {e}"
                        )
                        failed_count += 1

                batch_time = time.time() - batch_start_time
                total_processed += len(batch)

                # Save progress and update file every batch
                self.save_progress(total_processed, len(conversations))
                self.update_conversations_file(updated_conversations)

                print(f"  Batch completed in {batch_time:.2f}s")
                print(f"  Successful: {successful_count}, Failed: {failed_count}")
                print(f"  Total processed: {total_processed}/{len(conversations)}")

                # Brief pause to avoid overwhelming the API
                await asyncio.sleep(1)

        # Print final statistics
        print(f"\\nUX and Intent processing complete! Total processed: {total_processed}")
        print(f"Successful analyses: {successful_analyses}")
        
        print("\\n=== UX Analysis Results ===")
        for sentiment, count in ux_stats.items():
            percentage = (count / successful_analyses * 100) if successful_analyses > 0 else 0
            print(f"  {sentiment}: {count} ({percentage:.1f}%)")
        
        print("\\n=== Intent Analysis Results ===")
        for intent, count in sorted(intent_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / successful_analyses * 100) if successful_analyses > 0 else 0
            print(f"  {intent}: {count} ({percentage:.1f}%)")
        
        return updated_conversations

    async def process_ux_analysis(self, start_index: int = 0) -> list[Conversation]:
        """Legacy method for backward compatibility. Use process_ux_and_intent_analysis instead."""
        print("Note: process_ux_analysis is deprecated. Using process_ux_and_intent_analysis which includes both UX and Intent analysis.")
        return await self.process_ux_and_intent_analysis(start_index)

    def get_resume_info(self, conversations_count: int) -> tuple[bool, int]:
        """Check if we should resume processing and return start index."""
        progress = self.load_progress()

        if progress and "current_index" in progress:
            print(
                f"Found existing progress: {progress['current_index']}/{progress['total_count']} conversations processed"
            )
            return True, progress["current_index"]
        else:
            print("No existing progress found, starting fresh")
            return False, 0

    def cleanup_progress(self) -> None:
        """Clean up progress file."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print(f"Cleaned up {self.progress_file}")
