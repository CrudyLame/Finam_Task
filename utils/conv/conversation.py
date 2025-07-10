from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import re


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
    MISSING_INFORMATION = "missing_information"
    ROUTING_ERROR = "routing_error"
    PERFORMANCE_LATENCY = "performance_latency"


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

    # Technical and process help
    TECHNICAL_HELP = "technical_help"
    PROCESS_QUESTION = "process_question"
    
    # Information requests
    GENERAL_INFO = "general_info"
    PRODUCT_INFO = "product_info"
    ORGANIZATION_INFO = "organization_info"
    SOURCE_REQUEST = "source_request"
    STATISTICS = "statistics"
    
    # Communication and collaboration
    COORDINATION = "coordination"
    FEEDBACK = "feedback"
    
    # Task and project management
    PROJECT_TASK = "project_task"
    TASK_MANAGEMENT = "task_management"
    
    # HR requests
    HR_REQUEST = "hr_request"
    
    # Meeting management
    MEETING_MANAGEMENT = "meeting_management"
    
    # FAQ and help
    FAQ_USAGE = "faq_usage"
    
    # Design and creative requests
    DESIGN_REQUEST = "design_request"


class BlockType(str, Enum):
    """Types of conversation blocks"""
    
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"


class AgentType(str, Enum):
    """Agent types for conversation blocks"""
    
    SUPERVISOR = "supervisor"
    FACTS = "facts"
    QUESTIONS = "questions"
    DEPARTMENTS = "departments"
    PRODUCTS = "products"
    TASKS = "tasks"
    MEETINGS = "meetings"
    HR = "hr"
    FAQ = "faq"
    FEEDBACK = "feedback"
    SOURCES = "sources"
    STATISTIC = "statistic"
    DESIGNER = "designer"


class ConvBlock(BaseModel):
    """Represents a single block in a conversation"""
    
    block_type: BlockType = Field(description="Type of the block (system, user, agent)")
    text: str = Field(description="Text content of the block")
    agent_type: Optional[AgentType] = Field(default=None, description="Type of agent for AGENT blocks")
    
    @classmethod
    def from_csv_block(cls, block_data: str, csv_block_type: str) -> "ConvBlock":
        """Create a ConvBlock from CSV data"""
        # Map CSV block_type to BlockType
        block_type_mapping = {
            "request": BlockType.USER,
            "response": BlockType.SYSTEM,
            "intermidiat_response": BlockType.AGENT
        }
        
        block_type = block_type_mapping.get(csv_block_type, BlockType.SYSTEM)
        
        # For USER blocks, use full text
        if block_type == BlockType.USER:
            text = block_data
        else:
            # For AGENT/SYSTEM blocks, use first 150 chars
            text = block_data[:150] if len(block_data) > 150 else block_data
        
        # Extract agent type for AGENT blocks
        agent_type = None
        if block_type == BlockType.AGENT:
            agent_type = cls._extract_agent_type(block_data)
        
        return cls(
            block_type=block_type,
            text=text,
            agent_type=agent_type
        )
    
    @staticmethod
    def _extract_agent_type(block_data: str) -> Optional[AgentType]:
        """Extract agent type from block data by searching for agent names"""
        agent_names = {
            "Supervisor": AgentType.SUPERVISOR,
            "Facts assistant": AgentType.FACTS,
            "Questions assistant": AgentType.QUESTIONS,
            "Departments assistant": AgentType.DEPARTMENTS,
            "Products assistant": AgentType.PRODUCTS,
            "Tasks assistant": AgentType.TASKS,
            "Meetings assistant": AgentType.MEETINGS,
            "HR assistant": AgentType.HR,
            "FAQ assistant": AgentType.FAQ,
            "Feedback assistant": AgentType.FEEDBACK,
            "Sources assistant": AgentType.SOURCES,
            "Statistic assistant": AgentType.STATISTIC,
            "Designer assistant": AgentType.DESIGNER
        }
        
        # Search for agent names in the block data
        for agent_name, agent_type in agent_names.items():
            if agent_name in block_data:
                return agent_type
        
        return None


class RequestCategory(BaseModel):
    """Request classification information"""
    category: List[CategoryType] = Field(
        description="Classify the conversation (information, communication, project_tasks, etc)"
    )
    intent: List[IntentType] = Field(
        description="Identify the intent (technical_help, process_question, project_task, etc)"
    )


