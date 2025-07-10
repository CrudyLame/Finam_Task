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