"""
Problems analysis page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_problems_stats


def show_problems_analysis(conversations):
	"""Display problems analysis page with issue detection and severity"""
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