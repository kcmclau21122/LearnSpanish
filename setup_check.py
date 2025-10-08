"""
Setup Check Script
==================
Run this script to verify your Spanish Learning Assistant installation.
It checks for required files, dependencies, and configuration.

Usage: python setup_check.py
"""

import os
import sys
from pathlib import Path

def check_files():
    """Check if all required Python files exist."""
    required_files = [
        'main.py',
        'config_manager.py',
        'logger_config.py',
        'ollama_manager.py',
        'audio_manager.py',
        'spanish_tutor.py',
        'requirements.txt'
    ]
    
    print("=" * 60)
    print("CHECKING REQUIRED FILES")
    print("=" * 60)
    
    current_dir = Path.cwd()
    print(f"\nCurrent directory: {current_dir}\n")
    
    missing_files = []
    for file in required_files:
        file_path = current_dir / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} file(s)!")
        print("\nPlease create these files in the current directory:")
        for f in missing_files:
            print(f"  - {f}")
        return False
    else:
        print("\n✅ All required files present!")
        return True


def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = {
        'streamlit': 'streamlit',
        'ollama': 'ollama',
        'speech_recognition': 'SpeechRecognition',
        'gtts': 'gTTS',
        'requests': 'requests'
    }
    
    print("\n" + "=" * 60)
    print("CHECKING PYTHON DEPENDENCIES")
    print("=" * 60)
    print()
    
    missing_packages = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NOT INSTALLED")
            missing_packages.append(package_name)
    
    # Special check for PyAudio (optional but recommended)
    try:
        import pyaudio
        print(f"✅ PyAudio (for voice input)")
    except ImportError:
        print(f"⚠️  PyAudio - NOT INSTALLED (voice input won't work)")
        print("   Install: pip install pyaudio")
        print("   Windows: pipwin install pyaudio")
    
    if missing_packages:
        print(f"\n⚠️  Missing {len(missing_packages)} package(s)!")
        print("\nTo install missing packages:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required packages installed!")
        return True


def check_ollama():
    """Check if Ollama is available."""
    print("\n" + "=" * 60)
    print("CHECKING OLLAMA")
    print("=" * 60)
    print()
    
    try:
        import ollama
        print("✅ Ollama Python library installed")
        
        try:
            models = ollama.list()
            model_count = len(models.get('models', []))
            print(f"✅ Ollama service running ({model_count} models found)")
            
            if model_count > 0:
                print("\nInstalled models:")
                for model in models['models']:
                    print(f"  - {model['name']}")
            else:
                print("\n⚠️  No models installed")
                print("   Install a model: ollama pull qwen2.5:7b")
            
            return True
            
        except Exception as e:
            print("❌ Ollama service not running")
            print(f"   Error: {e}")
            print("\n   To start Ollama:")
            print("   - Windows: Check system tray or run from Start Menu")
            print("   - Mac/Linux: Run 'ollama serve' in terminal")
            return False
            
    except ImportError:
        print("❌ Ollama Python library not installed")
        print("   Install: pip install ollama")
        return False


def check_directory_structure():
    """Check and create required directories."""
    print("\n" + "=" * 60)
    print("CHECKING DIRECTORY STRUCTURE")
    print("=" * 60)
    print()
    
    home_dir = Path.home()
    spanish_tutor_dir = home_dir / ".spanish_tutor"
    logs_dir = spanish_tutor_dir / "logs"
    
    if not spanish_tutor_dir.exists():
        print(f"📁 Creating: {spanish_tutor_dir}")
        spanish_tutor_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"✅ Config directory exists: {spanish_tutor_dir}")
    
    if not logs_dir.exists():
        print(f"📁 Creating: {logs_dir}")
        logs_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"✅ Logs directory exists: {logs_dir}")
    
    # Check for existing config files
    config_file = spanish_tutor_dir / "config.json"
    env_file = spanish_tutor_dir / ".env.txt"
    
    print()
    if config_file.exists():
        print(f"✅ Config file exists: {config_file}")
    else:
        print(f"ℹ️  Config file will be created on first run: {config_file}")
    
    if env_file.exists():
        print(f"✅ Environment file exists: {env_file}")
    else:
        print(f"ℹ️  Environment file will be created when you add API key: {env_file}")
    
    return True


def create_test_imports():
    """Test importing all custom modules."""
    print("\n" + "=" * 60)
    print("TESTING MODULE IMPORTS")
    print("=" * 60)
    print()
    
    modules = [
        'config_manager',
        'logger_config',
        'ollama_manager',
        'audio_manager',
        'spanish_tutor'
    ]
    
    all_success = True
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name}.py imports successfully")
        except Exception as e:
            print(f"❌ {module_name}.py - Import error:")
            print(f"   {str(e)}")
            all_success = False
    
    return all_success


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("SPANISH LEARNING ASSISTANT - SETUP CHECK")
    print("=" * 60)
    
    checks = []
    
    # Run checks
    checks.append(("Files", check_files()))
    checks.append(("Dependencies", check_dependencies()))
    checks.append(("Ollama", check_ollama()))
    checks.append(("Directories", check_directory_structure()))
    checks.append(("Module Imports", create_test_imports()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP CHECK SUMMARY")
    print("=" * 60)
    print()
    
    for check_name, result in checks:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name:20} {status}")
    
    all_passed = all(result for _, result in checks)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("\nYou can now run the application:")
        print("  streamlit run main.py")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nPlease resolve the issues above before running the app.")
        print("\nQuick fixes:")
        print("  1. Ensure all .py files are in the same directory")
        print("  2. Install missing packages: pip install -r requirements.txt")
        print("  3. Install Ollama from: https://ollama.com")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()