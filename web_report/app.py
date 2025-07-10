import streamlit as st
from utils import load_conversation_data
from pages.overview import show_overview
from pages.category_analysis import show_category_analysis
from pages.problems_analysis import show_problems_analysis
from pages.functional_analysis import show_functional_analysis
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
	
	# Initialize session state for page navigation
	if 'current_page' not in st.session_state:
		st.session_state.current_page = "Обзор"
	
	# Sidebar navigation
	st.sidebar.title("Навигация")
	
	# Navigation buttons
	pages = {
		"📈 Обзор": "Обзор",
		"📊 Анализ категорий": "Анализ категорий", 
		"🔍 Анализ проблем": "Анализ проблем",
		"🔧 Анализ функционала": "Анализ функционала",
		"🎨 UX анализ": "UX анализ",
		"⚡ Производительность агентов": "Производительность агентов"
	}
	
	for display_name, page_key in pages.items():
		if st.sidebar.button(display_name, key=f"nav_{page_key}", use_container_width=True):
			st.session_state.current_page = page_key
	
	# Also keep selectbox for compatibility 
	selected_page = st.sidebar.selectbox(
		"Или выберите из списка:",
		list(pages.values()),
		index=list(pages.values()).index(st.session_state.current_page)
	)
	
	# Update current page if selectbox changed
	if selected_page != st.session_state.current_page:
		st.session_state.current_page = selected_page
	
	page = st.session_state.current_page
	
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
	elif page == "Анализ функционала":
		show_functional_analysis(conversations)
	elif page == "UX анализ":
		show_ux_analysis(conversations)
	elif page == "Производительность агентов":
		show_agent_performance(conversations)

if __name__ == "__main__":
	main()