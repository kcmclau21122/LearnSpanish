"""
Spanish Learning Assistant - Main Application
=============================================
A comprehensive Spanish learning tool with translation, correction, and conversation features.
Supports both local and cloud-hosted Ollama models with full logging and configuration management.

Main entry point for the Streamlit application.
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

# Import custom modules
from logger_config import setup_logging, get_logger, get_log_file_path, clear_old_logs
from config_manager import (
    load_config, save_config, reset_config, 
    load_env, save_env, get_api_key, get_config_info
)
from ollama_manager import (
    get_local_models, get_cloud_models, 
    test_ollama_connection, OLLAMA_AVAILABLE
)
from audio_manager import text_to_speech, speech_to_text
from spanish_tutor import SpanishTutor

# Initialize logging before any other operations
config = load_config()
setup_logging(
    log_level=config.get('log_level', 'INFO'),
    log_to_file=True,
    log_to_console=False  # Disable console in Streamlit
)

# Get module logger
logger = get_logger(__name__)
logger.info("Application starting...")


def initialize_session_state():
    """
    Initialize all session state variables for the Streamlit app.
    
    Sets up configuration, conversation history, model lists, and other
    state variables needed throughout the application.
    """
    logger.debug("Initializing session state")
    
    if 'config' not in st.session_state:
        st.session_state.config = load_config()
        logger.info("Configuration loaded into session state")
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
        logger.debug("Conversation history initialized")
    
    if 'local_models' not in st.session_state:
        st.session_state.local_models = get_local_models()
        logger.info(f"Found {len(st.session_state.local_models)} local models")
    
    if 'cloud_models' not in st.session_state:
        st.session_state.cloud_models = get_cloud_models()
        logger.debug(f"Loaded {len(st.session_state.cloud_models)} cloud models")
    
    if 'last_translation' not in st.session_state:
        st.session_state.last_translation = None
    
    if 'last_correction' not in st.session_state:
        st.session_state.last_correction = None
    
    if 'last_audio' not in st.session_state:
        st.session_state.last_audio = None
    
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    
    logger.debug("Session state initialization complete")


def render_options_page():
    """Render the options/settings page with all configuration options."""
    logger.info("Rendering options page")
    
    st.title("⚙️ Options")
    
    config = st.session_state.config
    
    # Model Settings
    st.header("🤖 Model Settings")
    
    # Local vs Cloud selection
    use_cloud = st.checkbox(
        "Use Cloud-hosted Models",
        value=config['use_cloud'],
        help="Enable this for large models like deepseek-v3 hosted on ollama.com"
    )
    
    if use_cloud != config['use_cloud']:
        logger.info(f"Cloud mode changed: {config['use_cloud']} -> {use_cloud}")
    
    config['use_cloud'] = use_cloud
    
    if use_cloud:
        render_cloud_model_settings(config)
    else:
        render_local_model_settings(config)
    
    st.divider()
    
    # Speech Settings
    render_speech_settings(config)
    
    st.divider()
    
    # UI Settings
    render_ui_settings(config)
    
    st.divider()
    
    # Logging Settings
    render_logging_settings(config)
    
    st.divider()
    
    # Diagnostics
    render_diagnostics()
    
    st.divider()
    
    # Save/Reset buttons
    render_options_buttons(config)


def render_cloud_model_settings(config: Dict[str, Any]):
    """Render cloud model configuration options."""
    logger.debug("Rendering cloud model settings")
    
    st.info("☁️ **Cloud Mode**: Using ollama.com cloud API for large models")
    
    # Cloud endpoint
    config['cloud_endpoint'] = st.text_input(
        "Cloud Endpoint URL",
        value=config['cloud_endpoint'],
        help="Ollama cloud API endpoint (default: https://ollama.com)"
    )
    
    # API Key management
    st.subheader("🔑 API Key Configuration")
    
    current_api_key = get_api_key()
    api_key_status = "✅ Set" if current_api_key else "❌ Not set"
    
    st.info(f"**API Key Status:** {api_key_status}")
    st.caption("Get your API key at: https://ollama.com/settings/keys")
    
    # Show masked key if exists
    if current_api_key:
        masked_key = current_api_key[:8] + "..." + current_api_key[-8:] if len(current_api_key) > 16 else "***"
        st.text_input(
            "Current API Key (masked)",
            value=masked_key,
            disabled=True,
            help="Your API key is stored securely"
        )
    
    # Input for new/updated API key
    new_api_key = st.text_input(
        "Enter/Update API Key",
        type="password",
        placeholder="Paste your Ollama API key here",
        help="Get your API key from https://ollama.com/settings/keys"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save API Key", disabled=not new_api_key):
            if new_api_key:
                logger.info("Saving new API key")
                env_vars = load_env()
                env_vars['OLLAMA_API_KEY'] = new_api_key
                if save_env(env_vars):
                    st.success("✅ API key saved successfully!")
                    logger.info("API key saved successfully")
                    st.rerun()
                else:
                    st.error("❌ Failed to save API key")
                    logger.error("Failed to save API key")
    
    with col2:
        if st.button("🗑️ Remove API Key", disabled=not current_api_key):
            logger.info("Removing API key")
            env_vars = load_env()
            if 'OLLAMA_API_KEY' in env_vars:
                del env_vars['OLLAMA_API_KEY']
                if save_env(env_vars):
                    st.success("✅ API key removed")
                    logger.info("API key removed successfully")
                    st.rerun()
    
    with col3:
        if st.button("👁️ Show API Key", disabled=not current_api_key):
            if current_api_key:
                st.code(current_api_key, language=None)
                st.warning("⚠️ Keep this key secret!")
    
    st.divider()
    
    # Cloud model selection
    st.subheader("Select Cloud Model")
    cloud_models = st.session_state.cloud_models
    cloud_model_names = [m['name'] for m in cloud_models]
    
    if config['preferred_model'] not in cloud_model_names:
        config['preferred_model'] = cloud_model_names[0]
    
    current_index = cloud_model_names.index(config['preferred_model'])
    
    selected_model = st.selectbox(
        "Cloud Model",
        cloud_model_names,
        index=current_index,
        format_func=lambda x: f"{x} - {next((m['description'] for m in cloud_models if m['name'] == x), '')}",
        help="Select a cloud-hosted model from ollama.com"
    )
    
    if selected_model != config['preferred_model']:
        logger.info(f"Model changed: {config['preferred_model']} -> {selected_model}")
    
    config['preferred_model'] = selected_model
    
    st.info("""
    **Recommended for Spanish Learning:**
    - **gpt-oss**: Good starting point, fast
    - **deepseek-v3**: Best for Spanish (recommended)
    - **llama3.1:70b**: High quality responses
    - **qwen2.5:72b**: Strong multilingual
    """)


def render_local_model_settings(config: Dict[str, Any]):
    """Render local model configuration options."""
    logger.debug("Rendering local model settings")
    
    st.info("💻 **Local Mode**: Using models installed on your computer")
    
    local_models = st.session_state.local_models
    
    if not local_models:
        st.error("No local Ollama models found. Please install models using 'ollama pull <model-name>'")
        st.info("Recommended local models: qwen2.5:7b, llama2, gemma3")
        
        st.markdown("---")
        st.subheader("Manual Model Entry")
        st.markdown("If you have models installed but they're not detected, enter the model name manually:")
        
        manual_model = st.text_input(
            "Model Name",
            placeholder="e.g., llama2, qwen2.5:7b",
            help="Enter the exact model name as shown in 'ollama list'"
        )
        
        if manual_model:
            config['preferred_model'] = manual_model
            st.success(f"Using manual model: {manual_model}")
            logger.info(f"Manual model set: {manual_model}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Local Models"):
                logger.info("Refreshing local models list")
                st.session_state.local_models = get_local_models()
                st.rerun()
        
        with col2:
            if st.button("🧪 Test Ollama Connection"):
                logger.info("Testing Ollama connection")
                status = test_ollama_connection()
                if status['connected']:
                    st.success(f"✅ Ollama connected! Found {status['models_found']} models")
                    logger.info(f"Connection successful: {status['models_found']} models")
                    if status['models']:
                        st.write("Models detected:")
                        for m in status['models']:
                            st.write(f"- {m}")
                else:
                    st.error(f"❌ Connection failed: {status['error']}")
                    logger.error(f"Connection failed: {status['error']}")
    else:
        if config['preferred_model'] not in local_models:
            config['preferred_model'] = local_models[0]
        
        current_index = local_models.index(config['preferred_model'])
        
        preferred_model = st.selectbox(
            "Local Model",
            local_models,
            index=current_index,
            help="Select the locally installed LLM model"
        )
        
        if preferred_model != config['preferred_model']:
            logger.info(f"Model changed: {config['preferred_model']} -> {preferred_model}")
        
        config['preferred_model'] = preferred_model
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Local Models"):
                logger.info("Refreshing local models list")
                st.session_state.local_models = get_local_models()
                st.rerun()
        
        with col2:
            if st.button("☁️ Switch to Cloud Models"):
                logger.info("Switching to cloud mode")
                config['use_cloud'] = True
                st.rerun()
    
    st.markdown(f"**Current Selection:** {config['preferred_model']} ({'Cloud' if config['use_cloud'] else 'Local'})")


def render_speech_settings(config: Dict[str, Any]):
    """Render speech recognition configuration options."""
    logger.debug("Rendering speech settings")
    
    st.header("🎤 Speech Recognition Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['speech_timeout'] = st.slider(
            "Speech Timeout (seconds)",
            min_value=5,
            max_value=30,
            value=config['speech_timeout'],
            help="Maximum time to wait for speech to start"
        )
        
        config['phrase_time_limit'] = st.slider(
            "Phrase Time Limit (seconds)",
            min_value=5,
            max_value=30,
            value=config['phrase_time_limit'],
            help="Maximum duration for a single phrase"
        )
        
        config['ambient_noise_duration'] = st.slider(
            "Ambient Noise Calibration (seconds)",
            min_value=0.2,
            max_value=2.0,
            value=config['ambient_noise_duration'],
            step=0.1,
            help="Time to calibrate for background noise"
        )
    
    with col2:
        dialect_options = {
            "Spain Spanish": "es-ES",
            "Mexican Spanish": "es-MX",
            "Argentine Spanish": "es-AR",
            "Colombian Spanish": "es-CO",
            "US English": "en-US",
            "UK English": "en-GB"
        }
        
        spanish_dialects = ["Spain Spanish", "Mexican Spanish", "Argentine Spanish", "Colombian Spanish"]
        current_spanish = [k for k, v in dialect_options.items() if v == config['spanish_dialect']][0]
        
        spanish_dialect = st.selectbox(
            "Spanish Dialect",
            options=spanish_dialects,
            index=spanish_dialects.index(current_spanish) if current_spanish in spanish_dialects else 0,
            help="Spanish dialect for speech recognition"
        )
        config['spanish_dialect'] = dialect_options[spanish_dialect]
        
        current_english = [k for k, v in dialect_options.items() if v == config['english_dialect']][0]
        english_dialect = st.selectbox(
            "English Dialect",
            options=["US English", "UK English"],
            index=0 if current_english == "US English" else 1,
            help="English dialect for speech recognition"
        )
        config['english_dialect'] = dialect_options[english_dialect]
        
        config['speech_speed'] = st.checkbox(
            "Slow Speech Output",
            value=config['speech_speed'],
            help="Generate slower audio for pronunciation practice"
        )


def render_ui_settings(config: Dict[str, Any]):
    """Render user interface configuration options."""
    logger.debug("Rendering UI settings")
    
    st.header("🎨 Interface Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config['max_conversation_history'] = st.number_input(
            "Max Conversation History",
            min_value=10,
            max_value=200,
            value=config['max_conversation_history'],
            step=10,
            help="Maximum number of conversation messages to keep"
        )
        
        config['auto_play_audio'] = st.checkbox(
            "Auto-play Audio",
            value=config['auto_play_audio'],
            help="Automatically play audio responses"
        )
    
    with col2:
        config['show_timestamps'] = st.checkbox(
            "Show Timestamps",
            value=config['show_timestamps'],
            help="Display timestamps in conversation history"
        )


def render_logging_settings(config: Dict[str, Any]):
    """Render logging configuration options."""
    logger.debug("Rendering logging settings")
    
    st.header("📋 Logging Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_level = config.get('log_level', 'INFO')
        
        new_log_level = st.selectbox(
            "Log Level",
            options=log_levels,
            index=log_levels.index(current_level) if current_level in log_levels else 1,
            help="Verbosity of logging output"
        )
        
        if new_log_level != config.get('log_level'):
            config['log_level'] = new_log_level
            logger.info(f"Log level will be changed to: {new_log_level} (requires restart)")
        
        st.info(f"**Current Log File:** `{get_log_file_path()}`")
    
    with col2:
        if st.button("📂 Show Log Location"):
            st.code(get_log_file_path())
        
        if st.button("🗑️ Clear Old Logs (30+ days)"):
            logger.info("Clearing old log files")
            deleted = clear_old_logs(days=30)
            st.success(f"Removed {deleted} old log files")
            logger.info(f"Removed {deleted} old log files")


def render_diagnostics():
    """Render diagnostics and troubleshooting information."""
    logger.debug("Rendering diagnostics")
    
    with st.expander("🔧 Diagnostics & Troubleshooting"):
        st.markdown("### System Information")
        
        col1, col2 = st.columns(2)
        
        config_info = get_config_info()
        
        with col1:
            st.write(f"**Ollama Python Library:** {'✅ Installed' if OLLAMA_AVAILABLE else '❌ Not installed'}")
            st.write(f"**Config File:** {'✅ Exists' if config_info['config_exists'] else '❌ Not found'}")
            st.write(f"**Config Location:** `{config_info['config_file']}`")
        
        with col2:
            st.write(f"**API Key File:** {'✅ Exists' if config_info['env_exists'] else '❌ Not found'}")
            st.write(f"**API Key Loaded:** {'✅ Yes' if config_info['has_api_key'] else '❌ No'}")
            st.write(f"**Env Location:** `{config_info['env_file']}`")
        
        st.markdown("---")
        st.markdown("### Quick Tests")
        
        if st.button("🧪 Test Ollama Connection"):
            logger.info("Running Ollama connection test")
            with st.spinner("Testing connection..."):
                status = test_ollama_connection()
                if status['connected']:
                    st.success(f"✅ Ollama connected! Found {status['models_found']} models")
                    if status['models']:
                        st.write("Models available:")
                        for m in status['models']:
                            st.write(f"- {m}")
                else:
                    st.error(f"❌ Connection failed: {status['error']}")


def render_options_buttons(config: Dict[str, Any]):
    """Render save/reset/back buttons for options page."""
    logger.debug("Rendering options buttons")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            logger.info("Saving configuration")
            if save_config(config):
                st.success("Settings saved successfully!")
                st.session_state.config = config
                logger.info("Configuration saved successfully")
            else:
                st.error("Failed to save settings")
                logger.error("Failed to save configuration")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            logger.info("Resetting configuration to defaults")
            st.session_state.config = reset_config()
            st.success("Settings reset to defaults!")
            logger.info("Configuration reset complete")
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to App", use_container_width=True):
            logger.info("Returning to main app")
            st.session_state.page = "main"
            st.rerun()


def render_translation_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render translation mode interface."""
    logger.debug("Rendering translation mode")
    
    st.header("📝 English to Spanish Translation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Input")
        english_text = st.text_area("Enter English text:", height=100)
        
        if st.button("Translate", type="primary"):
            if english_text:
                logger.info(f"Translation requested: '{english_text[:50]}...'")
                with st.spinner("Translating..."):
                    result = tutor.translate_to_spanish(english_text)
                    st.session_state.last_translation = result
                    
                    try:
                        spanish_part = result.split("Spanish:")[1].split("Notes:")[0].strip()
                        audio_file = text_to_speech(
                            spanish_part, 
                            lang='es', 
                            slow=config['speech_speed']
                        )
                        st.session_state.last_audio = audio_file
                        logger.debug("Audio generated for translation")
                    except Exception as e:
                        logger.warning(f"Could not generate audio: {e}")
    
    with col2:
        st.subheader("Voice Input")
        if st.button("🎤 Speak in English", type="secondary"):
            logger.info("Starting voice input for translation")
            text = speech_to_text(
                config['english_dialect'],
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            if text:
                st.success(f"You said: {text}")
                logger.info(f"Voice input captured: '{text}'")
                with st.spinner("Translating..."):
                    result = tutor.translate_to_spanish(text)
                    st.session_state.last_translation = result
                    
                    try:
                        spanish_part = result.split("Spanish:")[1].split("Notes:")[0].strip()
                        audio_file = text_to_speech(
                            spanish_part, 
                            lang='es', 
                            slow=config['speech_speed']
                        )
                        st.session_state.last_audio = audio_file
                    except Exception as e:
                        logger.warning(f"Could not generate audio: {e}")
            else:
                logger.warning("No speech detected for translation")
    
    if st.session_state.last_translation:
        st.markdown("---")
        st.markdown("### Result")
        st.markdown(st.session_state.last_translation)
        
        if st.session_state.last_audio and config['auto_play_audio']:
            st.audio(st.session_state.last_audio, format='audio/mp3')


def render_correction_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render correction mode interface."""
    logger.debug("Rendering correction mode")
    
    st.header("✏️ Spanish Correction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Input")
        spanish_text = st.text_area("Enter Spanish text:", height=100)
        
        if st.button("Check", type="primary"):
            if spanish_text:
                logger.info(f"Correction requested: '{spanish_text[:50]}...'")
                with st.spinner("Checking..."):
                    result = tutor.correct_spanish(spanish_text)
                    st.session_state.last_correction = result
    
    with col2:
        st.subheader("Voice Input")
        if st.button("🎤 Speak in Spanish", type="secondary"):
            logger.info("Starting voice input for correction")
            text = speech_to_text(
                config['spanish_dialect'],
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            if text:
                st.success(f"You said: {text}")
                logger.info(f"Voice input captured: '{text}'")
                with st.spinner("Checking..."):
                    result = tutor.correct_spanish(text)
                    st.session_state.last_correction = result
            else:
                logger.warning("No speech detected for correction")
    
    if st.session_state.last_correction:
        st.markdown("---")
        st.markdown("### Feedback")
        st.markdown(st.session_state.last_correction)


def render_conversation_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render conversation practice mode interface."""
    logger.debug("Rendering conversation mode")
    
    st.header("💬 Conversation Practice")
    
    # Trim conversation history if too long
    max_history = config['max_conversation_history']
    if len(st.session_state.conversation_history) > max_history:
        trimmed = len(st.session_state.conversation_history) - max_history
        st.session_state.conversation_history = st.session_state.conversation_history[-max_history:]
        logger.info(f"Trimmed {trimmed} old conversation messages")
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("### Conversation History")
        for entry in st.session_state.conversation_history:
            with st.chat_message(entry['role']):
                content = entry['content']
                if config['show_timestamps'] and 'timestamp' in entry:
                    content += f"\n\n*{entry['timestamp']}*"
                st.markdown(content)
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_input = st.text_input("Type your message (Spanish or English):")
        input_lang = st.radio("Language:", ["Spanish", "English"], horizontal=True)
        
        if st.button("Send", type="primary"):
            if user_input:
                logger.info(f"Conversation input: '{user_input[:50]}...' ({input_lang})")
                process_conversation_input(tutor, config, user_input, input_lang)
    
    with col2:
        if st.button("🎤 Speak", type="secondary"):
            logger.info("Starting voice input for conversation")
            lang_code = config['spanish_dialect'] if input_lang == "Spanish" else config['english_dialect']
            text = speech_to_text(
                lang_code,
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            
            if text:
                logger.info(f"Voice input captured: '{text}' ({input_lang})")
                process_conversation_input(tutor, config, text, input_lang)
            else:
                logger.warning("No speech detected for conversation")
    
    if st.session_state.last_audio and config['auto_play_audio']:
        st.audio(st.session_state.last_audio, format='audio/mp3')
    
    if st.button("🗑️ Clear Conversation"):
        logger.info("Clearing conversation history")
        st.session_state.conversation_history = []
        st.rerun()


def process_conversation_input(tutor: SpanishTutor, config: Dict[str, Any], 
                               text: str, language: str):
    """Process conversation input and generate response."""
    logger.info(f"Processing conversation: '{text[:50]}...' ({language})")
    
    is_spanish = (language == "Spanish")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': f"**You ({language}):** {text}",
        'timestamp': timestamp
    })
    
    with st.spinner("Thinking..."):
        response = tutor.conversational_response(text, is_spanish)
        
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
        logger.info("Conversation response generated")
        
        try:
            lines = response.split('\n')
            spanish_text = lines[0] if lines else response
            audio_file = text_to_speech(
                spanish_text, 
                lang='es', 
                slow=config['speech_speed']
            )
            st.session_state.last_audio = audio_file
            logger.debug("Audio generated for conversation response")
        except Exception as e:
            logger.warning(f"Could not generate audio: {e}")
    
    st.rerun()


