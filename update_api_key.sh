#!/bin/bash
echo "🔑 OpenAI API Key Update Script"
echo "================================"
echo ""
echo "Please enter your OpenAI API key:"
read -p "API Key (starts with sk-): " api_key

if [[ $api_key == sk-* ]]; then
    # Update the .env file
    sed -i '' "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
    echo "✅ API key updated successfully!"
    
    # Test the key
    echo ""
    echo "🧪 Testing your API key..."
    python test_openai.py
else
    echo "❌ Error: API key should start with 'sk-'"
    echo "Please get your key from: https://platform.openai.com/api-keys"
fi 