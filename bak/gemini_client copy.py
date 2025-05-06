# gemini/gemini_client.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from json import JSONDecodeError

# Load project-root .env so that GEMINI_API_KEY loads correctly
load_dotenv(find_dotenv())

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")


def extract_json(s: str) -> str:
    start = None
    depth = 0
    for i, ch in enumerate(s):
        if ch == '{':
            if start is None:
                start = i
            depth += 1
        elif ch == '}' and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                return s[start : i + 1]
    return s


def generate_structured_schema_and_cypher(text: str) -> dict:
    prompt = f"""
You are a knowledge-graph expert. Given this document text, produce a single JSON with keys:
1) "hierarchy": {{…}}
2) "schema": {{…}}
3) "cypher": [ … ]

Output ONLY valid JSON.

Document Text:
{text}
"""
    response = model.generate_content(prompt)
    payload = response.text.strip()

    # strip any code fences
    if payload.startswith("```"):
        lines = payload.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        payload = "\n".join(lines).strip()

    # parse JSON or fallback
    try:
        return json.loads(payload)
    except JSONDecodeError:
        snippet = extract_json(payload)
        try:
            return json.loads(snippet)
        except JSONDecodeError:
            raise ValueError(f"Invalid JSON received from model:\n{payload}")


def generate_semantic_narrative(hierarchy: dict, schema: dict) -> str:
    h = json.dumps(hierarchy, ensure_ascii=False)
    s = json.dumps(schema, ensure_ascii=False)
    prompt = f"""
Sei un esperto di knowledge graph… (resto del prompt)

Gerarchia:
{h}

Schema:
{s}

Risposta:
"""
    response = model.generate_content(prompt)
    narrative = response.text.strip()
    if narrative.startswith("```") and narrative.endswith("```"):
        narrative = narrative.strip("```").strip()
    return narrative
