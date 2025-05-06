# gemini/gemini_client.py

"""Robust Gemini client that works across old/new google-generativeai SDK versions.
   – Prefers native JSON output when supported.
   – Gracefully falls back to parsing text when not.
"""
import os
import json
import re
import inspect
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from json import JSONDecodeError

load_dotenv(find_dotenv())
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.0-flash")

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
BASE_PROMPT = """You are an expert Neo4j graph‑modeler.
Return ONLY a JSON object (no markdown fences) with keys:
  "hierarchy", "schema", "cypher".
Follow rules:
• nouns → nodeTypes (PascalCase)                
• verbs  → relationshipTypes (UPPER_SNAKE_CASE)
• IDs must look like P{{p}}_S{{s}}_E{{e}}
Document Text:
{doc}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _try_generate(prompt: str):
    """Call model; auto‑downgrade if certain kwargs unsupported."""
    kwargs1 = dict(
        generation_config={"temperature": 0.2},
        response_format={"type": "json_object"},
    )
    try:
        return model.generate_content(prompt, **kwargs1)
    except TypeError as e:
        # Remove response_format first
        if "response_format" in str(e):
            kwargs1.pop("response_format")
            try:
                return model.generate_content(prompt, **kwargs1)
            except TypeError as e2:
                # Fallback to bare call with temperature positional/back‑compat
                return model.generate_content(prompt, temperature=0.2)
        # Unknown other TypeError – retry simplest signature
        return model.generate_content(prompt, temperature=0.2)


def _extract_json_snippet(text: str) -> str:
    """Return first balanced {...} block."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text


def _sanitize(text: str) -> str:
    text = re.sub(r",\s*[}\]]", lambda m: m.group(0).lstrip(","), text)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    return text


def _legacy_parse(raw: str) -> dict:
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("```")]
    txt = _sanitize("\n".join(lines))
    snippet = _extract_json_snippet(txt)
    try:
        return json.loads(snippet)
    except JSONDecodeError as e:
        raise ValueError(
            "Gemini returned non‑JSON content and parsing failed:\n" + str(e)
        )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_structured_schema_and_cypher(text: str) -> dict:
    prompt = BASE_PROMPT.format(doc=text)

    response = _try_generate(prompt)

    # Path A: SDK provides structured parts
    try:
        part0 = response.candidates[0].content.parts[0]
        if hasattr(part0, "json_content"):
            return part0.json_content
        candidate_text = getattr(part0, "text", None)
    except (AttributeError, IndexError):
        candidate_text = getattr(response, "text", None)

    if candidate_text:
        try:
            return json.loads(candidate_text)
        except JSONDecodeError:
            pass  # fallthrough
    # Path C: legacy parse
    return _legacy_parse(candidate_text or "")


def generate_semantic_narrative(hierarchy: dict, schema: dict) -> str:
    """Return an Italian narrative explaining how KG maps to the text."""
    prompt = f"""
Sei un esperto di knowledge graph. Spiega, in italiano, come ogni nodo e relazione derivano dal testo originale usando la seguente gerarchia e schema.

Gerarchia:
{json.dumps(hierarchy, ensure_ascii=False)}

Schema:
{json.dumps(schema, ensure_ascii=False)}
"""
    response = _try_generate(prompt)
    # Extract plain text regardless of SDK surface
    if hasattr(response, "text") and response.text:
        text_out = response.text
    elif hasattr(response, "candidates") and response.candidates:
        text_out = response.candidates[0].text
    else:
        text_out = str(response)
    return text_out.strip("`").strip()
