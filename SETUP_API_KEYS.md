# 🔑 Setting Up Your API Keys

## OpenAI API Setup

### 1. Create Your .env File

First, create a `.env` file in the project root by copying the example:

```bash
cp env.example .env
```

### 2. Get Your OpenAI API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in with your OpenAI account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)

### 3. Add Your API Key to .env

Open the `.env` file and replace the placeholder with your actual key:

```env
# Replace this line:
OPENAI_API_KEY=your_openai_api_key_here

# With your actual key:
OPENAI_API_KEY=sk-proj-abcdef1234567890...
```

### 4. Choose Your GPT Model

You can use different GPT models based on your needs and access:

```env
# For GPT-4 (most capable, higher cost):
OPENAI_MODEL=gpt-4

# For GPT-4 Turbo (faster, cheaper than GPT-4):
OPENAI_MODEL=gpt-4-turbo-preview

# For GPT-3.5 Turbo (fastest, most affordable):
OPENAI_MODEL=gpt-3.5-turbo

# For GPT-3.5 Turbo 16K (larger context window):
OPENAI_MODEL=gpt-3.5-turbo-16k
```

## Using a Custom GPT or Assistant

If you've created a custom GPT or Assistant in OpenAI:

### Option 1: Using Custom Instructions

Edit `src/content_generator/generator.py` to add your custom instructions:

```python
def _get_system_prompt(self) -> str:
    """Get the system prompt for blog generation"""
    # Add your custom GPT instructions here
    custom_instructions = """
    [Your custom GPT instructions here]
    """

    tone_description = ", ".join(settings.blog_tone)
    return f"""{custom_instructions}

You are a professional content writer for Re-Defined...
"""
```

### Option 2: Using OpenAI Assistants API

If you want to use an OpenAI Assistant ID:

1. Get your Assistant ID from [OpenAI Platform](https://platform.openai.com/assistants)
2. Add to your `.env`:

```env
OPENAI_ASSISTANT_ID=asst_abc123...
```

3. Update the content generator to use the Assistant API (requires code modification)

## Cost Optimization Tips

### 1. Model Selection

- **Development/Testing**: Use `gpt-3.5-turbo` (cheapest)
- **Production**: Use `gpt-4-turbo-preview` (good balance)
- **Premium Content**: Use `gpt-4` (highest quality)

### 2. Token Usage

Monitor your token usage in the OpenAI dashboard. The system logs token usage for each blog:

- Average blog post: ~1,500-2,000 tokens
- Cost per blog (GPT-3.5): ~$0.002-$0.003
- Cost per blog (GPT-4): ~$0.03-$0.06

### 3. Set Usage Limits

Add to your `.env` to set monthly limits:

```env
OPENAI_MONTHLY_LIMIT=100  # Maximum blogs per month
OPENAI_MAX_TOKENS_PER_REQUEST=2000
```

## Testing Your API Key

Run this test script to verify your setup:

```bash
# Activate virtual environment
source venv/bin/activate

# Run Python test
python -c "
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    response = client.chat.completions.create(
        model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
        messages=[{'role': 'user', 'content': 'Say hello'}],
        max_tokens=10
    )
    print('✅ API Key is valid!')
    print(f'Response: {response.choices[0].message.content}')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## Troubleshooting

### Common Issues:

1. **"Invalid API Key"**

   - Make sure you copied the full key including `sk-`
   - Check for extra spaces or quotes

2. **"Rate limit exceeded"**

   - You may need to upgrade your OpenAI plan
   - Add delays between requests

3. **"Model not found"**

   - Ensure you have access to GPT-4 (requires waitlist approval)
   - Fall back to `gpt-3.5-turbo`

4. **"Insufficient quota"**
   - Add billing details to your OpenAI account
   - Set up usage limits

## Security Best Practices

1. **Never commit your .env file to Git** (already in .gitignore)
2. **Use environment variables in production**
3. **Rotate API keys regularly**
4. **Set up usage alerts in OpenAI dashboard**

## Next Steps

After setting up your API key:

1. Run the demo to test everything:

   ```bash
   python demo.py
   ```

2. Generate your first blog:

   ```bash
   python app.py
   # Then visit http://localhost:8000/docs
   ```

3. Use the dashboard:
   ```bash
   streamlit run dashboard.py
   # Visit http://localhost:8501
   ```

Happy blogging! 🚀
