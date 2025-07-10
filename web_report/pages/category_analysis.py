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