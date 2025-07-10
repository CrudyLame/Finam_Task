"""
Agent performance analysis page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_agent_performance_data


def show_agent_performance(conversations):
	"""Display agent performance analysis with usage and success metrics"""
	st.header("⚡ Агентские системы")
	
	# Create tabs
	tab1, tab2 = st.tabs(["📊 Анализ", "💡 Гипотезы"])
	
	with tab1:
		# Description section (empty for user to fill)
		st.subheader("📝 Описание раздела")
		st.info("В этом разделе представлен анализ работы агентских систем на основе собранных данных о диалогах. Из логов извлечены все задействованные агенты, их частота использования и показатели эффективности.")
		
		# Comments section (hardcoded)
		st.subheader("📝 Заметки")
		st.info("❗ Проанализировать, насколько эффективно система категоризирует и направляет задачи к соответствующим агентам. Выявить случаи, когда система не смогла адекватно ответить на запрос или направила его неправильному агенту. Это еще не реализовано, но код текущего проекта предусматривает следующий пайплайн для анализа проблемы: на основе собранных диалгов, можно пропустить user request через llm c megapromptом на определение agentов которым должен быть перенаправлен запрос пользователя, затем свертить это с текущим роутингом (можно тоже llm as a judge) и выявить кейсы в которых системы делает это не правильно")
		
		# Extract agent data
		agent_data = get_agent_performance_data(conversations)
		
		if agent_data:
			agent_df = pd.DataFrame(agent_data)
			
			col1, col2 = st.columns(2)
			
			with col1:
				# Agent usage frequency
				agent_counts = agent_df['agent'].value_counts()
				fig = px.bar(
					x=agent_counts.index,
					y=agent_counts.values,
					title="Частота использования агентов"
				)
				st.plotly_chart(fig, use_container_width=True)
			
			with col2:
				# Agent success rates
				success_rates = agent_df.groupby('agent')['success'].mean()
				fig = px.bar(
					x=success_rates.index,
					y=success_rates.values,
					title="Уровень успешности агентов"
				)
				fig.update_layout(yaxis=dict(tickformat='.1%'))
				st.plotly_chart(fig, use_container_width=True)
			
			# Performance metrics table
			st.subheader("📊 Метрики производительности агентов")
			performance_metrics = agent_df.groupby('agent').agg({
				'success': ['count', 'mean'],
				'duration': 'mean',
				'messages': 'mean'
			}).round(2)
			
			performance_metrics.columns = ['Всего взаимодействий', 'Уровень успеха', 'Средняя длительность (мин)', 'Среднее кол-во сообщений']
			st.dataframe(performance_metrics, use_container_width=True)
			
		else:
			st.info("Данные о производительности агентов недоступны")
			st.write("Большинство диалогов обрабатываются без назначения конкретных агентов.")
	
	with tab2:
		st.subheader("💡 Гипотезы")
		st.info("Это место для ваших гипотез относительно агентских систем. Заполните по необходимости.")
		
		# Hardcoded hypotheses section
		st.info("Здесь размещаются гипотезы относительно агентских систем.")