"""
Problem detection and analysis for conversations.
Analyzes conversation blocks to detect various types of problems.
"""

from typing import Dict, List, Set, Tuple
from datetime import timedelta
import re
from collections import defaultdict

from .conv.conversation import Conversation, ProblemType, BlockType


class ProblemDetector:
    """Detects problems in conversations using keyword analysis and timing."""
    
    def __init__(self, latency_threshold_seconds: int = 10):
        """
        Initialize problem detector.
        
        Args:
            latency_threshold_seconds: Threshold for performance latency detection
        """
        self.latency_threshold = timedelta(seconds=latency_threshold_seconds)
        self.keywords = self._init_keywords()
    
    def _init_keywords(self) -> Dict[ProblemType, List[str]]:
        """Initialize keyword mappings for problem detection."""
        return {
            ProblemType.TECHNICAL_ISSUES: [
                # Russian technical terms
                'ошибка', 'сбой', 'упал', 'не работает', 'неисправность', 'баг',
                'глюк', 'поломка', 'отказ', 'нарушение', 'проблема с системой',
                'технические неполадки', 'системная ошибка', 'сервер недоступен',
                'соединение потеряно', 'timeout', 'connection lost',
                # English technical terms
                'error', 'exception', 'failed', 'failure', 'crash', 'bug',
                'traceback', 'stack trace', 'server error', '500', '503', '502',
                'database error', 'connection error', 'network error',
                'internal error', 'system failure', 'malfunction'
            ],
            
            ProblemType.USER_CONFUSION: [
                # Russian confusion indicators
                'не понимаю', 'не понял', 'не поняла', 'что именно', 'как именно',
                'поясните', 'объясните', 'уточните', 'что вы имеете в виду',
                'не ясно', 'непонятно', 'можете объяснить', 'что это значит',
                'как это работает', 'не разобрался', 'запутался', 'сложно понять',
                'QA уточняет', 'нужны уточнения', 'требуется пояснение',
                # English confusion indicators
                'please clarify', 'not clear', 'confused', 'do not understand',
                'what do you mean', 'can you explain', 'please explain',
                'i don\'t get it', 'unclear', 'ambiguous', 'vague'
            ],
            
            ProblemType.SYSTEM_LIMITATIONS: [
                # Russian limitation indicators
                'не могу', 'не умею', 'не поддерживается', 'недоступно',
                'функция отсутствует', 'пока не реализовано', 'в разработке',
                'не предусмотрено', 'ограничение системы', 'нет такой возможности',
                'данная функция недоступна', 'не может быть выполнено',
                'превышен лимит', 'нет прав доступа', 'функция заблокирована',
                # English limitation indicators
                'not supported', 'feature not available', 'cannot perform',
                'limitation', 'restricted', 'access denied', 'permission denied',
                'feature disabled', 'not implemented', 'under development',
                'out of scope', 'beyond capabilities'
            ],
            
            ProblemType.MISSING_INFORMATION: [
                # Russian missing info indicators
                'не найдено', 'ничего не найдено', 'нет данных', 'отсутствует',
                'информация недоступна', 'данные отсутствуют', 'пустой результат',
                'нет результатов', 'база данных пуста', 'записи не найдены',
                'файл не найден', 'документ отсутствует', 'нет такого пользователя',
                'не существует', 'информация устарела', 'данные не обновлены',
                # English missing info indicators
                'not found', 'no data', 'no results', 'empty result',
                'no information', 'data not available', 'missing data',
                'no records', 'database empty', 'file not found',
                'document missing', 'user not found', 'does not exist',
                'no match', 'zero results', 'no entries'
            ],
            
            ProblemType.ROUTING_ERROR: [
                # Russian routing error indicators
                'не по адресу', 'неправильный ассистент', 'не мой профиль',
                'не моя специализация', 'обратитесь к другому', 'не компетентен',
                'это не ко мне', 'передаю другому специалисту', 'неправильный отдел',
                'не в моей компетенции', 'обратитесь в другой отдел',
                'я не занимаюсь этим', 'не моя задача', 'переадресую',
                # English routing error indicators
                'wrong assistant', 'not my area', 'wrong department',
                'transfer to', 'redirect to', 'not my expertise',
                'out of my scope', 'contact another', 'wrong person',
                'incorrect routing', 'misrouted', 'wrong channel'
            ],
        }
    
    def detect_problems(self, conversation: Conversation) -> List[ProblemType]:
        """
        Detect problems in a conversation.
        
        Args:
            conversation: Conversation object to analyze
            
        Returns:
            List of detected problem types
        """
        problems = set()
        
        # Get all text from conversation blocks
        all_text = self._get_conversation_text(conversation)
        
        # Check keyword-based problems
        for problem_type, keywords in self.keywords.items():
            if self._has_keywords(all_text, keywords):
                problems.add(problem_type)
        
        # Check performance latency
        if self._has_performance_latency(conversation):
            problems.add(ProblemType.PERFORMANCE_LATENCY)
        
        return list(problems)
    
    def _get_conversation_text(self, conversation: Conversation) -> str:
        """Extract all text from conversation blocks."""
        texts = []
        
        # Use blocks if available, otherwise fall back to full_text
        if conversation.blocks:
            for block in conversation.blocks:
                texts.append(block.text.lower())
        else:
            texts.append(conversation.full_text.lower())
        
        return ' '.join(texts)
    
    def _has_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if any keywords are present in text."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _has_performance_latency(self, conversation: Conversation) -> bool:
        """Check if conversation has performance latency issues."""
        if not conversation.blocks:
            # If no blocks, check overall duration
            return conversation.duration_minutes * 60 > self.latency_threshold.total_seconds()
        
        # Find first user request and last system response
        user_blocks = [b for b in conversation.blocks if b.block_type == BlockType.USER]
        system_blocks = [b for b in conversation.blocks if b.block_type == BlockType.SYSTEM]
        
        if not user_blocks or not system_blocks:
            return False
        
        # Check if conversation duration exceeds threshold
        return conversation.duration_minutes * 60 > self.latency_threshold.total_seconds()


