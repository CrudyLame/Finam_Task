"""
Shared utilities for the Finam analytics dashboard
"""

import json
import streamlit as st
from pathlib import Path
from collections import Counter
from datetime import datetime
import numpy as np


@st.cache_data
def load_conversation_data():
	"""Load and cache conversation data"""
	data_path = Path(__file__).parent / "conversations_data.json"
	with open(data_path, 'r', encoding='utf-8') as f:
		data = json.load(f)
	return data


def get_category_stats(conversations):
	"""Extract category statistics from conversations"""
	categories = []
	intents = []
	
	for conv in conversations:
		if 'analysis' in conv and 'request' in conv['analysis']:
			request_analysis = conv['analysis']['request']
			categories.extend(request_analysis.get('category', []))
			intents.extend(request_analysis.get('intent', []))
	
	return Counter(categories), Counter(intents)


def get_problems_stats(conversations):
	"""Extract problems statistics from conversations"""
	problems = []
	
	for conv in conversations:
		if 'analysis' in conv and 'problems' in conv['analysis']:
			problems.extend(conv['analysis']['problems'].get('problems', []))
	
	return Counter(problems)


def get_ux_stats(conversations):
	"""Extract UX and sentiment statistics from conversations"""
	sentiments = []
	emotions = []
	success_rates = []
	feedback_count = 0
	suggestions_count = 0
	
	for conv in conversations:
		if 'analysis' in conv and 'ux' in conv['analysis']:
			ux_analysis = conv['analysis']['ux']
			if 'sentiment' in ux_analysis:
				sentiments.append(ux_analysis['sentiment'])
			emotions.extend(ux_analysis.get('emotions', []))
			success_rates.append(ux_analysis.get('is_successful', False))
			feedback_count += len(ux_analysis.get('feedback', []))
			suggestions_count += len(ux_analysis.get('suggestions', []))
	
	return {
		'sentiments': Counter(sentiments),
		'emotions': Counter(emotions),
		'success_rate': sum(success_rates) / len(success_rates) if success_rates else 0,
		'feedback_count': feedback_count,
		'suggestions_count': suggestions_count
	}


def get_basic_metrics(conversations):
	"""Calculate basic conversation metrics"""
	avg_duration = np.mean([conv['duration_minutes'] for conv in conversations])
	avg_messages = np.mean([conv['message_count'] for conv in conversations])
	unique_users = len(set(conv['user_id'] for conv in conversations))
	
	return {
		'avg_duration': avg_duration,
		'avg_messages': avg_messages,
		'unique_users': unique_users
	}


def get_agent_performance_data(conversations):
	"""Extract agent performance data"""
	agent_data = []
	
	for conv in conversations:
		agent_types = conv.get('agent_types', [])
		is_successful = False
		if 'analysis' in conv and 'ux' in conv['analysis']:
			is_successful = conv['analysis']['ux'].get('is_successful', False)
		
		if agent_types:
			for agent in agent_types:
				agent_data.append({
					'agent': agent,
					'success': is_successful,
					'duration': conv['duration_minutes'],
					'messages': conv['message_count']
				})
	
	return agent_data


def get_timeline_data(conversations):
	"""Extract timeline data for conversations"""
	dates = [datetime.fromisoformat(conv['start_time']).date() for conv in conversations]
	return Counter(dates)


def get_sentiment_timeline(conversations):
	"""Extract sentiment timeline data"""
	sentiment_timeline = []
	
	for conv in conversations:
		if 'analysis' in conv and 'ux' in conv['analysis']:
			ux_analysis = conv['analysis']['ux']
			if 'sentiment' in ux_analysis:
				sentiment_timeline.append({
					'date': datetime.fromisoformat(conv['start_time']).date(),
					'sentiment': ux_analysis['sentiment'],
					'confidence': ux_analysis.get('sentiment_confidence', 0)
				})
	
	return sentiment_timeline