"""
Spanish Learning Assistant - Streamlit Application
A comprehensive Spanish learning tool with translation, correction, and conversation features.
Supports both local and cloud-hosted Ollama models.
"""

import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from datetime import datetime
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

# Constants
CONFIG_FILE = Path.home() / ".spanish_tutor_config.json"
ENV_FILE = Path.home() / ".env.txt"

DEFAULT_CONFIG = {
    "preferred_model": "deepseek-v3",
    "use_cloud": False,
    "cloud_endpoint": "https://api.ollama.ai",
    "speech_timeout": 10,
    "phrase_time_limit": 15,
    "ambient_noise_duration": 0.5,
    "spanish_dialect": "es-ES",
    "english_dialect": "en-US",
    "speech_speed": False,
    "max_conversation_history": 50,
    "auto_play_audio": True,
    "show_timestamps": False
}

# Cloud-hosted models (too large to run locally)
CLOUD_MODELS = {
    "deepseek-v3": "671B parameters - Excellent multilingual support",
    "qwen2.5:72b": "72B parameters - Strong language capabilities",
    "llama3.1:70b": "70B parameters - High quality responses",
    "mixtral:8x7b": "47B parameters - Fast and capable"
}

# Try to import Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


class ConfigManager:
    """Manages application configuration and persistence."""
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to handle new settings
                    return {**DEFAULT_CONFIG, **config}
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            st.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving config: {e}")
            return False
    
    @staticmethod
    def reset_config() -> Dict[str, Any]:
        """Reset configuration to defaults."""
        ConfigManager.save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


class OllamaManager:
    """Manages Ollama model interactions (local and cloud)."""
    
    @staticmethod
    def get_local_models() -> List[str]:
        """Retrieve list of locally downloaded Ollama models."""
        if not OLLAMA_AVAILABLE:
            return []
        
        try:
            # Try the standard API method first
            models_response = ollama.list()
            model_names = [model['name'].split(':')[0] for model in models_response['models']]
            return sorted(set(model_names))
        except Exception as e:
            # If API fails, try reading from file system (Windows fallback)
            try:
                # Check Windows default location
                windows_path = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"
                
                if windows_path.exists():
                    model_names = []
                    for model_dir in windows_path.iterdir():
                        if model_dir.is_dir():
                            model_names.append(model_dir.name)
                    
                    if model_names:
                        return sorted(set(model_names))
                
                # If no models found via filesystem, return empty with helpful error
                st.warning(f"Could not detect models automatically. Error: {e}")
                st.info(f"Models location: {windows_path}")
                return []
            except Exception as fs_error:
                st.error(f"Error detecting models: {e}\nFilesystem check error: {fs_error}")
                return []
    
    @staticmethod
    def get_cloud_models() -> List[Dict[str, str]]:
        """Get list of recommended cloud models."""
        return [{"name": name, "description": desc} for name, desc in CLOUD_MODELS.items()]
    
    @staticmethod
    def call_local_llm(prompt: str, system_prompt: str, model: str) -> str:
        """Call local LLM via Ollama."""
        if not OLLAMA_AVAILABLE:
            return "Error: Ollama not available. Please install it."
        
        try:
            # Ensure Ollama service is running
            response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        except ollama.ResponseError as e:
            return f"Error: Model '{model}' not found or not loaded.\n\nPlease ensure:\n1. Ollama is running (check system tray)\n2. Model is downloaded: ollama pull {model}\n3. Try running: ollama list\n\nDetails: {str(e)}"
        except Exception as e:
            error_msg = str(e).lower()
            if "connection" in error_msg or "refused" in error_msg:
                return f"Error: Cannot connect to Ollama service.\n\nPlease ensure Ollama is running:\n- Windows: Check system tray for Ollama icon\n- If not running: Start Ollama from Start Menu\n- Or run in terminal: ollama serve\n\nDetails: {str(e)}"
            return f"Error calling local LLM: {str(e)}\n\nTroubleshooting:\n1. Ensure Ollama is running\n2. Verify model exists: ollama list\n3. Try: ollama run {model}"
    
    @staticmethod
    def call_cloud_llm(prompt: str, system_prompt: str, model: str, 
                       endpoint: str, api_key: str) -> str:
        """Call cloud-hosted LLM via Ollama API."""
        try:
            # For Ollama Cloud, we use the same API structure
            if api_key:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            else:
                headers = {"Content-Type": "application/json"}
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{endpoint}/api/chat",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()['message']['content']
            else:
                return f"Error: Cloud API returned status {response.status_code}\n{response.text}"
        
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model may be loading or the server is busy."
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to cloud endpoint. Please check your endpoint URL and internet connection."
        except Exception as e:
            return f"Error calling cloud LLM: {str(e)}"
    
    @staticmethod
    def call_llm(prompt: str, system_prompt: str, config: Dict[str, Any]) -> str:
        """Call LLM (routes to local or cloud based on config)."""
        model = config['preferred_model']
        
        if config['use_cloud']:
            return OllamaManager.call_cloud_llm(
                prompt, 
                system_prompt, 
                model,
                config['cloud_endpoint'],
                config['cloud_api_key']
            )
        else:
            return OllamaManager.call_local_llm(prompt, system_prompt, model)


