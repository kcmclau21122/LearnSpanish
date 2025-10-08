"""
Spanish Tutor Core Module
=========================
This module contains the main Spanish tutoring functionality including translation,
correction, and conversational practice features.

Classes:
    - SpanishTutor: Main class for Spanish learning operations
"""

import logging
from typing import Dict, Any
from ollama_manager import call_llm

# Configure module logger
logger = logging.getLogger(__name__)


class SpanishTutor:
    """
    Main Spanish tutoring class providing translation, correction, and conversation features.
    
    Attributes:
        config: Configuration dictionary with model and speech settings
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Spanish tutor with configuration.
        
        Args:
            config: Configuration dictionary
            
        Example:
            >>> config = load_config()
            >>> tutor = SpanishTutor(config)
        """
        self.config = config
        logger.info("Spanish Tutor initialized")
        logger.debug(f"Using model: {config.get('preferred_model')} ({'cloud' if config.get('use_cloud') else 'local'})")
    
    def translate_to_spanish(self, text: str) -> str:
        """
        Translate English text to Spanish with grammar notes.
        
        Provides natural, conversational Spanish translation along with
        relevant grammar or cultural notes.
        
        Args:
            text: English text to translate
            
        Returns:
            str: Formatted translation with notes
            
        Example:
            >>> tutor = SpanishTutor(config)
            >>> result = tutor.translate_to_spanish("How are you?")
            >>> print(result)
            Spanish: ¿Cómo estás?
            Notes: Informal greeting...
        """
        logger.info(f"Translation request: '{text[:50]}...'")
        
        system_prompt = """You are a helpful Spanish language tutor. Translate the English text to Spanish. 
        Provide natural, conversational Spanish. Format your response as:
        Spanish: [translation]
        Notes: [any relevant grammar or cultural notes]"""
        
        prompt = f"Translate to Spanish: {text}"
        
        try:
            result = call_llm(prompt, system_prompt, self.config)
            logger.info("Translation completed successfully")
            logger.debug(f"Translation result length: {len(result)} chars")
            return result
        except Exception as e:
            error_msg = f"Error during translation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def correct_spanish(self, text: str) -> str:
        """
        Review Spanish text and provide corrections with explanations.
        
        Analyzes Spanish text for errors and provides corrections with
        detailed explanations and English translation.
        
        Args:
            text: Spanish text to review
            
        Returns:
            str: Formatted feedback with corrections or confirmation
            
        Example:
            >>> tutor = SpanishTutor(config)
            >>> result = tutor.correct_spanish("Yo tengo veinte años")
            >>> print(result)
            Corrected: ¡Correcto!
            Explanation: Perfect use of present tense...
        """
        logger.info(f"Correction request: '{text[:50]}...'")
        
        system_prompt = """You are a helpful Spanish language tutor. Review the Spanish text provided.
        If there are errors, provide corrections. If it's correct, confirm it.
        Format your response as:
        Corrected: [corrected version or "¡Correcto!"]
        Explanation: [explain any corrections or confirm correctness]
        English: [English translation]"""
        
        prompt = f"Review this Spanish text: {text}"
        
        try:
            result = call_llm(prompt, system_prompt, self.config)
            logger.info("Correction completed successfully")
            logger.debug(f"Correction result length: {len(result)} chars")
            return result
        except Exception as e:
            error_msg = f"Error during correction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def conversational_response(self, text: str, is_spanish: bool = True) -> str:
        """
        Generate conversational response for language practice.
        
        Provides natural conversational responses in Spanish with English
        translations, appropriate for language learning context.
        
        Args:
            text: User's message
            is_spanish: Whether user spoke in Spanish (True) or English (False)
            
        Returns:
            str: Conversational response in Spanish with translation
            
        Example:
            >>> tutor = SpanishTutor(config)
            >>> response = tutor.conversational_response("Me gusta el café", is_spanish=True)
            >>> print(response)
            ¡A mí también me gusta el café! ¿Cómo lo prefieres?
            (I like coffee too! How do you prefer it?)
        """
        logger.info(f"Conversation request: '{text[:50]}...' (Spanish input: {is_spanish})")
        
        if is_spanish:
            system_prompt = """You are a friendly Spanish conversation partner. Respond naturally in Spanish 
            to continue the conversation. Keep responses conversational and appropriate for language learning.
            After your Spanish response, provide:
            - English translation in parentheses
            - Any corrections to the user's Spanish if needed"""
            
            prompt = f"The user said in Spanish: {text}\nRespond naturally in Spanish and continue the conversation."
        else:
            system_prompt = """You are a friendly Spanish conversation partner. The user spoke in English.
            Respond in Spanish as if having a natural conversation, and provide the English translation."""
            
            prompt = f"The user said in English: {text}\nRespond in Spanish and provide English translation."
        
        try:
            result = call_llm(prompt, system_prompt, self.config)
            logger.info("Conversation response generated successfully")
            logger.debug(f"Response length: {len(result)} chars")
            return result
        except Exception as e:
            error_msg = f"Error during conversation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update tutor configuration.
        
        Args:
            config: New configuration dictionary
            
        Example:
            >>> tutor.update_config({'preferred_model': 'deepseek-v3'})
        """
        self.config = config
        logger.info("Configuration updated")
        logger.debug(f"New model: {config.get('preferred_model')}")