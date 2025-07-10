# Finam Analytics Dashboard

A comprehensive Streamlit dashboard for analyzing multi-agent system interactions.

## Features

- **Overview**: General metrics and conversation timeline
- **Category Analysis**: Request categories and user intent distribution  
- **Problems Analysis**: Problem frequency and severity classification
- **UX Analysis**: Sentiment analysis and user experience metrics
- **Agent Performance**: Agent usage and success rate analysis

## Running the Dashboard

```bash
cd web_report
uv run streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

## Data Source

The dashboard reads from `../conversations_data.json` which contains analyzed conversation data with:
- Conversation metadata (duration, message count, timestamps)
- Analysis results (categories, problems, sentiment, UX metrics)
- Agent interaction data