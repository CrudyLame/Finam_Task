"""
UX analysis page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_ux_stats, get_sentiment_timeline


def show_ux_analysis(conversations):
	"""Display UX analysis page with sentiment and emotion analysis"""
	st.header("😊 Анализ пользовательского опыта")
	
	# Create tabs
	tab1, tab2 = st.tabs(["📊 Анализ", "💡 Гипотезы"])
	
	with tab1:
		# Description section (empty for user to fill)
		st.subheader("📝 Описание раздела")
		st.info("Это место для описания раздела анализа пользовательского опыта. Заполните по необходимости.")
		
		# Notes section (hardcoded)
		st.subheader("📝 Заметки")
		st.info("Здесь размещаются заметки по анализу пользовательского опыта.")
		
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
		sentiment_timeline = get_sentiment_timeline(conversations)
		
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
			
		# Download buttons for feedback and suggestions
		st.subheader("📥 Скачать данные")
		col_download1, col_download2 = st.columns(2)
		
		with col_download1:
			# Extract all feedback
			all_feedback = []
			for conv in conversations:
				feedback = conv.get('analysis', {}).get('ux', {}).get('feedback', [])
				for fb in feedback:
					all_feedback.append({
						'dialogue_id': conv.get('dialogue_id'),
						'feedback': fb,
						'timestamp': conv.get('start_time')
					})
			
			if all_feedback:
				feedback_df = pd.DataFrame(all_feedback)
				feedback_csv = feedback_df.to_csv(index=False)
				st.download_button(
					label="📥 Скачать отзывы пользователей",
					data=feedback_csv,
					file_name="user_feedback.csv",
					mime="text/csv"
				)
			else:
				st.info("Нет отзывов для скачивания")
		
		with col_download2:
			# Extract all suggestions
			all_suggestions = []
			for conv in conversations:
				suggestions = conv.get('analysis', {}).get('ux', {}).get('suggestions', [])
				for sugg in suggestions:
					all_suggestions.append({
						'dialogue_id': conv.get('dialogue_id'),
						'suggestion': sugg,
						'timestamp': conv.get('start_time')
					})
			
			if all_suggestions:
				suggestions_df = pd.DataFrame(all_suggestions)
				suggestions_csv = suggestions_df.to_csv(index=False)
				st.download_button(
					label="📥 Скачать предложения пользователей",
					data=suggestions_csv,
					file_name="user_suggestions.csv",
					mime="text/csv"
				)
			else:
				st.info("Нет предложений для скачивания")
		
		# Satisfaction by agent system
		st.subheader("🎯 Удовлетворенность по агентским системам")
		
		# Create satisfaction analysis by agent type
		agent_satisfaction = {}
		for conv in conversations:
			agent_types = conv.get('agent_types', [])
			is_successful = conv.get('analysis', {}).get('ux', {}).get('is_successful', None)
			sentiment = conv.get('analysis', {}).get('ux', {}).get('sentiment', 'neutral')
			
			if agent_types and is_successful is not None:
				for agent_type in agent_types:
					if agent_type not in agent_satisfaction:
						agent_satisfaction[agent_type] = {'positive': 0, 'neutral': 0, 'negative': 0, 'total': 0}
					
					agent_satisfaction[agent_type][sentiment] += 1
					agent_satisfaction[agent_type]['total'] += 1
		
		if agent_satisfaction:
			# Convert to DataFrame for plotting
			satisfaction_data = []
			for agent, data in agent_satisfaction.items():
				for sentiment, count in data.items():
					if sentiment != 'total':
						satisfaction_data.append({
							'Agent_Type': agent,
							'Sentiment': sentiment,
							'Count': count,
							'Percentage': (count / data['total']) * 100
						})
			
			satisfaction_df = pd.DataFrame(satisfaction_data)
			fig_satisfaction = px.bar(satisfaction_df, 
							 x='Agent_Type', 
							 y='Percentage', 
							 color='Sentiment',
							 title='Удовлетворенность пользователей по типам агентов (%)',
							 color_discrete_map={
								 'positive': 'green',
								 'neutral': 'yellow', 
								 'negative': 'red'
							 })
			st.plotly_chart(fig_satisfaction, use_container_width=True)
		else:
			st.info("Недостаточно данных для анализа удовлетворенности по агентским системам")
	
	with tab2:
		st.subheader("📝 Заметки")
		st.info("Здесь размещаются заметки по анализу пользовательского опыта.")