"""
Audio Manager Module
===================
This module handles all audio input/output operations for the Spanish Learning Assistant.
It manages text-to-speech (TTS) conversion and speech recognition functionality.

Functions:
    - text_to_speech: Convert text to audio file
    - speech_to_text: Convert spoken audio to text
    - cleanup_temp_audio: Remove temporary audio files
"""

import logging
import tempfile
import speech_recognition as sr
from gtts import gTTS
from pathlib import Path
from typing import Optional

# Configure module logger
logger = logging.getLogger(__name__)


def text_to_speech(text: str, lang: str = 'es', slow: bool = False) -> Optional[str]:
    """
    Convert text to speech and return audio file path.
    
    Uses Google Text-to-Speech (gTTS) to generate audio. Creates temporary
    MP3 file that can be played back or saved.
    
    Args:
        text: Text to convert to speech
        lang: Language code (e.g., 'es' for Spanish, 'en' for English)
        slow: If True, generates slower speech for practice
        
    Returns:
        Optional[str]: Path to generated audio file, or None if error
        
    Example:
        >>> audio_file = text_to_speech("Hola mundo", lang='es')
        >>> if audio_file:
        ...     print(f"Audio saved to: {audio_file}")
    """
    try:
        logger.info(f"Generating TTS for text: '{text[:50]}...' (lang={lang}, slow={slow})")
        
        tts = gTTS(text=text, lang=lang, slow=slow)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)
        
        logger.debug(f"TTS audio saved to: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Error generating speech: {e}", exc_info=True)
        return None


def speech_to_text(language: str, 
                   timeout: int = 10, 
                   phrase_limit: int = 15,
                   ambient_duration: float = 0.5) -> Optional[str]:
    """
    Convert speech to text using microphone input.
    
    Uses Google Speech Recognition to transcribe audio from microphone.
    Automatically adjusts for ambient noise before recording.
    
    Args:
        language: Language code for recognition (e.g., 'es-ES', 'en-US')
        timeout: Maximum seconds to wait for speech to start
        phrase_limit: Maximum seconds to record a single phrase
        ambient_duration: Seconds to sample ambient noise for calibration
        
    Returns:
        Optional[str]: Transcribed text, or None if error/no speech detected
        
    Example:
        >>> text = speech_to_text('es-ES', timeout=10, phrase_limit=15)
        >>> if text:
        ...     print(f"You said: {text}")
    """
    recognizer = sr.Recognizer()
    
    try:
        logger.info(f"Starting speech recognition (lang={language}, timeout={timeout}s)")
        
        with sr.Microphone() as source:
            logger.debug(f"Adjusting for ambient noise ({ambient_duration}s)")
            recognizer.adjust_for_ambient_noise(source, duration=ambient_duration)
            
            logger.info("Listening for speech...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            
            logger.info("Processing audio...")
            text = recognizer.recognize_google(audio, language=language)
            
            logger.info(f"Speech recognized: '{text}'")
            return text
            
    except sr.WaitTimeoutError:
        logger.warning("No speech detected within timeout period")
        return None
        
    except sr.UnknownValueError:
        logger.warning("Speech was unintelligible")
        return None
        
    except sr.RequestError as e:
        logger.error(f"Speech recognition service error: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error in speech recognition: {e}", exc_info=True)
        return None


def cleanup_temp_audio(file_path: str) -> bool:
    """
    Remove temporary audio file.
    
    Args:
        file_path: Path to audio file to delete
        
    Returns:
        bool: True if deletion successful, False otherwise
        
    Example:
        >>> audio_file = text_to_speech("Hello")
        >>> # ... use audio file ...
        >>> cleanup_temp_audio(audio_file)
    """
    try:
        if file_path and Path(file_path).exists():
            Path(file_path).unlink()
            logger.debug(f"Removed temporary audio file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing audio file {file_path}: {e}")
        return False