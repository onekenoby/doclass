from neo4j import GraphDatabase, exceptions
import os
from dotenv import load_dotenv
from gemini.gemini_client import generate_narrative_from_cypher

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
    Print a human-friendly narrative of the graph defined by the given Cypher.
    """
    narrative = generate_narrative_from_cypher(cypher_script)
    print("\n=== Semantic Interpretation of Graph ===\n")
    print(narrative)