class SpanishTutor:
    """Main Spanish tutoring functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def translate_to_spanish(self, text: str) -> str:
        """Translate English to Spanish."""
        system_prompt = """You are a helpful Spanish language tutor. Translate the English text to Spanish. 
        Provide natural, conversational Spanish. Format your response as:
        Spanish: [translation]
        Notes: [any relevant grammar or cultural notes]"""
        
        prompt = f"Translate to Spanish: {text}"
        return OllamaManager.call_llm(prompt, system_prompt, self.config)
    
    def correct_spanish(self, text: str) -> str:
        """Correct Spanish text and provide feedback."""
        system_prompt = """You are a helpful Spanish language tutor. Review the Spanish text provided.
        If there are errors, provide corrections. If it's correct, confirm it.
        Format your response as:
        Corrected: [corrected version or "¡Correcto!"]
        Explanation: [explain any corrections or confirm correctness]
        English: [English translation]"""
        
        prompt = f"Review this Spanish text: {text}"
        return OllamaManager.call_llm(prompt, system_prompt, self.config)
    
    def conversational_response(self, text: str, is_spanish: bool = True) -> str:
        """Generate conversational response for practice."""
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
        
        return OllamaManager.call_llm(prompt, system_prompt, self.config)


class AudioManager:
    """Manages audio input/output functionality."""
    
    @staticmethod
    def text_to_speech(text: str, lang: str = 'es', slow: bool = False) -> Optional[str]:
        """Convert text to speech and return audio file path."""
        try:
            tts = gTTS(text=text, lang=lang, slow=slow)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            return temp_file.name
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return None
    
    @staticmethod
    def speech_to_text(language: str, timeout: int, phrase_limit: int, 
                       ambient_duration: float) -> Optional[str]:
        """Convert speech to text."""
        recognizer = sr.Recognizer()
        
        try:
            with sr.Microphone() as source:
                st.info("🎤 Listening... Speak now!")
                recognizer.adjust_for_ambient_noise(source, duration=ambient_duration)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                st.info("Processing...")
                
                text = recognizer.recognize_google(audio, language=language)
                return text
        except sr.WaitTimeoutError:
            st.error("No speech detected. Please try again.")
            return None
        except sr.UnknownValueError:
            st.error("Could not understand audio. Please try again.")
            return None
        except sr.RequestError as e:
            st.error(f"Error with speech recognition service: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return None


def initialize_session_state():
    """Initialize all session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = ConfigManager.load_config()
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'local_models' not in st.session_state:
        st.session_state.local_models = OllamaManager.get_local_models()
    
    if 'cloud_models' not in st.session_state:
        st.session_state.cloud_models = OllamaManager.get_cloud_models()
    
    if 'last_translation' not in st.session_state:
        st.session_state.last_translation = None
    
    if 'last_correction' not in st.session_state:
        st.session_state.last_correction = None
    
    if 'last_audio' not in st.session_state:
        st.session_state.last_audio = None