class ProblemDetection(BaseModel):
    """Problem detection and analysis"""
    problems: List[ProblemType] = Field(
        default_factory=list,
        description="Detect problem types (technical_issues, user_confusion, system_limitations, etc)"
    )


class UX(BaseModel):
    """User experience metrics"""
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


class ConversationMap(BaseModel):
    """LLM analysis results for a conversation"""
    request: RequestCategory
    problems: ProblemDetection
    ux: UX


def get_category_for_intent(intent: IntentType) -> CategoryType:
    """Map intent to appropriate category based on business logic"""
    intent_category_mapping = {
        # INFORMATION category
        IntentType.GENERAL_INFO: CategoryType.INFORMATION,
        IntentType.PRODUCT_INFO: CategoryType.INFORMATION,
        IntentType.ORGANIZATION_INFO: CategoryType.INFORMATION,
        IntentType.SOURCE_REQUEST: CategoryType.INFORMATION,
        IntentType.STATISTICS: CategoryType.INFORMATION,
        
        # COMMUNICATION category
        IntentType.COORDINATION: CategoryType.COMMUNICATION,
        IntentType.FEEDBACK: CategoryType.COMMUNICATION,
        
        # PROJECT_TASKS category
        IntentType.PROJECT_TASK: CategoryType.PROJECT_TASKS,
        IntentType.TASK_MANAGEMENT: CategoryType.PROJECT_TASKS,
        
        # HR category
        IntentType.HR_REQUEST: CategoryType.HR,
        
        # ORGANIZATIONAL category
        IntentType.MEETING_MANAGEMENT: CategoryType.ORGANIZATIONAL,
        
        # TECH_SUPPORT category
        IntentType.TECHNICAL_HELP: CategoryType.TECH_SUPPORT,
        
        # Specific categories that map to themselves
        IntentType.FAQ_USAGE: CategoryType.FAQ,
        IntentType.DESIGN_REQUEST: CategoryType.DESIGN_REQUEST,
        
        # Process questions could be multiple categories, default to OTHER
        IntentType.PROCESS_QUESTION: CategoryType.OTHER,
    }
    
    return intent_category_mapping.get(intent, CategoryType.OTHER)


def validate_request_category(request: RequestCategory) -> RequestCategory:
    """Validate and auto-correct category based on intent"""
    if not request.intent:
        return request
    
    # Get primary intent
    primary_intent = request.intent[0]
    
    # Get expected category for this intent
    expected_category = get_category_for_intent(primary_intent)
    
    # If category is not set correctly, update it
    if expected_category not in request.category:
        request.category = [expected_category]
    
    return request


class Conversation(BaseModel):
    """Represents a conversation between user and system"""

    dialogue_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    message_count: int
    full_text: str  # Keep for backward compatibility
    blocks: List[ConvBlock] = Field(default_factory=list)
    agent_types: List[AgentType] = Field(default_factory=list)
    departments: List[float] = Field(default_factory=list)
    analysis: Optional[ConversationMap] = None
    
    def get_user_messages(self) -> str:
        """Return only USER messages as concatenated text"""
        user_blocks = [block for block in self.blocks if block.block_type == BlockType.USER]
        return "\n".join([block.text for block in user_blocks])
    
    def get_user_request_and_agents(self) -> str:
        """Return user first message and all agents messages in conversation"""
        result_parts = []
        
        # Get first user message (the request)
        user_blocks = [block for block in self.blocks if block.block_type == BlockType.USER]
        if user_blocks:
            result_parts.append(f"User Request: {user_blocks[0].text}")
        
        # Get all agent messages
        agent_blocks = [block for block in self.blocks if block.block_type == BlockType.AGENT]
        if agent_blocks:
            result_parts.append("\nAgent Responses:")
            for agent_block in agent_blocks:
                agent_name = agent_block.agent_type.value if agent_block.agent_type else "Unknown"
                result_parts.append(f"- {agent_name}: {agent_block.text}")
        
        return "\n".join(result_parts)
    
    def update_agent_types(self):
        """Update the agent_types list based on blocks"""
        agent_types = set()
        for block in self.blocks:
            if block.block_type == BlockType.AGENT and block.agent_type:
                agent_types.add(block.agent_type)
        self.agent_types = list(agent_types)


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
