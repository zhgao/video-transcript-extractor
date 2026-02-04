#!/usr/bin/env python3
"""
Test Whisper transcription with a short YouTube video
"""

import requests
import json

# Test with a short video (30 seconds or less recommended for testing)
# This is a short motivational clip
test_url = "https://www.youtube.com/watch?v=ZXsQAXx_ao0"  # "Just Do It" - 1 min

print("Testing Whisper AI transcription...")
print(f"Video URL: {test_url}")
print("\nThis will:")
print("1. Download the audio from the video")
print("2. Use Whisper AI to transcribe it")
print("3. This may take 1-3 minutes for the first run (downloading model)")
print("\nStarting transcription...\n")

try:
    response = requests.post(
        'http://localhost:8080/test-whisper',
        json={'url': test_url},
        timeout=600  # 10 minute timeout
    )
    
    result = response.json()
    
    if result.get('success'):
        print("✓ SUCCESS!")
        print("\nTranscript:")
        print("-" * 80)
        print(result['transcript'])
        print("-" * 80)
        print(f"\nMethod used: {result.get('method', 'unknown')}")
    else:
        print("✗ FAILED")
        print(f"Error: {result.get('error')}")
        
except requests.exceptions.Timeout:
    print("✗ Request timed out (transcription took too long)")
except Exception as e:
    print(f"✗ Error: {str(e)}")
