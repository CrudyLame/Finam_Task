"""
Functional analysis page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

def show_functional_analysis(conversations):
	"""Display functional analysis page with agent type distribution and success metrics"""
	st.header("🔧 Анализ функционала")
	
	# Create tabs
	tab1, tab2 = st.tabs(["📊 Анализ", "💡 Гипотезы"])
	
	with tab1:
		# Description section (empty for user to fill)
		st.subheader("📝 Описание раздела")
		st.info("Это место для описания раздела анализа функционала. Заполните по необходимости.")
		
		# Parse data for analysis
		df = pd.DataFrame(conversations)
		
		# Agent type analysis (excluding supervisor)
		st.subheader("🤖 Распределение по типам агентов")
		
		# Extract agent types from all conversations
		all_agent_types = []
		for conv in conversations:
			agent_types = conv.get('agent_types', [])
			if agent_types:
				for agent_type in agent_types:
					if agent_type != 'supervisor':  # Exclude supervisor
						all_agent_types.append(agent_type)
		
		if all_agent_types:
			agent_counter = Counter(all_agent_types)
			agent_df = pd.DataFrame(list(agent_counter.items()), columns=['Agent Type', 'Count'])
			
			# Agent distribution pie chart
			fig_agents = px.pie(agent_df, values='Count', names='Agent Type', 
							   title='Распределение по типам агентов')
			st.plotly_chart(fig_agents, use_container_width=True)
		else:
			st.warning("Данные о типах агентов не найдены в conversations_data.json")
		
		# Success/Failure analysis
		st.subheader("✅ Анализ успешности запросов")
		
		success_data = []
		for conv in conversations:
			is_successful = conv.get('analysis', {}).get('ux', {}).get('is_successful', None)
			if is_successful is not None:
				success_data.append('Успешно' if is_successful else 'Неуспешно')
		
		if success_data:
			success_counter = Counter(success_data)
			success_df = pd.DataFrame(list(success_counter.items()), columns=['Статус', 'Количество'])
			
			# Success rate chart
			fig_success = px.bar(success_df, x='Статус', y='Количество',
							   title='Успешность запросов', color='Статус',
							   color_discrete_map={'Успешно': 'green', 'Неуспешно': 'red'})
			st.plotly_chart(fig_success, use_container_width=True)
			
			# Success percentage
			total_requests = sum(success_counter.values())
			success_rate = (success_counter.get('Успешно', 0) / total_requests) * 100
			st.metric("Процент успешных запросов", f"{success_rate:.1f}%")
		else:
			st.warning("Данные об успешности запросов не найдены")
		
		# Cross-analysis: Problems by Agent Type
		st.subheader("📊 Кросс-анализ: Проблемы по типам агентов")
		
		problem_agent_data = []
		for conv in conversations:
			problems = conv.get('analysis', {}).get('problems', {}).get('problems', [])
			agent_types = conv.get('agent_types', [])
			
			if problems and agent_types:
				for problem in problems:
					for agent_type in agent_types:
						if agent_type != 'supervisor':
							problem_agent_data.append({'Problem': problem, 'Agent_Type': agent_type})
		
		if problem_agent_data:
			problem_agent_df = pd.DataFrame(problem_agent_data)
			problem_agent_crosstab = pd.crosstab(problem_agent_df['Problem'], problem_agent_df['Agent_Type'])
			
			fig_heatmap = px.imshow(problem_agent_crosstab, 
								   title='Распределение проблем по типам агентов',
								   labels=dict(x="Тип агента", y="Тип проблемы", color="Количество"))
			st.plotly_chart(fig_heatmap, use_container_width=True)
		else:
			st.info("Недостаточно данных для кросс-анализа проблем и типов агентов")
		
		# Cross-analysis: Categories by Success
		st.subheader("📈 Кросс-анализ: Категории по успешности")
		
		category_success_data = []
		for conv in conversations:
			categories = conv.get('analysis', {}).get('request', {}).get('category', [])
			is_successful = conv.get('analysis', {}).get('ux', {}).get('is_successful', None)
			
			if categories and is_successful is not None:
				success_status = 'Успешно' if is_successful else 'Неуспешно'
				for category in categories:
					category_success_data.append({'Category': category, 'Success': success_status})
		
		if category_success_data:
			category_success_df = pd.DataFrame(category_success_data)
			category_success_crosstab = pd.crosstab(category_success_df['Category'], category_success_df['Success'])
			
			fig_category_success = px.bar(category_success_crosstab, 
										 title='Успешность по категориям запросов',
										 labels={'value': 'Количество', 'index': 'Категория'})
			st.plotly_chart(fig_category_success, use_container_width=True)
		else:
			st.info("Недостаточно данных для анализа категорий по успешности")
	
	with tab2:
		st.subheader("💡 Гипотезы")
		st.info("Это место для ваших гипотез относительно функционального анализа. Заполните по необходимости.")
		
		# Placeholder for hypotheses
		st.text_area("Ваши гипотезы:", 
					placeholder="Введите здесь свои гипотезы о функциональности системы...", 
					height=200, 
					key="functional_hypotheses")