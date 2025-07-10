"""
Enhanced conversation processor with concurrent processing, progress tracking, and incremental saving.
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from .conv.conversation import Conversation
from .llm import ConversationMapper
from .llm_local import create_mapper


class ConversationProcessor:
    """Enhanced conversation processor with concurrent processing and progress tracking."""
    
    def __init__(self, 
                 max_concurrent_requests: int = 10,
                 batch_size: int = 50,
                 progress_file: str = "processing_progress.json",
                 results_file: str = "analyzed_conversations_incremental.json",
                 llm_provider: str = "openai",
                 **llm_kwargs):
        """
        Initialize the processor.
        
        Args:
            max_concurrent_requests: Maximum concurrent API requests
            batch_size: Number of conversations to process before saving
            progress_file: File to store progress information
            results_file: File to store results
            llm_provider: LLM provider ('openai', 'huggingface', 'groq', 'ollama')
            **llm_kwargs: Provider-specific arguments
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.batch_size = batch_size
        self.progress_file = progress_file
        self.results_file = results_file
        self.llm_provider = llm_provider
        self.llm_kwargs = llm_kwargs
        
    def conversation_to_dict(self, conv: Conversation) -> dict:
        """Convert Conversation object to dictionary for JSON serialization."""
        result = {
            'dialogue_id': conv.dialogue_id,
            'user_id': conv.user_id,
            'start_time': conv.start_time.isoformat(),
            'end_time': conv.end_time.isoformat(),
            'duration_minutes': conv.duration_minutes,
            'message_count': conv.message_count,
            'full_text': conv.full_text,
            'departments': conv.departments,
            'analysis': None
        }
        
        if conv.analysis:
            result['analysis'] = {
                'sentiment': conv.analysis.sentiment,
                'sentiment_confidence': conv.analysis.sentiment_confidence,
                'emotions': conv.analysis.emotions,
                'problems': conv.analysis.problems,
                'problem_severity': conv.analysis.problem_severity,
                'problem_extra_info': conv.analysis.problem_extra_info,
                'success_indicators': conv.analysis.success_indicators,
                'failure_indicators': conv.analysis.failure_indicators,
                'category': conv.analysis.category,
                'intent': conv.analysis.intent,
                'feedback': conv.analysis.feedback,
                'suggestions': conv.analysis.suggestions,
                'analysis_explanation': conv.analysis.analysis_explanation
            }
        
        return result
    
    def save_progress(self, current_index: int, total_count: int, processed_count: int):
        """Save current progress to file."""
        progress_data = {
            'current_index': current_index,
            'total_count': total_count,
            'processed_count': processed_count,
            'timestamp': datetime.now().isoformat(),
            'results_file': self.results_file
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    def load_progress(self) -> Optional[Dict]:
        """Load progress from file if exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def create_output_data(self, conversations_dict: List[Dict]) -> Dict:
        """Create output data structure."""
        return {
            'metadata': {
                'total_conversations': len(conversations_dict),
                'processed_at': datetime.now().isoformat(),
                'source_file': 'data/data.csv',
                'time_threshold_minutes': 30
            },
            'conversations': conversations_dict
        }
    
    def save_results(self, conversations_dict: List[Dict], append_mode: bool = False):
        """Save results to JSON file."""
        if append_mode and os.path.exists(self.results_file):
            # Load existing data and append
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # Append new conversations
                existing_data['conversations'].extend(conversations_dict)
                existing_data['metadata']['total_conversations'] = len(existing_data['conversations'])
                existing_data['metadata']['last_updated'] = datetime.now().isoformat()
                
                output_data = existing_data
            except:
                # If file is corrupted, create new
                output_data = self.create_output_data(conversations_dict)
        else:
            output_data = self.create_output_data(conversations_dict)
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def process_conversation_sync(self, args: Tuple[Conversation, Any]) -> Dict:
        """Synchronous wrapper for processing a single conversation."""
        conversation, mapper = args
        try:
            start_time = time.time()
            analyzed_conv = mapper.map_conversation(conversation)
            processing_time = time.time() - start_time
            
            return {
                'conversation': analyzed_conv,
                'success': True,
                'processing_time': processing_time,
                'error': None
            }
        except Exception as e:
            return {
                'conversation': conversation,
                'success': False,
                'processing_time': 0,
                'error': str(e)
            }
    
    async def process_conversations_concurrent(self, 
                                             conversations: List[Conversation], 
                                             start_index: int = 0) -> List[Dict]:
        """Process conversations with concurrent execution and progress saving."""
        
        print(f"Starting concurrent processing from index {start_index}")
        print(f"Total conversations to process: {len(conversations) - start_index}")
        
        # Initialize mapper
        mapper = create_mapper(self.llm_provider, **self.llm_kwargs)
        
        # Process conversations in batches
        total_processed = start_index
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            # Process conversations in batches
            for i in range(start_index, len(conversations), self.batch_size):
                batch_end = min(i + self.batch_size, len(conversations))
                batch = conversations[i:batch_end]
                
                print(f"\nProcessing batch {i//self.batch_size + 1}: conversations {i+1}-{batch_end}")
                
                # Prepare arguments for concurrent processing
                batch_args = [(conv, mapper) for conv in batch]
                
                # Submit batch for concurrent processing
                batch_start_time = time.time()
                futures = [executor.submit(self.process_conversation_sync, args) for args in batch_args]
                
                # Collect results with progress tracking
                batch_processed = []
                successful_count = 0
                failed_count = 0
                
                for j, future in enumerate(futures):
                    try:
                        result = future.result(timeout=120)  # 2 minute timeout per conversation
                        
                        if result['success']:
                            # Convert to dict and add to batch
                            conv_dict = self.conversation_to_dict(result['conversation'])
                            batch_processed.append(conv_dict)
                            successful_count += 1
                        else:
                            print(f"Failed to process conversation {batch[j].dialogue_id}: {result['error']}")
                            failed_count += 1
                            
                            # Still add failed conversation without analysis
                            conv_dict = self.conversation_to_dict(result['conversation'])
                            batch_processed.append(conv_dict)
                        
                        # Progress indicator
                        if (j + 1) % 5 == 0:
                            print(f"  Completed {j + 1}/{len(batch)} in batch")
                            
                    except Exception as e:
                        print(f"Error processing conversation {batch[j].dialogue_id}: {e}")
                        failed_count += 1
                        
                        # Add failed conversation without analysis
                        conv_dict = self.conversation_to_dict(batch[j])
                        batch_processed.append(conv_dict)
                
                batch_time = time.time() - batch_start_time
                
                # Save batch results incrementally
                if start_index == 0 and i == 0:
                    # First batch - create new file
                    self.save_results(batch_processed, append_mode=False)
                else:
                    # Append to existing file
                    self.save_results(batch_processed, append_mode=True)
                
                total_processed += len(batch)
                
                # Save progress
                self.save_progress(total_processed, len(conversations), total_processed - start_index)
                
                print(f"  Batch completed in {batch_time:.2f}s")
                print(f"  Successful: {successful_count}, Failed: {failed_count}")
                print(f"  Total processed: {total_processed}/{len(conversations)}")
                
                # Brief pause to avoid overwhelming the API
                await asyncio.sleep(1)
        
        print(f"\nProcessing complete! Total processed: {total_processed}")
        
        # Load and return final results
        with open(self.results_file, 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        
        return final_data['conversations']
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics."""
        progress = self.load_progress()
        if progress:
            return {
                'has_progress': True,
                'current_index': progress.get('current_index', 0),
                'total_count': progress.get('total_count', 0),
                'processed_count': progress.get('processed_count', 0),
                'timestamp': progress.get('timestamp', ''),
                'results_file': progress.get('results_file', self.results_file)
            }
        return {'has_progress': False}
    
    def cleanup_progress(self):
        """Clean up progress and temporary files."""
        for file in [self.progress_file]:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up {file}")
    
    def resume_processing_prompt(self, conversations_count: int) -> Tuple[bool, int]:
        """
        Handle resume processing prompt and return (should_resume, start_index).
        
        Args:
            conversations_count: Total number of conversations
            
        Returns:
            Tuple of (should_resume, start_index)
        """
        progress = self.load_progress()
        start_index = 0
        
        if progress:
            print(f"Found existing progress: {progress['processed_count']}/{progress['total_count']} conversations processed")
            resume = input("Resume from where you left off? (y/n): ").strip().lower()
            
            if resume == 'y':
                start_index = progress['current_index']
                print(f"Resuming from conversation {start_index}")
                return True, start_index
            else:
                print("Starting fresh processing")
                # Clean up old files
                self.cleanup_progress()
                if os.path.exists(self.results_file):
                    os.remove(self.results_file)
                return False, 0
        else:
            print("No existing progress found, starting fresh")
            return False, 0
    
    def get_user_confirmation(self, conversations_count: int, start_index: int) -> bool:
        """Get user confirmation for processing."""
        remaining_count = conversations_count - start_index
        process_all = input(f"Process {'remaining ' if start_index > 0 else 'all '}{remaining_count} conversations? This will use OpenAI API credits. (y/n): ")
        return process_all.lower() == 'y'