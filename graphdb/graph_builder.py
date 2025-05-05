import re
from neo4j import GraphDatabase, exceptions
import os
from dotenv import load_dotenv
from gemini.gemini_client import generate_narrative_from_cypher

# Load environment
load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def preprocess_script(cypher_script: str) -> str:
    """
    Clean the raw script:
    - Remove stray 'cypher' markers
    - Collapse newlines inside string literals
    - Escape internal double quotes
    """
    # Remove standalone 'cypher' lines
    script = re.sub(r'(?m)^\s*cypher\s*$', '', cypher_script)
    # Collapse newlines and escape double quotes inside literals
    def escape_literal(match):
        content = match.group(1).replace('\n', ' ').replace('"', '\\"')
        return f'"{content}"'
    script = re.sub(r'"([^"\n]*(?:\n[^"\n]*)*)"', escape_literal, script, flags=re.DOTALL)
    return script

def execute_cypher_queries(cypher_script: str):
    """
    Execute each MERGE/CREATE after preprocessing, respecting
    the hierarchy: Documento -> Paragrafo -> Contenuto.
    """
    script = preprocess_script(cypher_script)
    # Split into statements by semicolon
    raw_statements = []
    parts = script.split(';')
    for part in parts:
        for line in part.splitlines():
            stmt = line.strip()
            if stmt:
                raw_statements.append(stmt)

    with driver.session() as session:
        for stmt in raw_statements:
            try:
                session.run(stmt)
            except exceptions.CypherSyntaxError as e:
                print(f"⚠️ Syntax error executing statement:\n{stmt}\n  -> {e.message}")
            except exceptions.Neo4jError as e:
                print(f"⚠️ Error executing statement:\n{stmt}\n  -> {e.message}")
    driver.close()

def interpret_graph(cypher_script: str):
    """
    Stampa analisi semantica in italiano e mostra schema (nodi/relazioni).
    """
    narrative_it = generate_narrative_from_cypher(cypher_script)
    print("\n=== Interpretazione Semantica del Grafo ===\n")
    print(narrative_it)

    with driver.session() as session:
        labels = [r["label"] for r in session.run("CALL db.labels()")]
        rels = [r["relationshipType"] for r in session.run("CALL db.relationshipTypes()")]

    print("\n=== Struttura dello Schema ===\n")
    print("Nodi:")
    for lbl in labels:
        print(f"- {lbl}")
    print("\nRelazioni:")
    for rel in rels:
        print(f"- {rel}")