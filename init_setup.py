"""
Initial Setup Script
===================
This script forcefully creates all necessary directories and files
for the Spanish Learning Assistant.

Run this FIRST before running the main application.

Usage: python init_setup.py
"""

import json
from pathlib import Path
from datetime import datetime


def create_directory_structure():
    """Create all necessary directories."""
    print("\n" + "="*60)
    print("CREATING DIRECTORY STRUCTURE")
    print("="*60)
    
    home = Path.home()
    spanish_dir = home / ".spanish_tutor"
    logs_dir = spanish_dir / "logs"
    
    directories = [
        spanish_dir,
        logs_dir
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            if directory.exists():
                print(f"✅ Created: {directory}")
            else:
                print(f"❌ Failed to create: {directory}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating {directory}: {e}")
            return False
    
    return True


def create_config_file():
    """Create default config.json file."""
    print("\n" + "="*60)
    print("CREATING config.json")
    print("="*60)
    
    config_file = Path.home() / ".spanish_tutor" / "config.json"
    
    default_config = {
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
    
    try:
        print(f"📄 Writing to: {config_file}")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        if config_file.exists():
            size = config_file.stat().st_size
            print(f"✅ Config file created ({size} bytes)")
            
            # Verify it's readable
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            print(f"✅ Config file is valid JSON")
            print(f"   Settings: {len(loaded)} entries")
            return True
        else:
            print(f"❌ Config file not found after creation!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating config.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_initial_log_file():
    """Create initial log file."""
    print("\n" + "="*60)
    print("CREATING INITIAL LOG FILE")
    print("="*60)
    
    log_file = Path.home() / ".spanish_tutor" / "logs" / f"spanish_tutor_{datetime.now().strftime('%Y%m%d')}.log"
    
    try:
        print(f"📝 Writing to: {log_file}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"Spanish Learning Assistant - Log File\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            f.write("Log file initialized by init_setup.py\n")
            f.write("Waiting for application to start...\n\n")
        
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"✅ Log file created ({size} bytes)")
            return True
        else:
            print(f"❌ Log file not found after creation!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating log file: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_env_file_if_needed():
    """Create .env.txt file in home directory if it doesn't exist."""
    print("\n" + "="*60)
    print("CHECKING .env.txt FILE")
    print("="*60)
    
    home_env = Path.home() / ".spanish_tutor" / ".env.txt"
    project_env = Path.cwd() / ".env.txt"
    
    print(f"📄 Home env file: {home_env}")
    print(f"   Exists: {'✅ Yes' if home_env.exists() else '❌ No'}")
    
    print(f"📄 Project env file: {project_env}")
    print(f"   Exists: {'✅ Yes' if project_env.exists() else '❌ No'}")
    
    # If project .env.txt exists, we're good
    if project_env.exists():
        print(f"\n✅ Using existing project .env.txt")
        return True
    
    # If home .env.txt exists, we're good
    if home_env.exists():
        print(f"\n✅ Using existing home .env.txt")
        return True
    
    # Otherwise, create a template in home directory
    try:
        print(f"\n📝 Creating template .env.txt in home directory")
        
        with open(home_env, 'w', encoding='utf-8') as f:
            f.write("# Spanish Tutor Environment Variables\n")
            f.write("# DO NOT SHARE THIS FILE - IT CONTAINS SENSITIVE API KEYS\n")
            f.write("# Auto-generated by init_setup.py\n\n")
            f.write("# Get your API key from: https://ollama.com/settings/keys\n")
            f.write("# Uncomment and add your key:\n")
            f.write("# OLLAMA_API_KEY=your-api-key-here\n")
        
        if home_env.exists():
            size = home_env.stat().st_size
            print(f"✅ Template .env.txt created ({size} bytes)")
            print(f"   Edit this file to add your API key")
            return True
        else:
            print(f"❌ .env.txt not found after creation!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating .env.txt: {e}")
        return False


def verify_setup():
    """Verify all files were created successfully."""
    print("\n" + "="*60)
    print("VERIFYING SETUP")
    print("="*60)
    
    spanish_dir = Path.home() / ".spanish_tutor"
    config_file = spanish_dir / "config.json"
    logs_dir = spanish_dir / "logs"
    
    checks = []
    
    # Check directory
    print(f"\n📁 .spanish_tutor directory")
    if spanish_dir.exists() and spanish_dir.is_dir():
        print(f"   ✅ Exists")
        checks.append(True)
    else:
        print(f"   ❌ Missing")
        checks.append(False)
    
    # Check config.json
    print(f"\n📄 config.json")
    if config_file.exists() and config_file.is_file():
        size = config_file.stat().st_size
        print(f"   ✅ Exists ({size} bytes)")
        checks.append(True)
    else:
        print(f"   ❌ Missing")
        checks.append(False)
    
    # Check logs directory
    print(f"\n📁 logs directory")
    if logs_dir.exists() and logs_dir.is_dir():
        log_files = list(logs_dir.glob("*.log"))
        print(f"   ✅ Exists ({len(log_files)} log files)")
        checks.append(True)
    else:
        print(f"   ❌ Missing")
        checks.append(False)
    
    # List all contents
    print(f"\n📦 Directory contents:")
    try:
        for item in spanish_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size
                print(f"   - {item.name} ({size} bytes)")
            else:
                count = len(list(item.iterdir())) if item.is_dir() else 0
                print(f"   - {item.name}/ ({count} items)")
    except Exception as e:
        print(f"   ❌ Cannot list contents: {e}")
    
    return all(checks)


def main():
    """Run the initialization."""
    print("\n" + "="*60)
    print("SPANISH LEARNING ASSISTANT - INITIALIZATION")
    print("="*60)
    
    print(f"\n🏠 Home directory: {Path.home()}")
    print(f"📂 Current directory: {Path.cwd()}")
    print(f"🎯 Target directory: {Path.home() / '.spanish_tutor'}")
    
    # Run setup steps
    steps = [
        ("Create directories", create_directory_structure),
        ("Create config.json", create_config_file),
        ("Create initial log", create_initial_log_file),
        ("Check .env.txt", create_env_file_if_needed),
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"\n❌ Step '{step_name}' failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((step_name, False))
    
    # Verify
    print("\n")
    verify_success = verify_setup()
    
    # Summary
    print("\n" + "="*60)
    print("INITIALIZATION SUMMARY")
    print("="*60)
    
    for step_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{step_name:30} {status}")
    
    print(f"{'Final Verification':30} {'✅ SUCCESS' if verify_success else '❌ FAILED'}")
    
    print("\n" + "="*60)
    
    if verify_success and all(r for _, r in results):
        print("🎉 INITIALIZATION COMPLETE!")
        print("\n✅ All files and directories created successfully")
        print(f"\n📁 Location: {Path.home() / '.spanish_tutor'}")
        print("\nNext steps:")
        print("1. Run: python test_config.py")
        print("2. If tests pass, run: streamlit run main.py")
        print("\n💡 Tip: Add your Ollama API key in the app's Options menu")
    else:
        print("⚠️  INITIALIZATION INCOMPLETE")
        print("\nSome files could not be created.")
        print("\nTroubleshooting:")
        print("1. Check if you have write permissions to your home directory")
        print("2. Try running this script as administrator")
        print("3. Check if antivirus is blocking file creation")
        print("4. Manually create the folder:")
        print(f"   {Path.home() / '.spanish_tutor'}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()