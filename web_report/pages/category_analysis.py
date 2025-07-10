"""
Category analysis page for the Finam analytics dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_category_stats


def show_category_analysis(conversations):
	"""Display category analysis page with request categories and intents"""
	st.header("🏷️ Анализ категорий")
	
	# Description section (empty for user to fill)
	st.subheader("📝 Описание раздела")
	st.markdown("""
	Категории и намерения получены через LLM анализ диалогов с использованием prompt engineering для классификации запросов пользователей.
	
	### Категории:
	- **information** - поиск фактов, справка
	- **communication** - сообщения, e-mail, чат
	- **other** - прочее
	- **project_tasks** - запросы по задачам/проектам
	- **hr** - кадровые вопросы
	- **organizational** - орг-структура, процессы
	- **tech_support** - техническая поддержка
	- **products_info** - сведения о продуктах, тарифах, ограничениях
	- **department_info** - кто в каком отделе, орг-диаграммы
	- **meetings** - календарь, планирование встреч, конфликты
	- **task_management** - личные to-do, напоминания, статусы
	- **faq** - помощь по использованию бота/сервиса
	- **feedback** - предложения, жалобы, обратная связь
	- **statistics** - запросы метрик, usage-report'ы
	- **design_request** - генерация презентаций, визуальных материалов
	- **sources_request** - просьба привести или проверить источники
	
	### Намерения:
	- **technical_help** - техническая помощь
	- **process_question** - вопросы по процессам
	- **general_info** - общая информация
	- **product_info** - информация о продуктах
	- **organization_info** - информация об организации
	- **source_request** - запрос источников
	- **statistics** - статистика
	- **coordination** - координация
	- **feedback** - обратная связь
	- **project_task** - проектные задачи
	- **task_management** - управление задачами
	- **hr_request** - HR запросы
	- **meeting_management** - управление встречами
	- **faq_usage** - FAQ и помощь
	- **design_request** - дизайн запросы
	""")
	
	# Notes section (hardcoded)
	st.subheader("📝 Заметки")
	st.info("Здесь размещаются заметки по анализу категорий.")
	
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