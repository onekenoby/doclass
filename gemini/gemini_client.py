import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure Gemini with your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize the Gemini model (use gemini-pro for text understanding)
model = genai.GenerativeModel(model_name="gemini-pro")

def generate_cypher_from_text(text: str) -> str:
    """
    Send the extracted text to Gemini and receive Cypher queries.
    """
    prompt = f"""
    Read the following document text and extract relevant entities and relationships.
    Generate Cypher queries to create a Neo4j knowledge graph. Use clear MERGE or CREATE syntax.

    Document:
    {text}
    """
    response = model.generate_content(prompt)

    # Return raw Cypher output
    return response.text.strip()
