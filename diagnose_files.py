"""
File Creation Diagnostics
=========================
This script diagnoses why config.json and log files are not being created.
It tests directory creation, file writing, and permissions.

Usage: python diagnose_files.py
"""

import os
import sys
from pathlib import Path
import json

def test_home_directory():
    """Test access to home directory."""
    print("\n" + "="*60)
    print("TESTING HOME DIRECTORY")
    print("="*60)
    
    try:
        home = Path.home()
        print(f"✅ Home directory: {home}")
        print(f"✅ Home exists: {home.exists()}")
        print(f"✅ Home is directory: {home.is_dir()}")
        
        # Check if we can list home directory
        try:
            items = list(home.iterdir())
            print(f"✅ Can list home directory ({len(items)} items)")
        except Exception as e:
            print(f"❌ Cannot list home directory: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing home directory: {e}")
        return False


def test_create_spanish_tutor_dir():
    """Test creating .spanish_tutor directory."""
    print("\n" + "="*60)
    print("TESTING .spanish_tutor DIRECTORY CREATION")
    print("="*60)
    
    try:
        spanish_dir = Path.home() / ".spanish_tutor"
        print(f"📁 Target directory: {spanish_dir}")
        
        # Try to create it
        spanish_dir.mkdir(parents=True, exist_ok=True)
        
        if spanish_dir.exists():
            print(f"✅ Directory exists!")
            print(f"✅ Is directory: {spanish_dir.is_dir()}")
            
            # Test write permissions
            test_file = spanish_dir / "test_write.txt"
            try:
                test_file.write_text("This is a test")
                print(f"✅ Can write to directory")
                
                # Read it back
                content = test_file.read_text()
                print(f"✅ Can read from directory: '{content}'")
                
                # Delete test file
                test_file.unlink()
                print(f"✅ Can delete from directory")
                
                return True
                
            except Exception as e:
                print(f"❌ Cannot write to directory: {e}")
                return False
        else:
            print(f"❌ Directory was not created!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_config_json():
    """Test creating config.json file."""
    print("\n" + "="*60)
    print("TESTING config.json CREATION")
    print("="*60)
    
    try:
        config_file = Path.home() / ".spanish_tutor" / "config.json"
        print(f"📄 Target file: {config_file}")
        
        # Test data
        test_config = {
            "version": "1.0.0",
            "test": "This is a test config",
            "created_by": "diagnose_files.py"
        }
        
        # Try to write JSON
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2)
        
        print(f"✅ File written")
        
        # Check if file exists
        if config_file.exists():
            size = config_file.stat().st_size
            print(f"✅ File exists ({size} bytes)")
            
            # Try to read it back
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            
            print(f"✅ File readable")
            print(f"✅ Content: {loaded}")
            
            # Delete test file
            config_file.unlink()
            print(f"✅ Test file deleted")
            
            return True
        else:
            print(f"❌ File not found after write!")
            return False
            
    except Exception as e:
        print(f"❌ Error with config.json: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_logs_directory():
    """Test creating logs directory."""
    print("\n" + "="*60)
    print("TESTING logs DIRECTORY CREATION")
    print("="*60)
    
    try:
        logs_dir = Path.home() / ".spanish_tutor" / "logs"
        print(f"📁 Target directory: {logs_dir}")
        
        # Try to create it
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        if logs_dir.exists():
            print(f"✅ Directory exists!")
            
            # Test writing a log file
            from datetime import datetime
            log_file = logs_dir / f"test_log_{datetime.now().strftime('%Y%m%d')}.log"
            
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("Test log entry\n")
                    f.write("This is a test\n")
                
                print(f"✅ Log file created: {log_file}")
                
                if log_file.exists():
                    size = log_file.stat().st_size
                    print(f"✅ Log file exists ({size} bytes)")
                    
                    # Delete test file
                    log_file.unlink()
                    print(f"✅ Test log deleted")
                    
                    return True
                else:
                    print(f"❌ Log file not found after write!")
                    return False
                    
            except Exception as e:
                print(f"❌ Cannot write log file: {e}")
                return False
        else:
            print(f"❌ Logs directory was not created!")
            return False
            
    except Exception as e:
        print(f"❌ Error creating logs directory: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_modules():
    """Test importing our custom modules."""
    print("\n" + "="*60)
    print("TESTING MODULE IMPORTS")
    print("="*60)
    
    modules_to_test = [
        'config_manager',
        'logger_config'
    ]
    
    all_success = True
    
    for module_name in modules_to_test:
        try:
            print(f"\n📦 Testing {module_name}...")
            module = __import__(module_name)
            print(f"✅ {module_name} imported successfully")
            
            # Test specific functions
            if module_name == 'config_manager':
                print(f"   Testing load_config()...")
                config = module.load_config()
                print(f"   ✅ Config loaded: {len(config)} settings")
                
                print(f"   Testing get_config_info()...")
                info = module.get_config_info()
                print(f"   ✅ Config info retrieved")
                
            elif module_name == 'logger_config':
                print(f"   Testing setup_logging()...")
                module.setup_logging(log_level="INFO", log_to_file=True, log_to_console=False)
                print(f"   ✅ Logging setup complete")
                
                print(f"   Testing get_log_file_path()...")
                log_path = module.get_log_file_path()
                print(f"   ✅ Log path: {log_path}")
                
        except Exception as e:
            print(f"❌ {module_name} failed: {e}")
            import traceback
            traceback.print_exc()
            all_success = False
    
    return all_success


def check_existing_files():
    """Check what files currently exist."""
    print("\n" + "="*60)
    print("CHECKING EXISTING FILES")
    print("="*60)
    
    spanish_dir = Path.home() / ".spanish_tutor"
    config_file = spanish_dir / "config.json"
    logs_dir = spanish_dir / "logs"
    env_file = spanish_dir / ".env.txt"
    
    print(f"\n📁 Spanish tutor directory: {spanish_dir}")
    print(f"   Exists: {'✅ Yes' if spanish_dir.exists() else '❌ No'}")
    
    if spanish_dir.exists():
        try:
            items = list(spanish_dir.iterdir())
            print(f"   Contents ({len(items)} items):")
            for item in items:
                size = item.stat().st_size if item.is_file() else "DIR"
                print(f"     - {item.name} ({size})")
        except Exception as e:
            print(f"   ❌ Cannot list contents: {e}")
    
    print(f"\n📄 Config file: {config_file}")
    print(f"   Exists: {'✅ Yes' if config_file.exists() else '❌ No'}")
    if config_file.exists():
        size = config_file.stat().st_size
        print(f"   Size: {size} bytes")
    
    print(f"\n📁 Logs directory: {logs_dir}")
    print(f"   Exists: {'✅ Yes' if logs_dir.exists() else '❌ No'}")
    
    if logs_dir.exists():
        try:
            log_files = list(logs_dir.glob("*.log*"))
            print(f"   Log files: {len(log_files)}")
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"     - {log_file.name} ({size} bytes)")
        except Exception as e:
            print(f"   ❌ Cannot list log files: {e}")
    
    print(f"\n📄 Env file (home): {env_file}")
    print(f"   Exists: {'✅ Yes' if env_file.exists() else '❌ No'}")
    
    # Also check project directory
    project_env = Path.cwd() / ".env.txt"
    print(f"\n📄 Env file (project): {project_env}")
    print(f"   Exists: {'✅ Yes' if project_env.exists() else '❌ No'}")


def test_permissions():
    """Test file system permissions."""
    print("\n" + "="*60)
    print("TESTING FILE SYSTEM PERMISSIONS")
    print("="*60)
    
    test_locations = [
        Path.home(),
        Path.home() / ".spanish_tutor",
        Path.cwd()
    ]
    
    for location in test_locations:
        print(f"\n📁 Location: {location}")
        
        if not location.exists():
            print(f"   ⚠️  Location does not exist")
            continue
        
        # Test read
        try:
            list(location.iterdir())
            print(f"   ✅ Read: OK")
        except Exception as e:
            print(f"   ❌ Read: FAILED - {e}")
        
        # Test write
        test_file = location / ".test_permission"
        try:
            test_file.write_text("test")
            print(f"   ✅ Write: OK")
            test_file.unlink()
        except Exception as e:
            print(f"   ❌ Write: FAILED - {e}")


def main():
    """Run all diagnostic tests."""
    print("\n" + "="*60)
    print("SPANISH LEARNING ASSISTANT - FILE DIAGNOSTICS")
    print("="*60)
    
    print(f"\n🐍 Python version: {sys.version}")
    print(f"💻 Platform: {sys.platform}")
    print(f"📂 Current directory: {Path.cwd()}")
    print(f"🏠 Home directory: {Path.home()}")
    
    # Run tests
    tests = [
        ("Home Directory Access", test_home_directory),
        ("Permissions Check", test_permissions),
        ("Create .spanish_tutor", test_create_spanish_tutor_dir),
        ("Create config.json", test_create_config_json),
        ("Create logs directory", test_create_logs_directory),
        ("Import Modules", test_import_modules),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Check what exists now
    check_existing_files()
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All diagnostics passed!")
        print("\nThe config.json and log files should now be created.")
        print("Try running: python test_config.py")
    else:
        print("\n⚠️  Some diagnostics failed.")
        print("\nPossible issues:")
        print("1. Permission problems with home directory")
        print("2. Antivirus blocking file creation")
        print("3. Disk space issues")
        print("4. Windows user profile problems")
        
        print("\nSuggested fixes:")
        print("1. Run as administrator")
        print("2. Check antivirus logs")
        print("3. Try creating .spanish_tutor folder manually in:")
        print(f"   {Path.home()}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()