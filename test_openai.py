#!/usr/bin/env python3
"""
Quick test script to verify your OpenAI API key is working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is set
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

if not api_key or api_key == 'your_openai_api_key_here':
    print("❌ Error: OpenAI API key not set!")
    print("Please edit your .env file and add your actual API key")
    print("Get your key from: https://platform.openai.com/api-keys")
    sys.exit(1)

print(f"🔑 API Key found: {api_key[:7]}...{api_key[-4:]}")
print(f"🤖 Model: {model}")

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    
    print("\n🧪 Testing API connection...")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Re-Defined!' in a cheerful way."}
        ],
        max_tokens=50
    )
    
    print("✅ Success! API is working properly.")
    print(f"\n🤖 GPT Response: {response.choices[0].message.content}")
    print(f"\n📊 Tokens used: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible issues:")
    print("1. Invalid API key - double-check you copied it correctly")
    print("2. No credit balance - add billing details to your OpenAI account")
    print("3. Model access - you may not have access to GPT-4 yet")
    print("4. Network issues - check your internet connection")
    
print("\n✨ Next steps:")
print("1. Run the demo: python ../demo.py")
print("2. Start the app: python ../app.py")
print("3. Open dashboard: streamlit run ../dashboard.py") 