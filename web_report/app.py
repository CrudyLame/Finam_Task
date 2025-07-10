import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from collections import Counter
import numpy as np

# Page config
st.set_page_config(
	page_title="Панель Аналитики Finam",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded"
)

@st.cache_data
def load_conversation_data():
	"""Load and cache conversation data"""
	data_path = Path(__file__).parent.parent / "conversations_data.json"
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

def main():
	st.title("📊 Панель Аналитики Мультиагентной Системы Finam")
	
	# Load data
	try:
		data = load_conversation_data()
		conversations = data['conversations']
		metadata = data['metadata']
	except Exception as e:
		st.error(f"Failed to load data: {str(e)}")
		return
	
	# Sidebar navigation
	st.sidebar.title("Навигация")
	page = st.sidebar.selectbox(
		"Выберите тип анализа",
		["Обзор", "Анализ категорий", "Анализ проблем", "UX анализ", "Производительность агентов"]
	)
	
	# Overview metrics
	st.sidebar.markdown("---")
	st.sidebar.metric("Всего диалогов", metadata['total_conversations'])
	st.sidebar.metric("Данные обновлены", metadata['last_updated'][:10])
	
	if page == "Обзор":
		show_overview(conversations, metadata)
	elif page == "Анализ категорий":
		show_category_analysis(conversations)
	elif page == "Анализ проблем":
		show_problems_analysis(conversations)
	elif page == "UX анализ":
		show_ux_analysis(conversations)
	elif page == "Производительность агентов":
		show_agent_performance(conversations)

def show_overview(conversations, metadata):
	st.header("📈 Обзор")
	
	col1, col2, col3, col4 = st.columns(4)
	
	# Basic metrics
	avg_duration = np.mean([conv['duration_minutes'] for conv in conversations])
	avg_messages = np.mean([conv['message_count'] for conv in conversations])
	unique_users = len(set(conv['user_id'] for conv in conversations))
	
	with col1:
		st.metric("Средняя продолжительность (мин)", f"{avg_duration:.2f}")
	with col2:
		st.metric("Среднее кол-во сообщений", f"{avg_messages:.1f}")
	with col3:
		st.metric("Уникальных пользователей", unique_users)
	with col4:
		st.metric("Показатель успеха", f"{get_ux_stats(conversations)['success_rate']:.1%}")
	
	# Timeline analysis
	st.subheader("📅 Хронология диалогов")
	
	# Extract dates and create timeline
	dates = [datetime.fromisoformat(conv['start_time']).date() for conv in conversations]
	date_counts = Counter(dates)
	
	timeline_df = pd.DataFrame(list(date_counts.items()), columns=['Date', 'Count'])
	timeline_df = timeline_df.sort_values('Date')
	
	fig = px.line(timeline_df, x='Date', y='Count', title="Ежедневный объем диалогов")
	st.plotly_chart(fig, use_container_width=True)

def show_category_analysis(conversations):
	st.header("🏷️ Анализ категорий")
	
	categories, intents = get_category_stats(conversations)
	
	col1, col2 = st.columns(2)
	
	with col1:
		st.subheader("Категории запросов")
		if categories:
			fig = px.pie(
				values=list(categories.values()),
				names=list(categories.keys()),
				title="Распределение категорий запросов"
			)
			st.plotly_chart(fig, use_container_width=True)
		else:
			st.info("Нет данных о категориях")
	
	with col2:
		st.subheader("Намерения пользователей")
		if intents:
			fig = px.bar(
				x=list(intents.keys()),
				y=list(intents.values()),
				title="Распределение намерений пользователей"
			)
			st.plotly_chart(fig, use_container_width=True)
		else:
			st.info("Нет данных о намерениях")
	
	# Detailed breakdown
	st.subheader("📊 Подробная разбивка")
	
	if categories:
		category_df = pd.DataFrame(list(categories.items()), columns=['Категория', 'Количество'])
		category_df['Процент'] = (category_df['Количество'] / category_df['Количество'].sum() * 100).round(2)
		st.dataframe(category_df, use_container_width=True)

