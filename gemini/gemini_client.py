import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure Gemini with your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

def generate_cypher_from_text(text: str) -> str:
    """
    Given the full document text, extract all distinct node types and relationships.
    • Include structural nodes: Document, Section, Paragraph.
    • Include content entity types (e.g. Person, Organization, Location, Date, Regulation, Acronym, Procedure, etc.).
    • Extract every relationship between them (e.g. ISSUED_BY, LOCATED_AT, GOVERNED_BY, RESPONSIBLE_FOR, HAS_DEADLINE, DESCRIBES, etc.).
    • Use MERGE to avoid duplicates on unique properties.
    Output only raw Cypher MERGE statements (one per line), no explanations or markdown.
    """
    prompt = f"""
You are a KG generation assistant. Analyze the following document text and:
1. Identify structural nodes: Document, Section, Paragraph.
2. Identify as many entity types (nodes) as possible: Person, Organization, Location, Date, Regulation, Acronym, Procedure, etc.
3. Identify all relationships between these nodes, naming them clearly (e.g., ISSUED_BY, LOCATED_AT, GOVERNED_BY, RESPONSIBLE_FOR, HAS_DEADLINE, DESCRIBES).
4. Use Cypher MERGE statements to create each node with appropriate labels & properties and to connect them.
5. Ensure deduplication: MERGE on unique properties for identical entities.
6. Only output the raw Cypher code (one MERGE per line), no markdown.

Document Text:
{text}
"""
    response = model.generate_content(prompt)
    cypher_code = response.text.strip()
    if cypher_code.startswith("```") and cypher_code.endswith("```"):
        cypher_code = cypher_code.strip("```").strip()
    return cypher_code


def generate_narrative_from_cypher(cypher_script: str) -> str:
    """
    Fornisci in italiano un'interpretazione approfondita dei comandi Cypher:
    • Evidenzia tutti i tipi di nodo e relazioni creati.
    • Segui la gerarchia Documento -> Paragrafo -> Contenuto.
    • Descrivi insight rilevanti e relazioni implicite.
    """
    prompt = f"""
Sei un esperto di knowledge graph. In italiano:
1. Analizza i seguenti comandi Cypher e riassumi tutti i tipi di nodi (label) e relazioni (edge) creati.
2. Segui la gerarchia: Documento -> Paragrafo -> Contenuto.
3. Riporta insight e relazioni chiave che emergono dal grafo.
4. Fornisci un testo coerente, senza codice o markdown.

{cypher_script}
"""
    response = model.generate_content(prompt)
    narrative = response.text.strip()
    if narrative.startswith("```") and narrative.endswith("```"):
        narrative = narrative.strip("```").strip()
    return narrative
