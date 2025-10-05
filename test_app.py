#!/usr/bin/env python3
"""
Test script to verify the AI Finance Assistant application structure
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager
        from werkzeug.security import generate_password_hash
        import json
        print("✓ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'templates/base.html',
        'templates/index.html',
        'templates/signup.html',
        'templates/login.html',
        'templates/dashboard.html',
        'templates/privacy_settings.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files exist")
        return True

def test_app_creation():
    """Test if the Flask app can be created"""
    try:
        from app import app
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating Flask app: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing AI Finance Assistant Application...")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("App Creation", test_app_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  Test failed: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! The application is ready to run.")
        print("\nTo run the application:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set your OpenAI API key in config.py")
        print("3. Run: python app.py")
        print("4. Open http://localhost:5000 in your browser")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
