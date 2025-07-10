"""
Alternative LLM mappers for lighter models that work well on Kaggle.
"""

import json
import re
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from .conv.conversation import Conversation, ConversationMap
from .conv.conversation import SentimentType, ProblemType, CategoryType, IntentType


class BaseLLMMapper(ABC):
    """Base class for LLM mappers."""
    
    @abstractmethod
    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Map a conversation using the specific LLM implementation."""
        pass


class HuggingFaceMapper(BaseLLMMapper):
    """Conversation mapper using Hugging Face transformers."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """
        Initialize with a Hugging Face model.
        
        Recommended models for Kaggle:
        - "microsoft/Phi-3-mini-4k-instruct" (3.8B params, fast)
        - "google/gemma-2b-it" (2B params, very fast)
        - "microsoft/DialoGPT-medium" (345M params, fastest)
        """
        self.model_name = model_name
        self._setup_model()
    
    def _setup_model(self):
        """Setup the Hugging Face model and tokenizer."""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            # Use text generation pipeline for easier inference
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.model_name,
                max_new_tokens=512,
                temperature=0.7,
                device_map="auto"  # Automatically use GPU if available
            )
            print(f"Successfully loaded {self.model_name}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Process a conversation with Hugging Face model."""
        try:
            prompt = self._create_analysis_prompt(conversation)
            
            # Generate response
            response = self.pipeline(
                prompt,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.pipeline.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            analysis_text = generated_text[len(prompt):].strip()
            
            # Parse the analysis
            analysis = self._parse_analysis(analysis_text)
            
            # Create conversation copy with analysis
            conversation_copy = conversation.model_copy()
            conversation_copy.analysis = analysis
            
            return conversation_copy
            
        except Exception as e:
            print(f"Error processing conversation {conversation.dialogue_id}: {e}")
            return conversation
    
    def _create_analysis_prompt(self, conversation: Conversation) -> str:
        """Create analysis prompt for the conversation."""
        return f"""Analyze this conversation and provide a structured analysis:

Conversation (Duration: {conversation.duration_minutes} minutes, Messages: {conversation.message_count}):
{conversation.full_text}

Please analyze and provide:
1. Sentiment (positive/negative/neutral)
2. Confidence (0.0-1.0)
3. Emotions (frustration, satisfaction, confusion, urgency)
4. Problems (technical_issues, user_confusion, system_limitations, process_inefficiency, communication_failure)
5. Problem severity (0-10)
6. Categories (information, communication, other, project_tasks, hr, organizational, tech_support)
7. Intent (technical_help, process_question, project_task, general_info, coordination)
8. Success (true/false)

Format your response as JSON:
{{
    "sentiment": "neutral",
    "sentiment_confidence": 0.8,
    "emotions": ["confusion"],
    "problems": ["user_confusion"],
    "problem_severity": 5,
    "categories": ["communication"],
    "intent": ["general_info"],
    "is_successful": false,
}}

Analysis:"""
    
    def _parse_analysis(self, analysis_text: str) -> ConversationMap:
        """Parse analysis text into ConversationMap object."""
        try:
            # Extract JSON from text
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
            else:
                # Fallback parsing
                parsed_data = self._fallback_parse(analysis_text)
            
            # Create ConversationMap with parsed data
            return ConversationMap(
                sentiment=self._parse_sentiment(parsed_data.get('sentiment', 'neutral')),
                sentiment_confidence=float(parsed_data.get('sentiment_confidence', 0.5)),
                emotions=parsed_data.get('emotions', []),
                problems=[ProblemType(p) for p in parsed_data.get('problems', [])],
                problem_severity=int(parsed_data.get('problem_severity', 5)),
                problem_extra_info=parsed_data.get('problem_extra_info', ''),
                success_indicators=parsed_data.get('success_indicators', []),
                failure_indicators=parsed_data.get('failure_indicators', []),
                category=[CategoryType(c) for c in parsed_data.get('categories', ['other'])],
                intent=[IntentType(i) for i in parsed_data.get('intent', ['general_info'])],
                feedback=parsed_data.get('feedback', []),
                suggestions=parsed_data.get('suggestions', []),
            )
            
        except Exception as e:
            print(f"Error parsing analysis: {e}")
            return self._default_analysis()
    
    def _parse_sentiment(self, sentiment_str: str) -> SentimentType:
        """Parse sentiment string to SentimentType."""
        sentiment_map = {
            'positive': SentimentType.POSITIVE,
            'negative': SentimentType.NEGATIVE,
            'neutral': SentimentType.NEUTRAL
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails."""
        return {
            'sentiment': 'neutral',
            'sentiment_confidence': 0.5,
            'emotions': [],
            'problems': ['user_confusion'],
            'problem_severity': 5,
            'categories': ['other'],
            'intent': ['general_info'],
            'is_successful': False,
        }
    
    def _default_analysis(self) -> ConversationMap:
        """Return default analysis when parsing fails."""
        return ConversationMap(
            sentiment=SentimentType.NEUTRAL,
            sentiment_confidence=0.5,
            emotions=[],
            problems=[ProblemType.USER_CONFUSION],
            problem_severity=5,
            problem_extra_info='',
            success_indicators=[],
            failure_indicators=[],
            category=[CategoryType.OTHER],
            intent=[IntentType.GENERAL_INFO],
            feedback=[],
            suggestions=[],
        )


class GroqMapper(BaseLLMMapper):
    """Conversation mapper using Groq API for fast inference."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama3-8b-8192"):
        """
        Initialize Groq mapper.
        
        Available models:
        - "llama3-8b-8192" (Fast, good quality)
        - "llama3-70b-8192" (Slower, better quality)
        - "mixtral-8x7b-32768" (Good balance)
        - "gemma-7b-it" (Lightweight)
        """
        self.api_key = api_key
        self.model_name = model_name
        self._setup_client()
    
    def _setup_client(self):
        """Setup Groq client."""
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            print(f"Successfully initialized Groq client with {self.model_name}")
        except Exception as e:
            print(f"Error initializing Groq client: {e}")
            raise
    
    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Process conversation with Groq API."""
        try:
            prompt = self._create_analysis_prompt(conversation)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert conversation analyst. Provide structured analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=512
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            analysis = self._parse_analysis(analysis_text)
            
            # Create conversation copy with analysis
            conversation_copy = conversation.model_copy()
            conversation_copy.analysis = analysis
            
            return conversation_copy
            
        except Exception as e:
            print(f"Error processing conversation {conversation.dialogue_id}: {e}")
            return conversation
    
    def _create_analysis_prompt(self, conversation: Conversation) -> str:
        """Create analysis prompt for Groq."""
        return f"""Analyze this conversation and provide structured analysis:

Conversation Details:
- Duration: {conversation.duration_minutes} minutes
- Messages: {conversation.message_count}
- Content: {conversation.full_text[:1000]}...

Analyze for:
1. Sentiment (positive/negative/neutral)
2. Confidence score (0.0-1.0)
3. Emotions present
4. Problems identified
5. Problem severity (0-10)
6. Categories
7. Intent
8. Success status

Respond with JSON only:
{{
    "sentiment": "neutral",
    "sentiment_confidence": 0.8,
    "emotions": [],
    "problems": ["user_confusion"],
    "problem_severity": 5,
    "categories": ["communication"],
    "intent": ["general_info"],
    "is_successful": false,
}}"""
    
    def _parse_analysis(self, analysis_text: str) -> ConversationMap:
        """Parse Groq response into ConversationMap."""
        # Use same parsing logic as HuggingFaceMapper
        try:
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
            else:
                parsed_data = self._fallback_parse(analysis_text)
            
            return ConversationMap(
                sentiment=self._parse_sentiment(parsed_data.get('sentiment', 'neutral')),
                sentiment_confidence=float(parsed_data.get('sentiment_confidence', 0.5)),
                emotions=parsed_data.get('emotions', []),
                problems=[ProblemType(p) for p in parsed_data.get('problems', [])],
                problem_severity=int(parsed_data.get('problem_severity', 5)),
                problem_extra_info=parsed_data.get('problem_extra_info', ''),
                success_indicators=parsed_data.get('success_indicators', []),
                failure_indicators=parsed_data.get('failure_indicators', []),
                category=[CategoryType(c) for c in parsed_data.get('categories', ['other'])],
                intent=[IntentType(i) for i in parsed_data.get('intent', ['general_info'])],
                feedback=parsed_data.get('feedback', []),
                suggestions=parsed_data.get('suggestions', []),
            )
        except Exception as e:
            print(f"Error parsing Groq analysis: {e}")
            return self._default_analysis()
    
    def _parse_sentiment(self, sentiment_str: str) -> SentimentType:
        """Parse sentiment string to SentimentType."""
        sentiment_map = {
            'positive': SentimentType.POSITIVE,
            'negative': SentimentType.NEGATIVE,
            'neutral': SentimentType.NEUTRAL
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails."""
        return {
            'sentiment': 'neutral',
            'sentiment_confidence': 0.5,
            'emotions': [],
            'problems': ['user_confusion'],
            'problem_severity': 5,
            'categories': ['other'],
            'intent': ['general_info'],
            'is_successful': False,
        }
    
    def _default_analysis(self) -> ConversationMap:
        """Return default analysis when parsing fails."""
        return ConversationMap(
            sentiment=SentimentType.NEUTRAL,
            sentiment_confidence=0.5,
            emotions=[],
            problems=[ProblemType.USER_CONFUSION],
            problem_severity=5,
            problem_extra_info='',
            success_indicators=[],
            failure_indicators=[],
            category=[CategoryType.OTHER],
            intent=[IntentType.GENERAL_INFO],
            feedback=[],
            suggestions=[],
            analysis_explanation='Default analysis due to error'
        )


class OllamaMapper(BaseLLMMapper):
    """Conversation mapper using Ollama for local inference."""
    
    def __init__(self, model_name: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama mapper.
        
        Popular models:
        - "llama3.1:8b" (8B parameters, good balance)
        - "phi3:mini" (3.8B parameters, fast)
        - "gemma:2b" (2B parameters, very fast)
        """
        self.model_name = model_name
        self.base_url = base_url
        self._setup_client()
    
    def _setup_client(self):
        """Setup Ollama client."""
        try:
            import ollama
            self.client = ollama.Client(host=self.base_url)
            print(f"Successfully initialized Ollama client with {self.model_name}")
        except Exception as e:
            print(f"Error initializing Ollama client: {e}")
            raise
    
    def map_conversation(self, conversation: Conversation) -> Conversation:
        """Process conversation with Ollama."""
        try:
            prompt = self._create_analysis_prompt(conversation)
            
            # Make API call
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'num_predict': 512
                }
            )
            
            # Parse response
            analysis_text = response['response']
            analysis = self._parse_analysis(analysis_text)
            
            # Create conversation copy with analysis
            conversation_copy = conversation.model_copy()
            conversation_copy.analysis = analysis
            
            return conversation_copy
            
        except Exception as e:
            print(f"Error processing conversation {conversation.dialogue_id}: {e}")
            return conversation
    
    def _create_analysis_prompt(self, conversation: Conversation) -> str:
        """Create analysis prompt for Ollama."""
        return f"""Analyze this conversation and provide structured analysis in JSON format:

Conversation:
Duration: {conversation.duration_minutes} minutes
Messages: {conversation.message_count}
Content: {conversation.full_text}

Provide analysis for:
- Sentiment (positive/negative/neutral)
- Confidence (0.0-1.0)
- Emotions
- Problems
- Problem severity (0-10)
- Categories
- Intent
- Success status

Response format (JSON only):
{{
    "sentiment": "neutral",
    "sentiment_confidence": 0.8,
    "emotions": [],
    "problems": ["user_confusion"],
    "problem_severity": 5,
    "categories": ["communication"],
    "intent": ["general_info"],
    "is_successful": false,
    "analysis_explanation": "Brief explanation"
}}"""
    
    def _parse_analysis(self, analysis_text: str) -> ConversationMap:
        """Parse Ollama response into ConversationMap."""
        # Use same parsing logic as other mappers
        try:
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
            else:
                parsed_data = self._fallback_parse(analysis_text)
            
            return ConversationMap(
                sentiment=self._parse_sentiment(parsed_data.get('sentiment', 'neutral')),
                sentiment_confidence=float(parsed_data.get('sentiment_confidence', 0.5)),
                emotions=parsed_data.get('emotions', []),
                problems=[ProblemType(p) for p in parsed_data.get('problems', [])],
                problem_severity=int(parsed_data.get('problem_severity', 5)),
                problem_extra_info=parsed_data.get('problem_extra_info', ''),
                success_indicators=parsed_data.get('success_indicators', []),
                failure_indicators=parsed_data.get('failure_indicators', []),
                category=[CategoryType(c) for c in parsed_data.get('categories', ['other'])],
                intent=[IntentType(i) for i in parsed_data.get('intent', ['general_info'])],
                feedback=parsed_data.get('feedback', []),
                suggestions=parsed_data.get('suggestions', []),
                analysis_explanation=parsed_data.get('analysis_explanation', '')
            )
        except Exception as e:
            print(f"Error parsing Ollama analysis: {e}")
            return self._default_analysis()
    
    def _parse_sentiment(self, sentiment_str: str) -> SentimentType:
        """Parse sentiment string to SentimentType."""
        sentiment_map = {
            'positive': SentimentType.POSITIVE,
            'negative': SentimentType.NEGATIVE,
            'neutral': SentimentType.NEUTRAL
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails."""
        return {
            'sentiment': 'neutral',
            'sentiment_confidence': 0.5,
            'emotions': [],
            'problems': ['user_confusion'],
            'problem_severity': 5,
            'categories': ['other'],
            'intent': ['general_info'],
            'is_successful': False,
            'analysis_explanation': 'Fallback analysis'
        }
    
    def _default_analysis(self) -> ConversationMap:
        """Return default analysis when parsing fails."""
        return ConversationMap(
            sentiment=SentimentType.NEUTRAL,
            sentiment_confidence=0.5,
            emotions=[],
            problems=[ProblemType.USER_CONFUSION],
            problem_severity=5,
            problem_extra_info='',
            success_indicators=[],
            failure_indicators=[],
            category=[CategoryType.OTHER],
            intent=[IntentType.GENERAL_INFO],
            feedback=[],
            suggestions=[],
            analysis_explanation='Default analysis due to error'
        )


def create_mapper(provider: str = "huggingface", **kwargs) -> BaseLLMMapper:
    """
    Factory function to create appropriate mapper.
    
    Args:
        provider: 'huggingface', 'groq', 'ollama', or 'openai'
        **kwargs: Provider-specific arguments
    
    Returns:
        Configured mapper instance
    """
    if provider == "huggingface":
        return HuggingFaceMapper(**kwargs)
    elif provider == "groq":
        return GroqMapper(**kwargs)
    elif provider == "ollama":
        return OllamaMapper(**kwargs)
    elif provider == "openai":
        from .llm import ConversationMapper
        return ConversationMapper(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")