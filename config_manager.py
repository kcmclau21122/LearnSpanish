"""
Configuration Manager Module
============================
This module handles all configuration management for the Spanish Learning Assistant.
It manages both JSON configuration files and environment variables, with proper
separation between settings and sensitive data (API keys).

Classes:
    ConfigManager: Singleton class for managing configuration

Functions:
    - load_config: Load application configuration from config.json
    - save_config: Save application configuration to config.json
    - reset_config: Reset configuration to default values
    - load_env: Load environment variables from .env.txt
    - save_env: Save environment variables to .env.txt
    - get_api_key: Retrieve Ollama API key from environment
    - get_config_info: Get configuration file status information
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

# Configure module logger
logger = logging.getLogger(__name__)

# Configuration file paths - use home directory
CONFIG_DIR = Path.home() / ".spanish_tutor"
CONFIG_FILE = CONFIG_DIR / "config.json"
ENV_FILE = CONFIG_DIR / ".env.txt"

# Also check for .env.txt in current directory (project folder)
PROJECT_ENV_FILE = Path.cwd() / ".env.txt"

# Default configuration values
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "preferred_model": "deepseek-v3.1:671b-cloud",
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


class ConfigManager:
    """
    Singleton configuration manager for application settings.
    
    Provides centralized access to configuration and environment variables
    with automatic file creation and validation.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config = None
        self._env = None
        self._initialized = True
        self.ensure_directories()
    
    def ensure_directories(self) -> bool:
        """
        Ensure all required directories exist.
        Creates config directory and logs directory if they don't exist.
        
        Returns:
            bool: True if successful, False if error
        """
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Config directory ready: {CONFIG_DIR}")
            
            logs_dir = CONFIG_DIR / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Logs directory ready: {logs_dir}")
            
            return True
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            return False
    
    @contextmanager
    def _atomic_write(self, file_path: Path):
        """
        Context manager for atomic file writes.
        
        Writes to temporary file first, then renames to avoid corruption.
        
        Args:
            file_path: Target file path
            
        Yields:
            file object for writing
        """
        temp_file = file_path.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                yield f
            temp_file.replace(file_path)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load application configuration from config.json file.
        
        Caches configuration after first load. Use reload_config() to force refresh.
        
        Returns:
            Dict[str, Any]: Configuration dictionary with all settings
        """
        if self._config is not None:
            return self._config
        
        try:
            if CONFIG_FILE.exists():
                logger.info(f"Loading config from: {CONFIG_FILE}")
                
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to handle new settings in updates
                self._config = {**DEFAULT_CONFIG, **loaded_config}
                logger.debug(f"Configuration loaded: {len(self._config)} settings")
                return self._config
            else:
                logger.info("No config file found, creating defaults")
                self._config = DEFAULT_CONFIG.copy()
                self.save_config(self._config)
                return self._config
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self._config = DEFAULT_CONFIG.copy()
            return self._config
        
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            self._config = DEFAULT_CONFIG.copy()
            return self._config
    
    def reload_config(self) -> Dict[str, Any]:
        """
        Force reload configuration from disk.
        
        Returns:
            Dict[str, Any]: Reloaded configuration
        """
        self._config = None
        return self.load_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save application configuration to config.json file.
        
        Uses atomic write to prevent corruption.
        
        Args:
            config: Dictionary containing configuration settings
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            self.ensure_directories()
            logger.info(f"Saving configuration to {CONFIG_FILE}")
            
            with self._atomic_write(CONFIG_FILE) as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._config = config
            logger.debug("Configuration saved successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = self.load_config()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value and save.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            bool: True if successful
        """
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
    
    def load_env(self) -> Dict[str, str]:
        """
        Load environment variables from .env.txt file.
        
        Checks both project directory and home directory for .env.txt.
        Project directory takes precedence. Caches after first load.
        
        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        if self._env is not None:
            return self._env
        
        env_file_to_use = None
        if PROJECT_ENV_FILE.exists():
            env_file_to_use = PROJECT_ENV_FILE
            logger.info(f"Loading environment from project: {PROJECT_ENV_FILE}")
        elif ENV_FILE.exists():
            env_file_to_use = ENV_FILE
            logger.info(f"Loading environment from home: {ENV_FILE}")
        else:
            logger.info("No .env.txt file found")
            self._env = {}
            return self._env
        
        try:
            env_vars = {}
            with open(env_file_to_use, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
                    else:
                        logger.warning(f"Invalid format in .env.txt line {line_num}")
            
            self._env = env_vars
            logger.debug(f"Loaded {len(env_vars)} environment variables")
            return env_vars
        
        except Exception as e:
            logger.error(f"Error loading .env.txt: {e}", exc_info=True)
            self._env = {}
            return {}
    
    def reload_env(self) -> Dict[str, str]:
        """
        Force reload environment variables from disk.
        
        Returns:
            Dict[str, str]: Reloaded environment variables
        """
        self._env = None
        return self.load_env()


# Module-level convenience functions
_config_manager = ConfigManager()

def ensure_directories() -> bool:
    """Ensure all required directories exist."""
    return _config_manager.ensure_directories()

def load_config() -> Dict[str, Any]:
    """Load application configuration."""
    return _config_manager.load_config()

def save_config(config: Dict[str, Any]) -> bool:
    """Save application configuration."""
    return _config_manager.save_config(config)

def reset_config() -> Dict[str, Any]:
    """Reset configuration to defaults."""
    logger.info("Resetting configuration to defaults")
    default_config = DEFAULT_CONFIG.copy()
    _config_manager.save_config(default_config)
    return default_config

def load_env() -> Dict[str, str]:
    """Load environment variables."""
    return _config_manager.load_env()

def save_env(env_vars: Dict[str, str]) -> bool:
    """Save environment variables to .env.txt file."""
    try:
        _config_manager.ensure_directories()
        logger.info(f"Saving environment to: {ENV_FILE}")
        
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write("# Spanish Tutor Environment Variables\n")
            f.write("# DO NOT SHARE THIS FILE - IT CONTAINS SENSITIVE API KEYS\n")
            f.write("# Auto-generated by Spanish Learning Assistant\n\n")
            
            for key, value in sorted(env_vars.items()):
                f.write(f"{key}={value}\n")
        
        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(ENV_FILE, 0o600)
        except Exception:
            pass
        
        logger.debug(f"Saved {len(env_vars)} environment variables")
        return True
    
    except Exception as e:
        logger.error(f"Error saving .env.txt: {e}", exc_info=True)
        return False

def get_api_key() -> str:
    """Get Ollama API key from environment."""
    env_vars = load_env()
    api_key = env_vars.get('OLLAMA_API_KEY', '')
    
    if api_key:
        logger.debug("API key found")
    else:
        logger.warning("No API key found")
    
    return api_key

def get_config_info() -> Dict[str, Any]:
    """Get configuration file status information."""
    return {
        'config_file': str(CONFIG_FILE),
        'config_exists': CONFIG_FILE.exists(),
        'env_file': str(ENV_FILE),
        'env_exists': ENV_FILE.exists(),
        'project_env_file': str(PROJECT_ENV_FILE),
        'project_env_exists': PROJECT_ENV_FILE.exists(),
        'config_dir': str(CONFIG_DIR),
        'has_api_key': bool(get_api_key())
    }