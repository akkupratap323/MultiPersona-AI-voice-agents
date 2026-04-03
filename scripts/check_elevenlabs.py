#!/usr/bin/env python3
"""Check ElevenLabs API key validity, subscription/credits, and voice compatibility."""
import os
import sys

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

def main():
    raw = os.environ.get("ELEVENLABS_API_KEY", "").strip().strip('"').strip("'")
    api_key = raw
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip().strip('"').strip("'")

    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in environment or .env")
        sys.exit(1)
    print(f"API key length: {len(api_key)} chars")

    try:
        import httpx
    except ImportError:
        print("ERROR: httpx required. Run: pip install httpx")
        sys.exit(1)

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}

    # 1. Check user subscription (credits)
    print("Checking subscription and credits...")
    try:
        r = httpx.get("https://api.elevenlabs.io/v1/user/subscription", headers=headers, timeout=10.0)
        if r.status_code == 401:
            print("  Result: INVALID API KEY (401 Unauthorized)")
            print("  Fix: Get a new API key from https://elevenlabs.io/app/settings/api-keys")
            print("  Ensure the key is copied fully (no spaces), then set ELEVENLABS_API_KEY in .env")
            sys.exit(1)
        if r.status_code != 200:
            print(f"  Result: Unexpected status {r.status_code}: {r.text[:200]}")
            sys.exit(1)
        data = r.json()
        # New API uses character_count / character_limit; some use credits
        char_count = data.get("character_count") or data.get("characters_used") or 0
        char_limit = data.get("character_limit") or data.get("character_count_limit") or 0
        tier = data.get("tier") or data.get("subscription", {}).get("tier") or "unknown"
        status = data.get("status") or "unknown"
        print(f"  Tier: {tier}")
        print(f"  Status: {status}")
        print(f"  Characters used: {char_count}")
        print(f"  Character limit: {char_limit}")
        if char_limit and char_limit > 0:
            remaining = max(0, char_limit - char_count)
            print(f"  Remaining (approx): {remaining}")
            if remaining == 0:
                print("  WARNING: No credits remaining.")
        print("  API key is valid.")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    # 2. Check voice exists and is available
    print("\nChecking voice compatibility...")
    try:
        r = httpx.get(f"https://api.elevenlabs.io/v1/voices/{voice_id}", headers=headers, timeout=10.0)
        if r.status_code == 401:
            print("  Result: INVALID API KEY (401)")
            sys.exit(1)
        if r.status_code == 404:
            print(f"  Result: Voice ID '{voice_id}' NOT FOUND. It may be invalid or not available on this account.")
            sys.exit(1)
        if r.status_code != 200:
            print(f"  Result: Status {r.status_code}: {r.text[:200]}")
            sys.exit(1)
        voice = r.json()
        name = voice.get("name", "?")
        labels = voice.get("labels", {})
        category = voice.get("category", "?")
        print(f"  Voice ID: {voice_id}")
        print(f"  Name: {name}")
        print(f"  Category: {category}")
        print(f"  Labels: {labels}")
        print("  Voice is valid and available for this key.")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    # 3. Test TTS generation (small test to verify API works)
    print("\nTesting TTS generation with voice...")
    try:
        test_text = "Hello, this is a test."
        payload = {
            "text": test_text,
            "model_id": "eleven_multilingual_v2",  # Same model as your config
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json=payload,
            timeout=15.0
        )
        if r.status_code == 401:
            print("  Result: INVALID API KEY (401) - Cannot generate speech")
            sys.exit(1)
        if r.status_code == 400:
            print(f"  Result: Bad request (400) - {r.text[:200]}")
            print("  This might indicate voice/model incompatibility or invalid parameters")
            sys.exit(1)
        if r.status_code == 402:
            print("  Result: PAYMENT REQUIRED (402) - No credits remaining")
            print("  You need to add credits to your ElevenLabs account")
            sys.exit(1)
        if r.status_code != 200:
            print(f"  Result: Status {r.status_code}: {r.text[:200]}")
            sys.exit(1)
        # Success - got audio data
        audio_size = len(r.content)
        print(f"  TTS generation successful! Generated {audio_size} bytes of audio")
        print(f"  Voice '{voice_id}' works with model 'eleven_multilingual_v2'")
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    print("\n✅ All checks passed. API key is valid, voice is available, and TTS generation works!")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
