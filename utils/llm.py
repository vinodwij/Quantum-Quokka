
import os
import requests

def load_system_prompt(path="prompts/sql_assistant.txt"):
    with open(path, "r") as file:
        return file.read()

def call_llm(user_query):
    system_prompt = load_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    response = requests.post(
        os.getenv("LLM_API_URL"),
        headers={"Content-Type": "application/json"},
        json={
            "model": os.getenv("LLM_MODEL"),
            "messages": messages
        }
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"LLM Error: {response.status_code}"
