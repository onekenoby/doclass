# gemini/gemini_client.py

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from json import JSONDecodeError
from google.generativeai import types

# Load project‑root .env so that GEMINI_API_KEY loads correctly
load_dotenv(find_dotenv())

# ────────────────  Gemini configuration  ────────────────
# You can switch model versions here if needed (e.g. "models/gemini-1.5-pro-latest")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")


############################################
# Utility helper to grab the first JSON blob
############################################

def extract_json(s: str) -> str:
    """Return the first balanced‑brace JSON object found inside *s*."""
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


###############################################################
# 1️⃣  MAIN ENTRY – STRUCTURED KG & CYPHER GENERATION PROMPT  #
###############################################################

def generate_structured_schema_and_cypher(text: str) -> dict:
    """Given raw document text, produce a rich JSON spec and Cypher script.

    The prompt below is engineered to maximise **coverage** and **granularity**
    of the resulting knowledge‑graph while keeping the output machine‑parsable.
    """
    prompt = f"""
You are an expert **knowledge‑graph architect** and **triple extractor**.
Your goal is to convert the following document into a *dense* but *coherent*
knowledge graph, surfacing as many meaningful **entities** (nodes) and
**relationships** (edges) as the text reasonably supports.  
Aim for high *recall* while keeping *precision* acceptable (≥ 0.4).

Return **one** valid JSON object with **exactly** these keys:

1.  \"hierarchy\"  – a recursive outline capturing topical structure. Example:  
        {{ \"root\": \"Quantum Computing\",
           \"children\": [ {{ \"title\": \"Qubits\" }} ] }}

2.  \"schema\" – describes the graph model, with two top‑level keys:  
       • nodes:          list<{{label, properties:{{name:type}}}}>  
       • relationships:  list<{{type, properties:{{name:type}}}}>

3.  \"cypher\" – **array** of Cypher statements that instantiate *all* extracted
       nodes **and** relationships and set their properties.

---

## Extraction guidelines
• Create **separate nodes** for distinct real‑world entities: persons, orgs,
  locations, events, concepts, dates, numerical facts, URLs, etc.  
  – Use *singular nouns* for node labels (PascalCase or snake_case).  
• Create **separate relationships** for distinct real‑world connections and map
  every **verb / verbal phrase** you detect to a relationship type in
  `UPPER_SNAKE_CASE` (e.g. PUBLISHED_BY, LOCATED_IN).  
  – Use *verbs* for relationship types (UPPER_SNAKE_CASE).
• Create all the relationships you can find among the nodes, even if they are
  not explicitly mentioned in the text.  
  – Use *verbs* for relationship types (UPPER_SNAKE_CASE).  
  – Use *singular nouns* for node labels (PascalCase or snake_case).  
  – Use *singular nouns* for relationship types (UPPER_SNAKE_CASE).
• **Mandatory balance – the graph must contain at least ⌈nodes ÷ 2⌉
  relationship statements.**  
• Emit each relationship as a *self‑contained* one‑liner, e.g.  
  – *Inline‑merge*  
    `MERGE (a:Person {{name:'Ada'}}) MERGE (b:Field {{name:'Math'}}) MERGE (a)-[:PIONEER_OF]->(b);`  
  – *Property‑match*  
    `MATCH (a:Person {{name:'Ada'}}),(b:Field {{name:'Math'}}) MERGE (a)-[:PIONEER_OF]->(b);`  
  (Variables must be declared and used inside the **same** physical line.)  
• Resolve pronouns / coreferences where clear.  
• Add properties when available (date, url, amount, confidence).  
  ➜ If confidence < 0.6 still include the edge but tag `confidence: float`.

---

## Cypher syntax constraints (STRICT)
• **One‑liner rule** – Every Cypher statement must appear on a single physical
  line and terminate with a semicolon `;`. No unescaped line‑break characters
  are allowed outside quoted strings.  
• **Balanced quotes** – String literals use single quotes `'...'`. Inside them,
  escape any embedded single quote as `\\'` and replace real line‑breaks with
  the two‑character sequence `\\n`.  
• **Valid identifiers** – Node labels and relationship types must be valid
  Neo4j identifiers. Prefer letters/digits/`_`; if spaces/punctuation remain,
  wrap the whole identifier in back‑ticks (`` `Label With Space` ``).  
• **Variables** – Start with a lower‑case letter, contain only letters, digits
  or `_`.  
• **No stray text** – Output nothing except Cypher (`MERGE`, `CREATE`, `MATCH`,
  etc.); no comments or blank lines.

---

## Graph size target
• Produce **≥ 15 distinct nodes** *or* cover ≥ 90 % of factual statements –
  whichever yields the larger graph.

---

## Output format
• Output **ONLY** the JSON object – no prose, no markdown fences.

Document Text ↓↓↓
{text}
"""

    # === Call the model ===
    response = model.generate_content(prompt)
    payload = response.text.strip()

    # ── Strip possible ``` fences ──────────────────────────────
    if payload.startswith("```"):
        lines = payload.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        payload = "\n".join(lines).strip()

    # ── Parse the JSON or fall back to best‑effort extraction ──
    try:
        return json.loads(payload)
    except JSONDecodeError:
        snippet = extract_json(payload)
        try:
            return json.loads(snippet)
        except JSONDecodeError:
            raise ValueError(f"Invalid JSON received from model:\n{payload}")


#################################################
# 2️⃣  NATURAL‑LANGUAGE NARRATIVE (unchanged)   #
#################################################

def generate_semantic_narrative(hierarchy: dict, schema: dict) -> str:
    """Italian narrative summary of the graph structure for UI/tooltips."""
    h = json.dumps(hierarchy, ensure_ascii=False)
    s = json.dumps(schema, ensure_ascii=False)
    prompt = f"""
Sei un esperto di knowledge graph. Usa la gerarchia e lo schema seguenti per
produrre una narrazione fluida ed avvincente (in italiano) che spieghi cosa
rappresenta il grafo, evidenzi i concetti chiave e le relazioni più
significative.

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
