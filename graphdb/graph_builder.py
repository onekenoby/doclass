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

def execute_cypher_queries(cypher_script: str):
    """
    Execute the given Cypher script by running each statement (CREATE or MERGE)
    separately, respecting the hierarchy: Document -> Paragraph -> Content.
    This approach ensures we systematically retrieve and create all nodes and
    relationships in the knowledge graph.
    Splits on semicolons and newlines, skipping empty lines and stripping trailing semicolons.
    """
    # Split script into individual statements
    raw_statements = []
    parts = cypher_script.split(';')
    for part in parts:
        for line in part.splitlines():
            stmt = line.strip()
            if not stmt:
                continue
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
    Stampa una narrazione approfondita in italiano del grafo
    e mostra la struttura dello schema (nodi e relazioni).
    """
    # Narrazione semantica in italiano
    narrative_it = generate_narrative_from_cypher(cypher_script)
    print("\n=== Interpretazione Semantica del Grafo ===\n")
    print(narrative_it)

    # Recupera struttura dello schema: etichette e tipi di relazioni
    with driver.session() as session:
        labels = [record["label"] for record in session.run("CALL db.labels()")]
        rel_types = [record["relationshipType"] for record in session.run("CALL db.relationshipTypes()")]

    print("\n=== Struttura dello Schema ===\n")
    print("Nodi (etichette):")
    for lbl in labels:
        print(f"- {lbl}")
    print("\nRelazioni:")
    for rt in rel_types:
        print(f"- {rt}")