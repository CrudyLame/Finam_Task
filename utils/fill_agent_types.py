#!/usr/bin/env python3
"""
Script to fill agent_type fields in conversations_parsed.json
using the same agent detection logic from utils/conv/conversation.py
"""

import json
from typing import Optional
from enum import Enum


class AgentType(str, Enum):
	"""Agent types for conversation blocks"""
	
	SUPERVISOR = "supervisor"
	FACTS = "facts"
	QUESTIONS = "questions"
	DEPARTMENTS = "departments"
	PRODUCTS = "products"
	TASKS = "tasks"
	MEETINGS = "meetings"
	HR = "hr"
	FAQ = "faq"
	FEEDBACK = "feedback"
	SOURCES = "sources"
	STATISTIC = "statistic"
	DESIGNER = "designer"


def extract_agent_type(block_data: str) -> Optional[str]:
	"""Extract agent type from block data by searching for agent names"""
	agent_names = {
		"Supervisor": AgentType.SUPERVISOR,
		"Facts assistant": AgentType.FACTS,
		"Questions assistant": AgentType.QUESTIONS,
		"Departments assistant": AgentType.DEPARTMENTS,
		"Products assistant": AgentType.PRODUCTS,
		"Tasks assistant": AgentType.TASKS,
		"Meetings assistant": AgentType.MEETINGS,
		"HR assistant": AgentType.HR,
		"FAQ assistant": AgentType.FAQ,
		"Feedback assistant": AgentType.FEEDBACK,
		"Sources assistant": AgentType.SOURCES,
		"Statistic assistant": AgentType.STATISTIC,
		"Designer assistant": AgentType.DESIGNER
	}
	
	# Search for agent names in the block data
	for agent_name, agent_type in agent_names.items():
		if agent_name in block_data:
			return agent_type.value
	
	return None


def fill_agent_types(input_file: str, output_file: str = None):
	"""Fill agent_type fields in conversations JSON file"""
	if output_file is None:
		output_file = input_file
	
	print(f"Loading conversations from {input_file}...")
	
	# Load the JSON file
	with open(input_file, 'r', encoding='utf-8') as f:
		data = json.load(f)
	
	conversations = data.get('conversations', [])
	total_conversations = len(conversations)
	updated_blocks = 0
	filled_agent_types = 0
	
	print(f"Processing {total_conversations} conversations...")
	
	# Process each conversation
	for conv_idx, conversation in enumerate(conversations):
		if conv_idx % 100 == 0:
			print(f"Progress: {conv_idx}/{total_conversations} conversations processed")
		
		blocks = conversation.get('blocks', [])
		conversation_agent_types = set()
		
		# Process each block
		for block in blocks:
			updated_blocks += 1
			
			# Only process blocks that don't already have agent_type set
			if block.get('agent_type') is None:
				block_type = block.get('block_type', '')
				text = block.get('text', '')
				
				# For system blocks, try to extract agent type
				if block_type == 'system' and text:
					agent_type = extract_agent_type(text)
					if agent_type:
						block['agent_type'] = agent_type
						conversation_agent_types.add(agent_type)
						filled_agent_types += 1
		
		# Update conversation-level agent_types list
		if conversation_agent_types:
			existing_agent_types = set(conversation.get('agent_types', []))
			existing_agent_types.update(conversation_agent_types)
			conversation['agent_types'] = list(existing_agent_types)
	
	# Update metadata
	if 'metadata' in data:
		data['metadata']['last_updated'] = "2025-07-10T20:00:00.000000"
	
	print(f"\nResults:")
	print(f"- Total conversations processed: {total_conversations}")
	print(f"- Total blocks processed: {updated_blocks}")
	print(f"- Agent types filled: {filled_agent_types}")
	
	# Save the updated JSON
	print(f"\nSaving updated conversations to {output_file}...")
	with open(output_file, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)
	
	print("Done!")


if __name__ == "__main__":
	input_file = "conversations_parsed.json"
	fill_agent_types(input_file)