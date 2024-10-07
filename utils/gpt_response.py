import aiohttp
import asyncio
from config.settings import OPENAI_API_KEY
import logging

async def get_response(transcription, model, output_method, precontext='Provide a brief and direct response.'):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    messages = [{'role': 'user', 'content': transcription}]
    if output_method != 'Clipboard':
        messages.insert(0, {'role': 'system', 'content': precontext})

    data = {
        'model': model,
        'messages': messages,
        'max_tokens': 150,
        'temperature': 0.7,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                return postprocess_output(ai_response)
    except aiohttp.ClientResponseError as e:
        logging.error(f"HTTP error occurred: {e.status} - {e.message}")
        return "Sorry, I couldn't process your request due to an HTTP error."
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return "An error occurred while generating a response."

def postprocess_output(ai_response):
    unwanted_phrases = ["hello", "hi", "greetings", "thank you", "goodbye", "have a great day"]
    for phrase in unwanted_phrases:
        ai_response = ai_response.replace(phrase, "")
    
    return ai_response.strip()