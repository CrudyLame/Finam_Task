from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SentimentType(str, Enum):
    """Sentiment classifications"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ProblemType(str, Enum):
    """Types of problems detected"""

    TECHNICAL_ISSUES = "technical_issues"
    USER_CONFUSION = "user_confusion"
    SYSTEM_LIMITATIONS = "system_limitations"
    PROCESS_INEFFICIENCY = "process_inefficiency"
    COMMUNICATION_FAILURE = "communication_failure"
    OTHER = "other"


class EmotionType(str, Enum):
    """Emotion classifications"""

    FRUSTRATION = "frustration"
    SATISFACTION = "satisfaction"
    CONFUSION = "confusion"
    URGENCY = "urgency"


class CategoryType(str, Enum):
    """Request categories"""

    # --- существующие ---
    INFORMATION      = "information"       # поиск фактов, справка
    COMMUNICATION    = "communication"     # сообщения, e-mail, чат
    OTHER            = "other"             # прочее
    PROJECT_TASKS    = "project_tasks"     # запросы по задачам/проектам
    HR               = "hr"                # кадровые вопросы
    ORGANIZATIONAL   = "organizational"    # орг-структура, процессы
    TECH_SUPPORT     = "tech_support"      # техническая поддержка

    # --- новые, основанные на профилях ассистентов ---
    PRODUCTS_INFO    = "products_info"     # сведения о продуктах, тарифах, ограничениях
    DEPARTMENT_INFO  = "department_info"   # «кто в каком отделе», орг-диаграммы
    MEETINGS         = "meetings"          # календарь, планирование встреч, конфликты
    TASK_MANAGEMENT  = "task_management"   # личные to-do, напоминания, статусы
    FAQ              = "faq"               # помощь по использованию бота/сервиса
    FEEDBACK         = "feedback"          # предложения, жалобы, обратная связь
    STATISTICS       = "statistics"        # запросы метрик, usage-report’ы
    DESIGN_REQUEST   = "design_request"    # генерация презентаций, визуальных материалов
    SOURCES_REQUEST  = "sources_request"   # просьба привести или проверить источники


class IntentType(str, Enum):
    """Request intents"""

    TECHNICAL_HELP = "technical_help"
    PROCESS_QUESTION = "process_question"
    PROJECT_TASK = "project_task"
    GENERAL_INFO = "general_info"
    COORDINATION = "coordination"


class ConversationMap(BaseModel):
    """LLM analysis results for a conversation"""

    sentiment: SentimentType = Field(
        description="Determine if the conversation is positive, negative, or neutral"
    )
    sentiment_confidence: float = Field(
        ge=0.0, 
        le=1.0,
        description="Confidence score for sentiment classification"
    )
    emotions: List[EmotionType] = Field(
        default_factory=list,
        description="Identify emotions present (frustration, satisfaction, confusion, urgency)"
    )
    problems: List[ProblemType] = Field(
        default_factory=list,
        description="Detect problem types (technical_issues, user_confusion, system_limitations, etc)"
    )
    problem_severity: int = Field(
        ge=0,
        le=10,
        description="Rate from 0-10 (0 = no problems, 10 = critical issues)"
    )
    problem_extra_info: str = Field(
        default="",
        description="Additional details about identified problems"
    )
    category: List[CategoryType] = Field(
        description="Classify the conversation (information, communication, project_tasks, etc)"
    )
    intent: List[IntentType] = Field(
        description="Identify the intent (technical_help, process_question, project_task, etc)"
    )
    feedback: List[str] = Field(
        default_factory=list,
        description="Extract any user feedback about the agent system performance and behavior"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Extract any user suggestions for improving the system or conversation experience"
    )
    is_successful: bool = Field(
        default=True,
        description="Indicates if this was a successful case of system usage"
    )


class Conversation(BaseModel):
    """Represents a conversation between user and system"""

    dialogue_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    message_count: int
    full_text: str
    departments: List[float] = Field(default_factory=list)
    analysis: Optional[ConversationMap] = None


# class AnalysisResults(BaseModel):
#     """Aggregated analysis results for multiple dialogues"""
#     total_dialogues: int

#     # Sentiment distribution
#     sentiment_distribution: Dict[SentimentType, int]
#     avg_sentiment_confidence: float

#     # Problem analysis
#     problem_distribution: Dict[ProblemType, int]
#     avg_problem_severity: float
#     problematic_dialogues_count: int

#     # Category analysis
#     category_distribution: Dict[str, int]

#     # Satisfaction metrics
#     avg_satisfaction_score: float
#     avg_success_rate: float

#     # Recommendations
#     top_issues: List[str] = Field(default_factory=list)
#     recommendations: List[str] = Field(default_factory=list)


"""
Диалог:
Набор сообщений от одного пользователя

Dialogue Mapping:

category & intent:

ависимости от типов запросов, которые поступают от сотрудников (например, техническая поддержка, организационные вопросы, задачи по проектам и т.д.).

Распределение по категориям:
  информация: 1,415 (38.1%)
  коммуникация: 1,072 (28.9%)
  другое: 1,069 (28.8%)
  проекты_задачи: 96 (2.6%)
  hr_кадры: 29 (0.8%)
  организационные: 28 (0.8%)
  техподдержка: 6 (0.2%)
Определить потерянные категории (30% другое, можно точнее)


sentiment: SentimentType
sentiment_confidence: float = Field(ge=0.0, le=1.0)
emotions: List[EmotionType] = Field(default_factory=list)

# Problem detection
problems: List[ProblemType] = Field(default_factory=list)
problem_severity: int = Field(ge=0, le=10)
problem_extra_info: str = Field(default="")

# Success/failure analysis
success_indicators: List[str] = Field(default_factory=list)  # Positive outcome markers
failure_indicators: List[str] = Field(default_factory=list)  # Negative outcome markers

analysis_explanation: str (if needed)

"""