def show_problems_analysis(conversations):
	st.header("⚠️ Анализ проблем")
	
	problems = get_problems_stats(conversations)
	
	if problems:
		col1, col2 = st.columns([2, 1])
		
		with col1:
			# Problem frequency chart
			fig = px.bar(
				x=list(problems.values()),
				y=list(problems.keys()),
				orientation='h',
				title="Частота возникновения проблем"
			)
			fig.update_layout(yaxis={'categoryorder':'total ascending'})
			st.plotly_chart(fig, use_container_width=True)
		
		with col2:
			st.subheader("Статистика проблем")
			total_problems = sum(problems.values())
			st.metric("Всего случаев проблем", total_problems)
			st.metric("Уникальных типов проблем", len(problems))
			
			# Problem severity (mock classification for demo)
			st.subheader("Критичность проблем")
			high_severity = ["system_error", "data_loss", "security_breach"]
			medium_severity = ["performance_issue", "user_confusion", "timeout"]
			
			high_count = sum(problems.get(p, 0) for p in high_severity)
			medium_count = sum(problems.get(p, 0) for p in medium_severity)
			low_count = total_problems - high_count - medium_count
			
			severity_data = pd.DataFrame({
				'Критичность': ['Высокая', 'Средняя', 'Низкая'],
				'Количество': [high_count, medium_count, low_count]
			})
			
			fig = px.pie(severity_data, values='Количество', names='Критичность', 
						title="Распределение по критичности")
			st.plotly_chart(fig, use_container_width=True)
		
		# Detailed problems table
		st.subheader("📋 Подробный отчет о проблемах")
		problems_df = pd.DataFrame(list(problems.items()), columns=['Тип проблемы', 'Частота'])
		problems_df['Процент'] = (problems_df['Частота'] / problems_df['Частота'].sum() * 100).round(2)
		problems_df = problems_df.sort_values('Частота', ascending=False)
		st.dataframe(problems_df, use_container_width=True)
		
	else:
		st.info("Нет данных о проблемах в диалогах")

def show_ux_analysis(conversations):
	st.header("😊 Анализ пользовательского опыта")
	
	ux_stats = get_ux_stats(conversations)
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.metric("Показатель успеха", f"{ux_stats['success_rate']:.1%}")
	with col2:
		st.metric("Отзывы", ux_stats['feedback_count'])
	with col3:
		st.metric("Предложения", ux_stats['suggestions_count'])
	
	col1, col2 = st.columns(2)
	
	with col1:
		st.subheader("Распределение настроений")
		if ux_stats['sentiments']:
			fig = px.pie(
				values=list(ux_stats['sentiments'].values()),
				names=list(ux_stats['sentiments'].keys()),
				title="Распределение настроений пользователей"
			)
			st.plotly_chart(fig, use_container_width=True)
		else:
			st.info("Нет данных о настроениях")
	
	with col2:
		st.subheader("Эмоции пользователей")
		if ux_stats['emotions']:
			fig = px.bar(
				x=list(ux_stats['emotions'].keys()),
				y=list(ux_stats['emotions'].values()),
				title="Обнаруженные эмоции пользователей"
			)
			st.plotly_chart(fig, use_container_width=True)
		else:
			st.info("Нет данных об эмоциях")
	
	# Sentiment over time
	st.subheader("📈 Тренды настроений")
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
	
	if sentiment_timeline:
		sentiment_df = pd.DataFrame(sentiment_timeline)
		
		# Group by date and calculate sentiment scores
		sentiment_scores = {'positive': 1, 'neutral': 0, 'negative': -1}
		sentiment_df['score'] = sentiment_df['sentiment'].map(sentiment_scores)
		
		daily_sentiment = sentiment_df.groupby('date')['score'].mean().reset_index()
		
		fig = px.line(daily_sentiment, x='date', y='score', 
					 title="Ежедневные тренды настроений",
					 labels={'score': 'Оценка настроения', 'date': 'Дата'})
		fig.add_hline(y=0, line_dash="dash", line_color="gray")
		st.plotly_chart(fig, use_container_width=True)

def show_agent_performance(conversations):
	st.header("🤖 Agent Performance Analysis")
	
	# Extract agent data
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
	
	if agent_data:
		agent_df = pd.DataFrame(agent_data)
		
		col1, col2 = st.columns(2)
		
		with col1:
			# Agent usage frequency
			agent_counts = agent_df['agent'].value_counts()
			fig = px.bar(
				x=agent_counts.index,
				y=agent_counts.values,
				title="Agent Usage Frequency"
			)
			st.plotly_chart(fig, use_container_width=True)
		
		with col2:
			# Agent success rates
			success_rates = agent_df.groupby('agent')['success'].mean()
			fig = px.bar(
				x=success_rates.index,
				y=success_rates.values,
				title="Agent Success Rates"
			)
			fig.update_layout(yaxis=dict(tickformat='.1%'))
			st.plotly_chart(fig, use_container_width=True)
		
		# Performance metrics table
		st.subheader("📊 Agent Performance Metrics")
		performance_metrics = agent_df.groupby('agent').agg({
			'success': ['count', 'mean'],
			'duration': 'mean',
			'messages': 'mean'
		}).round(2)
		
		performance_metrics.columns = ['Total Interactions', 'Success Rate', 'Avg Duration (min)', 'Avg Messages']
		st.dataframe(performance_metrics, use_container_width=True)
		
	else:
		st.info("No agent performance data available")
		st.write("Most conversations appear to be handled without specific agent assignments.")

if __name__ == "__main__":
	main()