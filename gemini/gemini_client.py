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


def generate_cypher_from_paragraph(paragraph_text: str, paragraph_index: int, docname: str) -> str:
    """
    Given a paragraph, ask Gemini to generate Cypher that links:
    - Document node -> Paragraph node
    - Paragraph node -> Extracted Entity nodes
    """
    prompt = f"""
            You are helping to build a Neo4j knowledge graph from a document.

            Input Information:
            - Document filename: "{docname}"
            - Paragraph index: {paragraph_index}
            - Paragraph text:
            \"\"\"
            {paragraph_text}
            \"\"\"

            Task:
            - Create a Document node with label :Document and a property `filename`.
            - Create a Paragraph node with label :Paragraph and properties `index` (integer) and `text` (string).
            - Link Document to Paragraph using relationship :HAS_PARAGRAPH.
            - Extract any Entities (Person, Company, Date, Location, Concept) you find in the paragraph.
            - Create Entity nodes with label :Entity and properties `name` and `type`.
            - Link each Entity to the Paragraph using relationship :CONTAINS_ENTITY.

            Format:
            - Only output clean Cypher statements.
            - Use MERGE for nodes and relationships.
            - Do NOT use LOAD CSV.
            - Do NOT use Markdown (no triple backticks or extra text).
            - No explanations, only the Cypher code.

            Go!
            """

    response = model.generate_content(prompt)

    cypher_code = response.text.strip()

    # Extra safety: remove triple backticks if Gemini returns them
    if cypher_code.startswith("```") and cypher_code.endswith("```"):
        cypher_code = cypher_code.strip("```").strip()

    return cypher_code
