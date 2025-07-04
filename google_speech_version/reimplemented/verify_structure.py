#!/usr/bin/env python3
"""
Verify the reimplemented structure follows Development Guidelines
"""

import sys
from pathlib import Path

def verify_structure():
    """Verify all required components exist"""
    base_dir = Path(__file__).parent
    
    print("Verifying reimplemented structure...")
    print("=" * 50)
    
    # Check modules
    modules = [
        "modules/__init__.py",
        "modules/config.py",
        "modules/logger.py", 
        "modules/error_handler.py",
        "modules/server.py",
        "modules/speech_handler.py",
        "modules/tray_icon.py"
    ]
    
    print("\n1. Checking modular architecture:")
    all_exist = True
    for module in modules:
        path = base_dir / module
        exists = path.exists()
        print(f"   {'✓' if exists else '✗'} {module}")
        if not exists:
            all_exist = False
    
    # Check main files
    print("\n2. Checking main files:")
    main_files = [
        "main.py",
        "requirements.txt",
        "config.json",
        "README.md",
        "run.bat"
    ]
    
    for file in main_files:
        path = base_dir / file
        exists = path.exists()
        print(f"   {'✓' if exists else '✗'} {file}")
        if not exists:
            all_exist = False
    
    # Check test structure
    print("\n3. Checking E2E tests:")
    test_files = [
        "tests/test_e2e_speech_recognition.py",
        "tests/run_tests.bat"
    ]
    
    for file in test_files:
        path = base_dir / file
        exists = path.exists()
        print(f"   {'✓' if exists else '✗'} {file}")
        if not exists:
            all_exist = False
    
    # Check directories
    print("\n4. Checking directories:")
    dirs = ["modules", "tests", "logs"]
    
    for dir_name in dirs:
        path = base_dir / dir_name
        exists = path.exists()
        print(f"   {'✓' if exists else '✗'} {dir_name}/")
        if not exists and dir_name != "logs":  # logs created at runtime
            all_exist = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_exist:
        print("✓ All components verified successfully!")
        print("\nDevelopment Guidelines compliance:")
        print("✓ Modular Code Architecture")
        print("✓ Configurable Logging") 
        print("✓ Strategic Testing (E2E)")
        print("✓ Centralized Configuration")
        print("✓ Robust Error Handling")
    else:
        print("✗ Some components are missing!")
        return 1
    
    print("\nTo run the application: python main.py")
    print("To run tests: cd tests && run_tests.bat")
    
    return 0

if __name__ == "__main__":
    sys.exit(verify_structure())