class ProblemAnalyzer:
    """Analyzes problems across multiple conversations."""
    
    def __init__(self, detector: ProblemDetector = None):
        """Initialize analyzer with optional custom detector."""
        self.detector = detector or ProblemDetector()
        self.reset_stats()
    
    def reset_stats(self):
        """Reset analysis statistics."""
        self.problem_counts = {problem_type: 0 for problem_type in ProblemType}
        self.dialog_problems = {}
        self.total_conversations = 0
    
    def analyze_conversations(self, conversations: List[Conversation]) -> Dict:
        """
        Analyze problems across all conversations.
        
        Args:
            conversations: List of conversations to analyze
            
        Returns:
            Dictionary with analysis results
        """
        self.reset_stats()
        self.total_conversations = len(conversations)
        
        for conversation in conversations:
            problems = self.detector.detect_problems(conversation)
            
            if problems:
                self.dialog_problems[conversation.dialogue_id] = problems
                for problem in problems:
                    self.problem_counts[problem] += 1
        
        return self.get_analysis_summary()
    
    def get_analysis_summary(self) -> Dict:
        """Get summary of problem analysis."""
        total_problematic = len(self.dialog_problems)
        
        return {
            'total_conversations': self.total_conversations,
            'problematic_conversations': total_problematic,
            'problem_rate': total_problematic / self.total_conversations if self.total_conversations > 0 else 0,
            'problem_counts': dict(self.problem_counts),
            'problem_percentages': {
                problem: (count / self.total_conversations * 100) if self.total_conversations > 0 else 0
                for problem, count in self.problem_counts.items()
            },
            'dialog_problems': self.dialog_problems,
            'top_problems': self._get_top_problems()
        }
    
    def _get_top_problems(self, top_n: int = 3) -> List[Tuple[ProblemType, int]]:
        """Get top N most frequent problems."""
        sorted_problems = sorted(
            self.problem_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_problems[:top_n]
    
    def get_conversations_with_problem(self, problem_type: ProblemType) -> List[int]:
        """Get list of conversation IDs that have a specific problem."""
        return [
            dialog_id for dialog_id, problems in self.dialog_problems.items()
            if problem_type in problems
        ]
    
    def get_problem_distribution(self) -> Dict[str, float]:
        """Get normalized problem distribution."""
        total_problems = sum(self.problem_counts.values())
        if total_problems == 0:
            return {problem.value: 0.0 for problem in ProblemType}
        
        return {
            problem.value: count / total_problems * 100
            for problem, count in self.problem_counts.items()
        }


def analyze_conversation_problems(conversations: List[Conversation], 
                                latency_threshold: int = 10) -> Dict:
    """
    Convenience function to analyze problems in conversations.
    
    Args:
        conversations: List of conversations to analyze
        latency_threshold: Threshold in seconds for latency detection
        
    Returns:
        Analysis results dictionary
    """
    detector = ProblemDetector(latency_threshold_seconds=latency_threshold)
    analyzer = ProblemAnalyzer(detector)
    return analyzer.analyze_conversations(conversations)


def create_problem_detection_for_conversation(conversation: Conversation) -> 'ProblemDetection':
    """
    Create ProblemDetection object for a single conversation.
    
    Args:
        conversation: Conversation to analyze
        
    Returns:
        ProblemDetection object with detected problems
    """
    from .conv.conversation import ProblemDetection
    
    detector = ProblemDetector()
    problems = detector.detect_problems(conversation)
    
    return ProblemDetection(problems=problems)