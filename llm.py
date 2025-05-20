import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("LLM_API_URL")
MODEL   = os.getenv("LLM_MODEL")

def llm_chat(messages, temperature=0.0, max_tokens=512):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    res = requests.post(API_URL, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json()
    return data["choices"][0]["message"]["content"].strip()