def render_main_app():
    """Render the main application interface."""
    logger.debug("Rendering main application")
    
    st.title("🇪🇸 Spanish Learning Assistant")
    st.markdown("Practice Spanish with text and voice input!")
    
    config = st.session_state.config
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("⚙️ Options", use_container_width=True):
            logger.info("Navigating to options page")
            st.session_state.page = "options"
            st.rerun()
        
        st.divider()
        
        st.title("Learning Mode")
        mode = st.radio(
            "Choose Mode:",
            ["Translation", "Correction", "Conversation Practice"],
            label_visibility="collapsed"
        )
        
        logger.debug(f"Mode selected: {mode}")
        
        st.divider()
        
        st.markdown("### Current Settings")
        mode_icon = "☁️" if config['use_cloud'] else "💻"
        st.info(f"{mode_icon} **Model:** {config['preferred_model']}\n\n**Mode:** {'Cloud' if config['use_cloud'] else 'Local'}\n\n**Spanish:** {config['spanish_dialect']}")
        
        st.divider()
        
        st.markdown("### About")
        st.markdown("""
        **Translation**: English → Spanish
        **Correction**: Get feedback on Spanish
        **Conversation**: Practice with AI tutor
        """)
        
        if not OLLAMA_AVAILABLE and not config['use_cloud']:
            st.error("⚠️ Ollama not installed")
    
    # Initialize tutor with config
    tutor = SpanishTutor(config)
    
    # Render appropriate mode
    if mode == "Translation":
        render_translation_mode(tutor, config)
    elif mode == "Correction":
        render_correction_mode(tutor, config)
    else:
        render_conversation_mode(tutor, config)
    
    # Footer
    st.markdown("---")
    footer_text = f"*Powered by {'Cloud-hosted' if config['use_cloud'] else 'Local'} Ollama models*"
    st.markdown(footer_text)


def main():
    """Main application entry point."""
    logger.info("=" * 80)
    logger.info("SPANISH LEARNING ASSISTANT - Session Started")
    logger.info("=" * 80)
    
    st.set_page_config(
        page_title="Spanish Learning Assistant",
        page_icon="🇪🇸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    try:
        # Initialize session state
        initialize_session_state()
        
        # Route to appropriate page
        if st.session_state.page == "options":
            render_options_page()
        else:
            render_main_app()
            
    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
        st.error(f"A critical error occurred: {str(e)}")
        st.error("Please check the logs for more details.")
        st.info(f"Log file: {get_log_file_path()}")


if __name__ == "__main__":
    main()