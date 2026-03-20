"""
checker.py — Calls the custom LLM endpoint and parses structured results.
"""

import json
import os
import re
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config from .env ──────────────────────────────────────────────────────────
API_ENDPOINT = os.getenv("LLM_API_ENDPOINT", "")       # e.g. https://api.example.com/v1/chat/completions
API_KEY      = os.getenv("LLM_API_KEY", "")
MODEL_NAME   = os.getenv("LLM_MODEL_NAME", "")
TIMEOUT      = int(os.getenv("REQUEST_TIMEOUT", "60"))


def _build_prompt(code: str, checklist_items: list[str], language: Optional[str]) -> str:
    lang_hint = f"The code is written in {language}." if language else "Auto-detect the language."
    items_numbered = "\n".join(f"{i+1}. {item}" for i, item in enumerate(checklist_items))

    return f"""You are a senior software engineer performing a thorough code review.

{lang_hint}

## Code to Review
```
{code}
```

## Quality Checklist
{items_numbered}

## Instructions
For EACH checklist item above, provide:
1. `status`: one of "pass", "warn", or "fail"
   - pass = fully satisfied
   - warn = partially satisfied or minor issues
   - fail = not satisfied or serious issues
2. `observation`: a concise, specific observation about the code related to this checklist item (1-3 sentences)
3. `suggestion`: actionable improvement suggestion (leave empty string "" if status is "pass")

Also provide a brief `overall_summary` (2-4 sentences) covering the overall code quality.

Respond ONLY with valid JSON in this exact format — no markdown fences, no preamble:
{{
  "items": [
    {{
      "checklist_item": "<exact checklist item text>",
      "status": "pass|warn|fail",
      "observation": "<your observation>",
      "suggestion": "<your suggestion or empty string>"
    }}
  ],
  "overall_summary": "<overall summary>"
}}
"""


def _call_api(prompt: str) -> dict:
    """
    Sends the prompt to the custom LLM endpoint.
    Supports OpenAI-compatible /v1/chat/completions format.
    Adjust the payload structure below if your endpoint differs.
    """
    if not API_ENDPOINT:
        raise ValueError("LLM_API_ENDPOINT is not set in your .env file.")
    if not API_KEY:
        raise ValueError("LLM_API_KEY is not set in your .env file.")
    if not MODEL_NAME:
        raise ValueError("LLM_MODEL_NAME is not set in your .env file.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # ── Payload (OpenAI-compatible format) ────────────────────────────────────
    # If your endpoint uses a different schema, modify this section.
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a senior software engineer. Always respond with valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    response = requests.post(
        API_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _extract_text(api_response: dict) -> str:
    """
    Extracts the assistant message text from the API response.
    Handles OpenAI-compatible response format.
    Modify this if your endpoint returns a different structure.
    """
    try:
        # OpenAI / most compatible APIs
        return api_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass

    # Fallback: search for any 'content' or 'text' key
    if "content" in api_response:
        return api_response["content"]
    if "text" in api_response:
        return api_response["text"]

    raise ValueError(f"Could not extract text from API response: {api_response}")


def _parse_json(raw: str) -> dict:
    """Strips markdown fences if present and parses JSON."""
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


def run_quality_check(
    code: str,
    checklist_items: list[str],
    language: Optional[str] = None,
) -> dict:
    """
    Main entry point. Returns a dict with 'items' and 'overall_summary',
    or {'error': <message>} on failure.
    """
    try:
        prompt       = _build_prompt(code, checklist_items, language)
        api_response = _call_api(prompt)
        raw_text     = _extract_text(api_response)
        result       = _parse_json(raw_text)

        # Validate expected structure
        if "items" not in result:
            raise ValueError("Response JSON missing 'items' key.")

        return result

    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to the LLM endpoint. Check LLM_API_ENDPOINT in your .env."}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT}s. Try increasing REQUEST_TIMEOUT in .env."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API returned HTTP {e.response.status_code}: {e.response.text[:300]}"}
    except json.JSONDecodeError as e:
        return {"error": f"Could not parse model response as JSON: {e}"}
    except Exception as e:
        return {"error": str(e)}