def render_options_page():
    """Render the options/settings page."""
    st.title("⚙️ Options")
    
    config = st.session_state.config
    
    # Model Settings
    st.header("🤖 Model Settings")
    
    # Local vs Cloud selection
    use_cloud = st.checkbox(
        "Use Cloud-hosted Models",
        value=config['use_cloud'],
        help="Enable this for large models like deepseek-v3 that are too big to run locally"
    )
    config['use_cloud'] = use_cloud
    
    if use_cloud:
        st.info("☁️ **Cloud Mode**: Using remote Ollama API for large models")
        
        # Cloud endpoint
        config['cloud_endpoint'] = st.text_input(
            "Cloud Endpoint URL",
            value=config['cloud_endpoint'],
            help="Ollama cloud API endpoint (e.g., https://api.ollama.ai)"
        )
        
        # API Key (optional)
        config['cloud_api_key'] = st.text_input(
            "API Key (optional)",
            value=config['cloud_api_key'],
            type="password",
            help="Your Ollama cloud API key if required"
        )
        
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
            help="Select a cloud-hosted model"
        )
        config['preferred_model'] = selected_model
        
        st.warning("⚠️ Note: Cloud models may have usage costs. Check with your Ollama cloud provider.")
        
    else:
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
                placeholder="e.g., llama2, qwen2.5:7b, deepseek-v3",
                help="Enter the exact model name as shown in 'ollama list'"
            )
            
            if manual_model:
                config['preferred_model'] = manual_model
                st.success(f"Using manual model: {manual_model}")
                st.info("Click 'Save Settings' below to save this model")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Local Models"):
                    st.session_state.local_models = OllamaManager.get_local_models()
                    st.rerun()
            
            with col2:
                if st.button("🧪 Test Ollama Connection"):
                    try:
                        test_models = ollama.list()
                        st.success(f"✅ Ollama connected! Found {len(test_models.get('models', []))} models")
                        if test_models.get('models'):
                            st.write("Models detected:")
                            for m in test_models['models']:
                                st.write(f"- {m['name']}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")
                        st.info("Make sure Ollama is running (check system tray)")
        else:
            # Ensure preferred model is in available models
            if config['preferred_model'] not in local_models:
                config['preferred_model'] = local_models[0]
            
            current_index = local_models.index(config['preferred_model'])
            
            preferred_model = st.selectbox(
                "Local Model",
                local_models,
                index=current_index,
                help="Select the locally installed LLM model"
            )
            config['preferred_model'] = preferred_model
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Local Models"):
                    st.session_state.local_models = OllamaManager.get_local_models()
                    st.rerun()
            
            with col2:
                if st.button("☁️ Switch to Cloud Models"):
                    config['use_cloud'] = True
                    st.rerun()
    
    st.markdown(f"**Current Selection:** {config['preferred_model']} ({'Cloud' if config['use_cloud'] else 'Local'})")
    
    # Diagnostics section
    with st.expander("🔧 Diagnostics & Troubleshooting"):
        st.markdown("### System Information")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Ollama Python Library:** {'✅ Installed' if OLLAMA_AVAILABLE else '❌ Not installed'}")
            st.write(f"**OS:** {os.name}")
            st.write(f"**Home Directory:** {Path.home()}")
        
        with col2:
            models_path = Path.home() / ".ollama" / "models"
            st.write(f"**Models Path Exists:** {'✅ Yes' if models_path.exists() else '❌ No'}")
            if models_path.exists():
                st.write(f"**Models Path:** {models_path}")
        
        st.markdown("---")
        st.markdown("### Quick Tests")
        
        if st.button("🧪 Test Ollama Service"):
            with st.spinner("Testing connection..."):
                try:
                    import subprocess
                    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        st.success("✅ Ollama CLI is working!")
                        st.code(result.stdout)
                    else:
                        st.error(f"❌ Ollama CLI error: {result.stderr}")
                except FileNotFoundError:
                    st.error("❌ Ollama CLI not found in PATH")
                    st.info("Make sure Ollama is installed and added to PATH")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        if st.button("🔍 Scan Models Directory"):
            with st.spinner("Scanning..."):
                models_path = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"
                if models_path.exists():
                    found_models = [d.name for d in models_path.iterdir() if d.is_dir()]
                    if found_models:
                        st.success(f"✅ Found {len(found_models)} models in filesystem:")
                        for model in found_models:
                            st.write(f"- {model}")
                    else:
                        st.warning("⚠️ Models directory exists but no models found")
                else:
                    st.error(f"❌ Models directory not found: {models_path}")
    
    st.divider()
    
    # Speech Settings
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
    
    st.divider()
    
    # UI Settings
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
    
    st.divider()
    
    # Save/Reset buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            if ConfigManager.save_config(config):
                st.success("Settings saved successfully!")
                st.session_state.config = config
            else:
                st.error("Failed to save settings")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.session_state.config = ConfigManager.reset_config()
            st.success("Settings reset to defaults!")
            st.rerun()
    
    with col3:
        if st.button("🏠 Back to App", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()


def render_translation_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render translation mode interface."""
    st.header("📝 English to Spanish Translation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Input")
        english_text = st.text_area("Enter English text:", height=100)
        
        if st.button("Translate", type="primary"):
            if english_text:
                with st.spinner("Translating..."):
                    result = tutor.translate_to_spanish(english_text)
                    st.session_state.last_translation = result
                    
                    try:
                        spanish_part = result.split("Spanish:")[1].split("Notes:")[0].strip()
                        audio_file = AudioManager.text_to_speech(
                            spanish_part, 
                            lang='es', 
                            slow=config['speech_speed']
                        )
                        st.session_state.last_audio = audio_file
                    except:
                        pass
    
    with col2:
        st.subheader("Voice Input")
        if st.button("🎤 Speak in English", type="secondary"):
            text = AudioManager.speech_to_text(
                config['english_dialect'],
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            if text:
                st.success(f"You said: {text}")
                with st.spinner("Translating..."):
                    result = tutor.translate_to_spanish(text)
                    st.session_state.last_translation = result
                    
                    try:
                        spanish_part = result.split("Spanish:")[1].split("Notes:")[0].strip()
                        audio_file = AudioManager.text_to_speech(
                            spanish_part, 
                            lang='es', 
                            slow=config['speech_speed']
                        )
                        st.session_state.last_audio = audio_file
                    except:
                        pass
    
    if st.session_state.last_translation:
        st.markdown("---")
        st.markdown("### Result")
        st.markdown(st.session_state.last_translation)
        
        if st.session_state.last_audio and config['auto_play_audio']:
            st.audio(st.session_state.last_audio, format='audio/mp3')


def render_correction_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render correction mode interface."""
    st.header("✏️ Spanish Correction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Text Input")
        spanish_text = st.text_area("Enter Spanish text:", height=100)
        
        if st.button("Check", type="primary"):
            if spanish_text:
                with st.spinner("Checking..."):
                    result = tutor.correct_spanish(spanish_text)
                    st.session_state.last_correction = result
    
    with col2:
        st.subheader("Voice Input")
        if st.button("🎤 Speak in Spanish", type="secondary"):
            text = AudioManager.speech_to_text(
                config['spanish_dialect'],
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            if text:
                st.success(f"You said: {text}")
                with st.spinner("Checking..."):
                    result = tutor.correct_spanish(text)
                    st.session_state.last_correction = result
    
    if st.session_state.last_correction:
        st.markdown("---")
        st.markdown("### Feedback")
        st.markdown(st.session_state.last_correction)


def render_conversation_mode(tutor: SpanishTutor, config: Dict[str, Any]):
    """Render conversation practice mode interface."""
    st.header("💬 Conversation Practice")
    
    # Trim conversation history if too long
    max_history = config['max_conversation_history']
    if len(st.session_state.conversation_history) > max_history:
        st.session_state.conversation_history = st.session_state.conversation_history[-max_history:]
    
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
                process_conversation_input(tutor, config, user_input, input_lang)
    
    with col2:
        if st.button("🎤 Speak", type="secondary"):
            lang_code = config['spanish_dialect'] if input_lang == "Spanish" else config['english_dialect']
            text = AudioManager.speech_to_text(
                lang_code,
                config['speech_timeout'],
                config['phrase_time_limit'],
                config['ambient_noise_duration']
            )
            
            if text:
                process_conversation_input(tutor, config, text, input_lang)
    
    if st.session_state.last_audio and config['auto_play_audio']:
        st.audio(st.session_state.last_audio, format='audio/mp3')
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.rerun()


def process_conversation_input(tutor: SpanishTutor, config: Dict[str, Any], 
                               text: str, language: str):
    """Process conversation input and generate response."""
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
        
        try:
            lines = response.split('\n')
            spanish_text = lines[0] if lines else response
            audio_file = AudioManager.text_to_speech(
                spanish_text, 
                lang='es', 
                slow=config['speech_speed']
            )
            st.session_state.last_audio = audio_file
        except:
            pass
    
    st.rerun()


def render_main_app():
    """Render the main application interface."""
    st.title("🇪🇸 Spanish Learning Assistant")
    st.markdown("Practice Spanish with text and voice input!")
    
    config = st.session_state.config
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("⚙️ Options", use_container_width=True):
            st.session_state.page = "options"
            st.rerun()
        
        st.divider()
        
        st.title("Learning Mode")
        mode = st.radio(
            "Choose Mode:",
            ["Translation", "Correction", "Conversation Practice"],
            label_visibility="collapsed"
        )
        
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
    st.set_page_config(
        page_title="Spanish Learning Assistant",
        page_icon="🇪🇸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    
    # Route to appropriate page
    if st.session_state.page == "options":
        render_options_page()
    else:
        render_main_app()


if __name__ == "__main__":
    main()