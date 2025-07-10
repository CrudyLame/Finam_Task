"""
Simple Groq conversation processor with concurrent processing and progress tracking.
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict, Tuple

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
        results_file: str = "analyzed_conversations_groq.json",
    ):
        """
        Initialize the Groq processor.

        Args:
            api_key: Groq API key
            model_name: Groq model name
            max_concurrent_requests: Maximum concurrent API requests
            batch_size: Number of conversations to process before saving
            results_file: File to store results
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_concurrent_requests = max_concurrent_requests
        self.batch_size = batch_size
        self.results_file = results_file
        self.progress_file = "processing_progress_groq.json"

    def conversation_to_dict(self, conv: Conversation) -> dict:
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
            "analysis": None,
        }

        if conv.analysis:
            result["analysis"] = {
                "sentiment": conv.analysis.sentiment,
                "sentiment_confidence": conv.analysis.sentiment_confidence,
                "emotions": conv.analysis.emotions,
                "problems": conv.analysis.problems,
                "problem_severity": conv.analysis.problem_severity,
                "problem_extra_info": conv.analysis.problem_extra_info,
                "category": conv.analysis.category,
                "intent": conv.analysis.intent,
                "feedback": conv.analysis.feedback,
                "suggestions": conv.analysis.suggestions,
                "is_successful": conv.analysis.is_successful,
            }

        return result

    def save_progress(self, current_index: int, total_count: int):
        """Save current progress to file."""
        progress_data = {
            "current_index": current_index,
            "total_count": total_count,
            "timestamp": datetime.now().isoformat(),
            "results_file": self.results_file,
        }

        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    def load_progress(self) -> Dict:
        """Load progress from file if exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_results(self, conversations_dict: List[Dict], append_mode: bool = False):
        """Save results to JSON file."""
        if append_mode and os.path.exists(self.results_file):
            # Load existing data and append
            try:
                with open(self.results_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

                existing_data["conversations"].extend(conversations_dict)
                existing_data["metadata"]["total_conversations"] = len(
                    existing_data["conversations"]
                )
                existing_data["metadata"]["last_updated"] = datetime.now().isoformat()

                output_data = existing_data
            except:
                output_data = self._create_output_data(conversations_dict)
        else:
            output_data = self._create_output_data(conversations_dict)

        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    def _create_output_data(self, conversations_dict: List[Dict]) -> Dict:
        """Create output data structure."""
        return {
            "metadata": {
                "total_conversations": len(conversations_dict),
                "processed_at": datetime.now().isoformat(),
                "llm_provider": "groq",
                "model": self.model_name,
                "source_file": "data/data.csv",
            },
            "conversations": conversations_dict,
        }

    def process_conversation_sync(self, args: Tuple[Conversation, GroqMapper]) -> Dict:
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

    async def process_all_conversations(
        self, conversations: List[Conversation], start_index: int = 0
    ) -> List[Dict]:
        """Process all conversations with Groq."""

        print(f"Starting Groq processing from index {start_index}")
        print(f"Total conversations to process: {len(conversations) - start_index}")

        # Initialize Groq mapper
        mapper = GroqMapper(api_key=self.api_key, model_name=self.model_name)

        total_processed = start_index

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

                # Collect results
                batch_processed = []
                successful_count = 0
                failed_count = 0

                for j, future in enumerate(futures):
                    try:
                        result = future.result(timeout=120)

                        if result["success"]:
                            conv_dict = self.conversation_to_dict(
                                result["conversation"]
                            )
                            batch_processed.append(conv_dict)
                            successful_count += 1
                        else:
                            print(
                                f"Failed to process conversation {batch[j].dialogue_id}: {result['error']}"
                            )
                            failed_count += 1

                            # Add failed conversation with default analysis
                            conv_dict = self.conversation_to_dict(
                                result["conversation"]
                            )
                            if conv_dict["analysis"] is None:
                                conv_dict["analysis"] = {
                                    "sentiment": "neutral",
                                    "sentiment_confidence": 0.0,
                                    "emotions": [],
                                    "problems": [],
                                    "problem_severity": 0,
                                    "problem_extra_info": "Failed to analyze",
                                    "category": ["other"],
                                    "intent": ["general_info"],
                                    "feedback": [],
                                    "suggestions": [],
                                    "is_successful": False,
                                }
                            batch_processed.append(conv_dict)

                        # Progress indicator
                        if (j + 1) % 5 == 0:
                            print(f"  Completed {j + 1}/{len(batch)} in batch")

                    except Exception as e:
                        print(
                            f"Error processing conversation {batch[j].dialogue_id}: {e}"
                        )
                        failed_count += 1

                        conv_dict = self.conversation_to_dict(batch[j])
                        batch_processed.append(conv_dict)

                batch_time = time.time() - batch_start_time

                # Save batch results incrementally
                if start_index == 0 and i == 0:
                    self.save_results(batch_processed, append_mode=False)
                else:
                    self.save_results(batch_processed, append_mode=True)

                total_processed += len(batch)

                # Save progress
                self.save_progress(total_processed, len(conversations))

                print(f"  Batch completed in {batch_time:.2f}s")
                print(f"  Successful: {successful_count}, Failed: {failed_count}")
                print(f"  Total processed: {total_processed}/{len(conversations)}")

                # Brief pause to avoid overwhelming the API
                await asyncio.sleep(1)

        print(f"\\nProcessing complete! Total processed: {total_processed}")

        # Load and return final results
        with open(self.results_file, "r", encoding="utf-8") as f:
            final_data = json.load(f)

        return final_data["conversations"]

    def get_resume_info(self, conversations_count: int) -> Tuple[bool, int]:
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

    def cleanup_progress(self):
        """Clean up progress file."""
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print(f"Cleaned up {self.progress_file}")
