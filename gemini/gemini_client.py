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
    """

    response = model.generate_content(prompt)

    raw = response.text.strip()

    if raw.startswith("```") and raw.endswith("```"):
        raw = raw.strip("```").strip()

    return raw
