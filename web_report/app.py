import streamlit as st
from utils import load_conversation_data
from pages.overview import show_overview
from pages.category_analysis import show_category_analysis
from pages.problems_analysis import show_problems_analysis
from pages.ux_analysis import show_ux_analysis
from pages.agent_performance import show_agent_performance

# Page config
st.set_page_config(
	page_title="Панель Аналитики Finam",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded"
)


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

if __name__ == "__main__":
	main()