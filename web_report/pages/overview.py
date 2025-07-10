"""
Overview page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_basic_metrics, get_ux_stats, get_timeline_data


def show_overview(conversations, metadata):
	"""Display overview page with key metrics and timeline"""
	st.header("📈 Обзор")
	
	col1, col2, col3, col4 = st.columns(4)
	
	# Basic metrics
	metrics = get_basic_metrics(conversations)
	ux_stats = get_ux_stats(conversations)
	
	with col1:
		st.metric("Средняя продолжительность (мин)", f"{metrics['avg_duration']:.2f}")
	with col2:
		st.metric("Среднее кол-во сообщений", f"{metrics['avg_messages']:.1f}")
	with col3:
		st.metric("Уникальных пользователей", metrics['unique_users'])
	with col4:
		st.metric("Показатель успеха", f"{ux_stats['success_rate']:.1%}")
	
	# Timeline analysis
	st.subheader("📅 Хронология диалогов")
	
	# Extract dates and create timeline
	date_counts = get_timeline_data(conversations)
	
	timeline_df = pd.DataFrame(list(date_counts.items()), columns=['Date', 'Count'])
	timeline_df = timeline_df.sort_values('Date')
	
	fig = px.line(timeline_df, x='Date', y='Count', title="Ежедневный объем диалогов")
	st.plotly_chart(fig, use_container_width=True)