"""
Ollama Manager Module
====================
This module manages interactions with Ollama models (both local and cloud-hosted).
It handles model discovery, API calls, and error handling for LLM operations.

Functions:
    - get_local_models: Retrieve list of locally installed Ollama models
    - get_cloud_models: Get list of recommended cloud-hosted models
    - call_local_llm: Execute prompt on local Ollama model
    - call_cloud_llm: Execute prompt on cloud-hosted Ollama model
    - call_llm: Route LLM call to appropriate backend (local or cloud)
    - test_ollama_connection: Verify Ollama service is accessible
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import Ollama
try:
    import ollama
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Configure module logger
logger = logging.getLogger(__name__)

# Cloud-hosted models available on ollama.com
# NOTE: Cloud models need -cloud suffix
# Official list: https://docs.ollama.com/cloud
CLOUD_MODELS = {
    "deepseek-v3.1:671b-cloud": "671B parameters - Excellent multilingual support (RECOMMENDED)",
    "gpt-oss:120b-cloud": "120B parameters - GPT-style open source model",
    "gpt-oss:20b-cloud": "20B parameters - Smaller GPT-style model",
    "qwen3-coder:480b-cloud": "480B parameters - Specialized for coding"
}


def get_local_models() -> List[str]:
    """
    Retrieve list of locally downloaded Ollama models.
    
    Attempts to query Ollama API first, falls back to filesystem scan on Windows
    if API fails. Returns empty list if no models found.
    
    Returns:
        List[str]: List of model names available locally
        
    Example:
        >>> models = get_local_models()
        >>> print(f"Found {len(models)} local models")
    """
    if not OLLAMA_AVAILABLE:
        logger.warning("Ollama library not available")
        return []
    
    try:
        logger.info("Querying local Ollama models via API")
        
        # Try the standard API method first
        models_response = ollama.list()
        
        # Handle different response formats
        models = models_response.get('models', [])
        model_names = []
        
        for model in models:
            # Handle both dict and object formats
            if isinstance(model, dict):
                model_name = model.get('name', '')
            else:
                model_name = getattr(model, 'name', '')
            
            if model_name:
                model_names.append(model_name)
        
        unique_models = sorted(set(model_names))
        
        logger.info(f"Found {len(unique_models)} local models via API")
        logger.debug(f"Models: {unique_models}")
        
        return unique_models
        
    except Exception as e:
        logger.warning(f"API query failed: {e}")
        logger.info("Attempting filesystem scan for models")
        
        # If API fails, try reading from file system (Windows fallback)
        try:
            windows_path = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"
            
            if windows_path.exists():
                model_names = []
                for model_dir in windows_path.iterdir():
                    if model_dir.is_dir():
                        model_names.append(model_dir.name)
                
                if model_names:
                    unique_models = sorted(set(model_names))
                    logger.info(f"Found {len(unique_models)} models via filesystem")
                    logger.debug(f"Models: {unique_models}")
                    return unique_models
            
            logger.warning(f"No models found in {windows_path}")
            return []
            
        except Exception as fs_error:
            logger.error(f"Filesystem scan failed: {fs_error}", exc_info=True)
            return []


def get_cloud_models() -> List[Dict[str, str]]:
    """
    Get list of recommended cloud-hosted models from Ollama.
    
    Returns:
        List[Dict[str, str]]: List of dicts with 'name' and 'description' keys
        
    Example:
        >>> models = get_cloud_models()
        >>> for model in models:
        ...     print(f"{model['name']}: {model['description']}")
    """
    logger.debug("Returning cloud model list")
    return [{"name": name, "description": desc} for name, desc in CLOUD_MODELS.items()]


def call_local_llm(prompt: str, system_prompt: str, model: str) -> str:
    """
    Call local LLM via Ollama service.
    
    Sends chat request to locally running Ollama instance with system and user prompts.
    
    Args:
        prompt: User prompt/question
        system_prompt: System instruction for model behavior
        model: Name of the local model to use
        
    Returns:
        str: Model response or error message
        
    Example:
        >>> response = call_local_llm(
        ...     "Translate to Spanish: Hello",
        ...     "You are a Spanish tutor",
        ...     "llama2"
        ... )
    """
    if not OLLAMA_AVAILABLE:
        error_msg = "Error: Ollama not available. Please install it."
        logger.error(error_msg)
        return error_msg
    
    try:
        logger.info(f"Calling local model: {model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
        )
        
        result = response['message']['content']
        logger.info(f"Local model response received ({len(result)} chars)")
        logger.debug(f"Response preview: {result[:100]}...")
        
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "connection" in error_msg or "refused" in error_msg:
            error_response = (
                f"Error: Cannot connect to Ollama service.\n\n"
                f"Please ensure Ollama is running:\n"
                f"- Windows: Check system tray for Ollama icon\n"
                f"- If not running: Start Ollama from Start Menu\n"
                f"- Or run in terminal: ollama serve\n\n"
                f"Details: {str(e)}"
            )
            logger.error(f"Connection error: {e}")
        else:
            error_response = (
                f"Error calling local LLM: {str(e)}\n\n"
                f"Troubleshooting:\n"
                f"1. Ensure Ollama is running\n"
                f"2. Verify model exists: ollama list\n"
                f"3. Try: ollama run {model}"
            )
            logger.error(f"LLM error: {e}", exc_info=True)
        
        return error_response


def call_cloud_llm(prompt: str, system_prompt: str, model: str, 
                   endpoint: str, api_key: str) -> str:
    """
    Call cloud-hosted LLM via Ollama Cloud API.
    
    Uses Ollama Python library to communicate with cloud-hosted models.
    Requires valid API key from ollama.com.
    
    Args:
        prompt: User prompt/question
        system_prompt: System instruction for model behavior
        model: Name of the cloud model to use (must include version tag)
        endpoint: Ollama cloud endpoint URL
        api_key: Ollama API key
        
    Returns:
        str: Model response or error message
        
    Example:
        >>> response = call_cloud_llm(
        ...     "Translate to Spanish: Hello",
        ...     "You are a Spanish tutor",
        ...     "deepseek-v3:latest",
        ...     "https://ollama.com",
        ...     "your-api-key"
        ... )
    """
    try:
        if not api_key:
            error_msg = (
                "Error: No API key found.\n\n"
                "Please:\n"
                "1. Go to https://ollama.com/settings/keys\n"
                "2. Create an API key\n"
                "3. Save it in Options → API Key Configuration"
            )
            logger.error("No API key provided for cloud call")
            return error_msg
        
        if not OLLAMA_AVAILABLE:
            error_msg = "Error: Ollama library not installed.\n\nPlease install: pip install ollama"
            logger.error("Ollama library not available")
            return error_msg
        
        logger.info(f"Calling cloud model: {model} at {endpoint}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        logger.debug(f"API key present: {bool(api_key)}")
        
        # Create client with cloud endpoint and API key
        client = Client(
            host=endpoint,
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        
        # Make non-streaming request
        response = client.chat(model=model, messages=messages, stream=False)
        result = response['message']['content']
        
        logger.info(f"Cloud model response received ({len(result)} chars)")
        logger.debug(f"Response preview: {result[:100]}...")
        
        return result
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "401" in error_msg or "unauthorized" in error_msg:
            error_response = (
                f"Error: Invalid API key.\n\n"
                f"Please:\n"
                f"1. Check your API key at https://ollama.com/settings/keys\n"
                f"2. Update in Options → API Key Configuration\n\n"
                f"Details: {e}"
            )
            logger.error(f"Authentication error: {e}")
            
        elif "404" in error_msg or "not found" in error_msg:
            error_response = (
                f"Error: Model '{model}' not found on Ollama cloud.\n\n"
                f"Available cloud models:\n"
                f"- deepseek-v3.1:671b-cloud\n"
                f"- gpt-oss:120b-cloud\n"
                f"- gpt-oss:20b-cloud\n"
                f"- qwen3-coder:480b-cloud\n\n"
                f"Details: {e}"
            )
            logger.error(f"Model not found: {e}")
            
        elif "connection" in error_msg or "resolve" in error_msg:
            error_response = (
                f"Error: Cannot connect to {endpoint}\n\n"
                f"Please check:\n"
                f"1. Internet connection\n"
                f"2. Endpoint URL (should be: https://ollama.com)\n"
                f"3. Firewall settings\n\n"
                f"Details: {e}"
            )
            logger.error(f"Connection error: {e}")
            
        else:
            error_response = (
                f"Error calling Ollama cloud:\n{e}\n\n"
                f"If this persists, try:\n"
                f"1. Regenerate API key\n"
                f"2. Check https://ollama.com/status"
            )
            logger.error(f"Unexpected cloud error: {e}", exc_info=True)
        
        return error_response


def call_llm(prompt: str, system_prompt: str, config: Dict[str, Any]) -> str:
    """
    Call LLM (routes to local or cloud based on config).
    
    Main entry point for LLM calls. Routes to appropriate backend based on
    configuration settings.
    
    Args:
        prompt: User prompt/question
        system_prompt: System instruction for model behavior
        config: Configuration dictionary with model settings
        
    Returns:
        str: Model response or error message
        
    Example:
        >>> config = {'use_cloud': False, 'preferred_model': 'llama2'}
        >>> response = call_llm("Hello", "You are helpful", config)
    """
    model = config['preferred_model']
    use_cloud = config.get('use_cloud', False)
    
    logger.info(f"Routing LLM call: {'cloud' if use_cloud else 'local'} - {model}")
    
    if use_cloud:
        from config_manager import get_api_key
        api_key = get_api_key()
        return call_cloud_llm(
            prompt, 
            system_prompt, 
            model,
            config.get('cloud_endpoint', 'https://ollama.com'),
            api_key
        )
    else:
        return call_local_llm(prompt, system_prompt, model)


def test_ollama_connection() -> Dict[str, Any]:
    """
    Test connection to Ollama service and return status information.
    
    Returns:
        Dict[str, Any]: Status dictionary with connection info
        
    Example:
        >>> status = test_ollama_connection()
        >>> if status['connected']:
        ...     print("Ollama is running")
    """
    status = {
        'connected': False,
        'library_available': OLLAMA_AVAILABLE,
        'models_found': 0,
        'models': [],
        'error': None
    }
    
    if not OLLAMA_AVAILABLE:
        status['error'] = "Ollama Python library not installed"
        logger.warning("Connection test failed: library not available")
        return status
    
    try:
        logger.info("Testing Ollama connection")
        models_response = ollama.list()
        status['connected'] = True
        
        # Handle different response formats
        models = models_response.get('models', [])
        model_names = []
        
        for model in models:
            # Handle both dict and object formats
            if isinstance(model, dict):
                model_name = model.get('name', '')
            else:
                model_name = getattr(model, 'name', '')
            
            if model_name:
                model_names.append(model_name)
        
        status['models'] = model_names
        status['models_found'] = len(model_names)
        
        logger.info(f"Connection test successful: {status['models_found']} models found")
        
    except Exception as e:
        status['error'] = str(e)
        logger.error(f"Connection test failed: {e}")
    
    return status