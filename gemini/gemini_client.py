import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure Gemini with your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Gemini model (use gemini-pro for text understanding)
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

def generate_cypher_from_text(text: str) -> str:
    """
    Send text to Gemini and return Cypher queries without any LOAD CSV commands.
    """
    prompt = f"""
Read the following document and extract entities (e.g., Person, Company, Date)
and relationships between them.

Generate clean, standalone Neo4j Cypher CREATE or MERGE queries only.

⚡ Do NOT use LOAD CSV.
⚡ Do NOT reference any external files.
⚡ Do NOT use CALL procedures.

Document:
{text}

- No explanations, only the Cypher code.
- Do NOT use Markdown (no triple backticks or extra text).

Go!
"""
    response = model.generate_content(prompt)
    cypher_code = response.text.strip()
    # Extra safety: remove triple backticks if Gemini returns them
    if cypher_code.startswith("```") and cypher_code.endswith("```"):
        cypher_code = cypher_code.strip("```").strip()
    return cypher_code


def generate_narrative_from_cypher(cypher_script: str) -> str:
    """
    Fornisci in italiano una interpretazione approfondita dei comandi Cypher,
    seguendo la gerarchia Documento -> Paragrafo -> Contenuto.
    """
    prompt = f"""
Sei un assistente esperto nella semantica dei grafi di conoscenza.
Fornisci in italiano una interpretazione approfondita dei seguenti comandi Cypher,
tenendo conto della gerarchia di informazione: Documento -> Paragrafo -> Contenuto.
Evidenzia concetti chiave, relazioni implicite e insight rilevanti.

{cypher_script}
"""
    response = model.generate_content(prompt)
    narrative = response.text.strip()
    # Strip any ``` fences
    if narrative.startswith("```") and narrative.endswith("```"):
        narrative = narrative.strip("```").strip()
    return narrative

