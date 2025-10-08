"""
Configuration Manager Module
============================
This module handles all configuration management for the Spanish Learning Assistant.
It manages both JSON configuration files and environment variables, with proper
separation between settings and sensitive data (API keys).

Functions:
    - load_config: Load application configuration from config.json
    - save_config: Save application configuration to config.json
    - reset_config: Reset configuration to default values
    - load_env: Load environment variables from .env.txt
    - save_env: Save environment variables to .env.txt
    - get_api_key: Retrieve Ollama API key from environment
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure module logger
logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_FILE = Path.home() / ".spanish_tutor" / "config.json"
ENV_FILE = Path.home() / ".spanish_tutor" / ".env.txt"

# Ensure directory exists
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Default configuration values
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "preferred_model": "gpt-oss",
    "use_cloud": False,
    "cloud_endpoint": "https://ollama.com",
    "speech_timeout": 10,
    "phrase_time_limit": 15,
    "ambient_noise_duration": 0.5,
    "spanish_dialect": "es-ES",
    "english_dialect": "en-US",
    "speech_speed": False,
    "max_conversation_history": 50,
    "auto_play_audio": True,
    "show_timestamps": False,
    "log_level": "INFO",
    "theme": "light"
}


def load_config() -> Dict[str, Any]:
    """
    Load application configuration from config.json file.
    
    If the configuration file doesn't exist or is invalid, returns default
    configuration. Merges loaded config with defaults to handle version updates
    where new settings are added.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
        
    Example:
        >>> config = load_config()
        >>> print(config['preferred_model'])
        'gpt-oss'
    """
    try:
        if CONFIG_FILE.exists():
            logger.info(f"Loading configuration from {CONFIG_FILE}")
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # Merge with defaults to handle new settings in updates
            config = {**DEFAULT_CONFIG, **loaded_config}
            
            logger.debug(f"Configuration loaded successfully: {len(config)} settings")
            return config
        else:
            logger.info("No config file found, using defaults")
            return DEFAULT_CONFIG.copy()
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        logger.info("Falling back to default configuration")
        return DEFAULT_CONFIG.copy()
        
    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save application configuration to config.json file.
    
    Creates the configuration directory if it doesn't exist. Writes config
    as formatted JSON with indentation for readability.
    
    Args:
        config: Dictionary containing configuration settings
        
    Returns:
        bool: True if save successful, False otherwise
        
    Example:
        >>> config = load_config()
        >>> config['preferred_model'] = 'deepseek-v3'
        >>> save_config(config)
        True
    """
    try:
        # Ensure directory exists
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving configuration to {CONFIG_FILE}")
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.debug("Configuration saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        return False


def reset_config() -> Dict[str, Any]:
    """
    Reset configuration to default values.
    
    Overwrites the existing config file with default settings.
    
    Returns:
        Dict[str, Any]: Default configuration dictionary
        
    Example:
        >>> config = reset_config()
        >>> print(config['use_cloud'])
        False
    """
    logger.info("Resetting configuration to defaults")
    
    default_config = DEFAULT_CONFIG.copy()
    save_config(default_config)
    
    logger.debug("Configuration reset complete")
    return default_config


def load_env() -> Dict[str, str]:
    """
    Load environment variables from .env.txt file.
    
    Parses KEY=VALUE format, ignoring comments (lines starting with #)
    and empty lines. Handles sensitive data like API keys.
    
    Returns:
        Dict[str, str]: Dictionary of environment variables
        
    Example:
        >>> env = load_env()
        >>> api_key = env.get('OLLAMA_API_KEY', '')
    """
    env_vars = {}
    
    try:
        if ENV_FILE.exists():
            logger.info(f"Loading environment variables from {ENV_FILE}")
            
            with open(ENV_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                    else:
                        logger.warning(f"Invalid format in .env.txt line {line_num}: {line}")
            
            logger.debug(f"Loaded {len(env_vars)} environment variables")
        else:
            logger.info("No .env.txt file found")
            
        return env_vars
        
    except Exception as e:
        logger.error(f"Error loading .env.txt: {e}", exc_info=True)
        return {}


def save_env(env_vars: Dict[str, str]) -> bool:
    """
    Save environment variables to .env.txt file.
    
    Writes in KEY=VALUE format with a warning header about sensitive data.
    Creates the directory if it doesn't exist.
    
    Args:
        env_vars: Dictionary of environment variables to save
        
    Returns:
        bool: True if save successful, False otherwise
        
    Example:
        >>> env_vars = {'OLLAMA_API_KEY': 'your-key-here'}
        >>> save_env(env_vars)
        True
    """
    try:
        # Ensure directory exists
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving environment variables to {ENV_FILE}")
        
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write("# Spanish Tutor Environment Variables\n")
            f.write("# DO NOT SHARE THIS FILE - IT CONTAINS SENSITIVE API KEYS\n")
            f.write("# Auto-generated by Spanish Learning Assistant\n\n")
            
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
        
        # Set file permissions to be more restrictive (Unix-like systems)
        try:
            ENV_FILE.chmod(0o600)  # Read/write for owner only
            logger.debug("Set restrictive permissions on .env.txt")
        except Exception:
            pass  # Windows doesn't support chmod
        
        logger.debug(f"Saved {len(env_vars)} environment variables")
        return True
        
    except Exception as e:
        logger.error(f"Error saving .env.txt: {e}", exc_info=True)
        return False


def get_api_key() -> str:
    """
    Retrieve Ollama API key from environment variables.
    
    Returns:
        str: API key if found, empty string otherwise
        
    Example:
        >>> api_key = get_api_key()
        >>> if api_key:
        ...     print("API key is configured")
    """
    env_vars = load_env()
    api_key = env_vars.get('OLLAMA_API_KEY', '')
    
    if api_key:
        logger.debug("API key found in environment")
    else:
        logger.debug("No API key found in environment")
    
    return api_key


def get_config_info() -> Dict[str, Any]:
    """
    Get information about configuration file locations and status.
    
    Returns:
        Dict[str, Any]: Dictionary containing config file info
        
    Example:
        >>> info = get_config_info()
        >>> print(info['config_exists'])
        True
    """
    return {
        'config_file': str(CONFIG_FILE),
        'config_exists': CONFIG_FILE.exists(),
        'env_file': str(ENV_FILE),
        'env_exists': ENV_FILE.exists(),
        'config_dir': str(CONFIG_FILE.parent),
        'has_api_key': bool(get_api_key())
    }