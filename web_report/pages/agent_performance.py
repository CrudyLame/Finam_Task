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
	st.header("🤖 Agent Performance Analysis")
	
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
				title="Agent Usage Frequency"
			)
			st.plotly_chart(fig, use_container_width=True)
		
		with col2:
			# Agent success rates
			success_rates = agent_df.groupby('agent')['success'].mean()
			fig = px.bar(
				x=success_rates.index,
				y=success_rates.values,
				title="Agent Success Rates"
			)
			fig.update_layout(yaxis=dict(tickformat='.1%'))
			st.plotly_chart(fig, use_container_width=True)
		
		# Performance metrics table
		st.subheader("📊 Agent Performance Metrics")
		performance_metrics = agent_df.groupby('agent').agg({
			'success': ['count', 'mean'],
			'duration': 'mean',
			'messages': 'mean'
		}).round(2)
		
		performance_metrics.columns = ['Total Interactions', 'Success Rate', 'Avg Duration (min)', 'Avg Messages']
		st.dataframe(performance_metrics, use_container_width=True)
		
	else:
		st.info("No agent performance data available")
		st.write("Most conversations appear to be handled without specific agent assignments.")