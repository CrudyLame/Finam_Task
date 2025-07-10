import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from .conversation import Conversation, ConvBlock


class ConversationParser:
    """Parses CSV data into Conversation objects"""
    
    def __init__(self, csv_file_path: str, time_threshold_minutes: int = 30):
        self.csv_file_path = csv_file_path
        self.time_threshold = timedelta(minutes=time_threshold_minutes)
        self.logger = logging.getLogger(__name__)
        
        # Load data
        self.df = pd.read_csv(csv_file_path, sep=';')
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
    def segment_conversations(self) -> pd.DataFrame:
        """
        Segment events into conversations based on:
        1. Time gaps > threshold
        2. Previous block_type == 'response' and current == 'request'
        """
        df_with_conversations = self.df.copy()
        df_with_conversations['dialogue_id'] = 0
        
        current_dialogue_id = 1
        
        for user_id in df_with_conversations['user_id'].unique():
            user_mask = df_with_conversations['user_id'] == user_id
            user_data = df_with_conversations[user_mask].sort_values('timestamp').reset_index(drop=True)
            
            dialogue_ids = []
            current_id = current_dialogue_id
            
            for idx in range(len(user_data)):
                if idx == 0:
                    dialogue_ids.append(current_id)
                    continue
                
                row = user_data.iloc[idx]
                prev_row = user_data.iloc[idx - 1]
                time_diff = row['timestamp'] - prev_row['timestamp']
                
                # Start new conversation if time gap > threshold OR previous was response and current is request
                if (time_diff > self.time_threshold or 
                    (prev_row['block_type'] == 'response' and row['block_type'] == 'request')):
                    current_id += 1
                
                dialogue_ids.append(current_id)
            
            df_with_conversations.loc[user_mask, 'dialogue_id'] = dialogue_ids
            current_dialogue_id = current_id + 1
        
        return df_with_conversations
    
    def parse_conversations(self) -> List[Conversation]:
        """Parse CSV data into Conversation objects"""
        df_segmented = self.segment_conversations()
        conversations = []
        
        for dialogue_id in df_segmented['dialogue_id'].unique():
            conversation_data = df_segmented[df_segmented['dialogue_id'] == dialogue_id].sort_values('timestamp')
            
            if len(conversation_data) == 0:
                continue
            
            # Extract conversation metadata
            user_id = conversation_data['user_id'].iloc[0]
            start_time = conversation_data['timestamp'].min()
            end_time = conversation_data['timestamp'].max()
            duration_minutes = (end_time - start_time).total_seconds() / 60
            message_count = len(conversation_data)
            
            # Combine all block_data into full_text with deduplication (for backward compatibility)
            unique_blocks = []
            seen_blocks = set()
            for block in conversation_data['block_data'].astype(str):
                if block not in seen_blocks:
                    unique_blocks.append(block)
                    seen_blocks.add(block)
            full_text = '\n'.join(unique_blocks)
            
            # Create ConvBlock objects for the new structure
            blocks = []
            seen_block_texts = set()
            for _, row in conversation_data.iterrows():
                block_data = str(row['block_data'])
                block_type = row['block_type']
                
                # Avoid duplicates
                if block_data not in seen_block_texts:
                    conv_block = ConvBlock.from_csv_block(block_data, block_type)
                    blocks.append(conv_block)
                    seen_block_texts.add(block_data)
            
            # Extract departments
            departments = conversation_data['nnDepartment'].dropna().unique().tolist()
            
            # Create Conversation object
            conversation = Conversation(
                dialogue_id=dialogue_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                message_count=message_count,
                full_text=full_text,
                blocks=blocks,
                departments=departments
            )
            
            # Update agent types based on blocks
            conversation.update_agent_types()
            
            conversations.append(conversation)
        
        return conversations
    
    def get_conversation_stats(self, conversations: List[Conversation]) -> dict:
        """Get basic statistics about parsed conversations"""
        if not conversations:
            return {}
        
        total_conversations = len(conversations)
        total_messages = sum(c.message_count for c in conversations)
        unique_users = len(set(c.user_id for c in conversations))
        avg_duration = sum(c.duration_minutes for c in conversations) / total_conversations
        avg_message_count = total_messages / total_conversations
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'unique_users': unique_users,
            'avg_duration_minutes': avg_duration,
            'avg_message_count': avg_message_count
        }
    
