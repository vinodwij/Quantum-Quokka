import os
import logging
import requests
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def configure_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


logger = configure_logger()


def load_system_prompt(prompt_path: str = "prompts/sql_assistant.txt") -> str:
    """
    Load the system prompt from the given file path.
    Raises FileNotFoundError if the file is missing.
    """
    prompt_file = Path(prompt_path)
    if not prompt_file.is_file():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    content = prompt_file.read_text(encoding="utf-8").strip()
    logger.info(f"Loaded system prompt from {prompt_path}")
    return content


def call_llm(user_query: str, prompt_path: str = "prompts/sql_assistant.txt") -> str:
    """
    Call the LLM API with the provided user query and system prompt.
    Returns the LLM's response content or an error string.
    """
    if not user_query or not user_query.strip():
        logger.error("Empty user query")
        raise ValueError("User query cannot be empty")

    api_url = os.getenv("LLM_API_URL")
    model = os.getenv("LLM_MODEL")
    if not api_url or not model:
        error_msg = "Environment variables LLM_API_URL and LLM_MODEL must be set"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)

    system_prompt = load_system_prompt(prompt_path)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query.strip()}
    ]

    try:
        response = requests.post(
            api_url,
            json={"model": model, "messages": messages},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        choices = result.get("choices")
        if not choices:
            logger.error(f"No choices in LLM response: {result}")
            raise ValueError("Invalid LLM response: no choices")
        content = choices[0]["message"]["content"].strip()
        logger.info("Received LLM response")
        return content
    except requests.Timeout:
        logger.error("LLM API request timed out")
        return "LLM Error: Request timed out"
    except requests.HTTPError as e:
        status = response.status_code if response is not None else 'Unknown'
        logger.error(f"LLM API HTTP error {status}: {e}")
        return f"LLM Error: HTTP {status}"
    except requests.RequestException as e:
        logger.error(f"LLM API request failed: {e}")
        return f"LLM Error: {e}"
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return f"LLM Error: {e}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "LLM Error: Unexpected error occurred"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python llm.py \"<your query>\"")
        sys.exit(1)
    query = " ".join(sys.argv[1:])
    try:
        response = call_llm(query)
        print(response)
    except Exception as e:
        print(f"Error: {e}")
