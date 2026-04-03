#!/usr/bin/env python3
"""
Verify Koala noise suppression is properly configured and working.
"""

import os
import sys

def check_env():
    """Check if KOALA_ACCESS_KEY is in environment."""
    print("🔍 Checking environment variables...")
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv("KOALA_ACCESS_KEY")
    if not key or key == "your_koala_access_key_here":
        print("❌ KOALA_ACCESS_KEY not configured in .env")
        return False
    
    print(f"✅ KOALA_ACCESS_KEY found: {key[:20]}...{key[-10:]}")
    return True

def check_import():
    """Check if Koala can be imported."""
    print("\n📦 Checking Koala import...")
    try:
        from pipecat.audio.filters.koala_filter import KoalaFilter
        print("✅ KoalaFilter imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import KoalaFilter: {e}")
        print("   Run: pip install 'pipecat-ai[koala]'")
        return False

def test_initialization():
    """Test Koala initialization with the key."""
    print("\n🧪 Testing Koala initialization...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    key = os.getenv("KOALA_ACCESS_KEY")
    
    try:
        from pipecat.audio.filters.koala_filter import KoalaFilter
        koala = KoalaFilter(access_key=key)
        print("✅ Koala initialized successfully!")
        print(f"   Filter type: {type(koala).__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Koala: {e}")
        return False

def check_config():
    """Check if Koala is enabled in config.yaml."""
    print("\n⚙️ Checking config.yaml...")
    
    try:
        import yaml
        with open("app/config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        noise_suppression = config.get("noise_suppression", {})
        if noise_suppression.get("enabled"):
            print("✅ Koala enabled in config.yaml")
            print(f"   Provider: {noise_suppression.get('provider')}")
            return True
        else:
            print("⚠️ Koala disabled in config.yaml")
            return False
    except Exception as e:
        print(f"⚠️ Could not read config.yaml: {e}")
        return False

def main():
    print("=" * 50)
    print("🔇 KOALA NOISE SUPPRESSION VERIFICATION")
    print("=" * 50)
    
    results = []
    results.append(("Environment", check_env()))
    results.append(("Import", check_import()))
    results.append(("Config", check_config()))
    results.append(("Initialization", test_initialization()))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED - Koala is ready to use!")
        print("\nNext steps:")
        print("1. Start server: python app/main.py")
        print("2. Watch for: '🔇 Koala noise suppression ENABLED'")
    else:
        print("❌ SOME TESTS FAILED - Please fix the issues above")
        sys.exit(1)
    print("=" * 50)

if __name__ == "__main__":
    main()
